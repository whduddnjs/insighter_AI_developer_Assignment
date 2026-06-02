import os
import glob
import logging
import json
import re
import pdfplumber

# pdfminer 라이브러리의 폰트 경고 로그 출력 억제
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def mask_name(name: str) -> str:
    """
    NOTE: 이름의 개인정보 보호를 위해 마스킹 처리를 수행합니다. 예: "홍길동" -> "홍*동", "이산" -> "이*", "독고인사" -> "독**사"
    """
    if not name:
        return name
    name_len = len(name)
    if name_len <= 1:
        return "*"
    elif name_len == 2:
        return name[0] + "*"
    else:
        # 3글자 이상인 경우 첫 글자와 마지막 글자만 유지하고 중간 글자들을 마스킹
        return name[0] + "*" * (name_len - 2) + name[-1]

def parse_pdf_files(input_dir: str, output_dir: str):
    """
    TODO: 비정형 PDF가 입력될 경우 AI Vison / OCR 기반의 FALLBACK 코드가 추가되어야 합니다. (AI Vison API 사용을 위해서는 API KEY 발급이 필요합니다.)
    NOTE: 지정된 디렉토리 내의 모든 .pdf 파일을 읽고, 1, 2, 3페이지에서 대상 항목들을 추출하여 출력 디렉토리에 JSON 파일로 저장합니다.
    """
    search_path = os.path.join(input_dir, "*.pdf")
    pdf_files = glob.glob(search_path)
    
    if not pdf_files:
        print(f"디렉토리 내에 PDF 파일이 존재하지 않습니다: {input_dir}")
        return

    # 출력 디렉토리가 존재하지 않는 경우 생성
    os.makedirs(output_dir, exist_ok=True)

    for pdf_path in pdf_files:
        print("=" * 80)
        print(f"파싱 진행 중: {pdf_path}")
        print("=" * 80)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    print("[빈 PDF 파일]")
                    continue
                
                # 1페이지 텍스트 추출 진행
                first_page_text = pdf.pages[0].extract_text()
                if not first_page_text:
                    print("[1페이지 텍스트 추출 실패]")
                    continue
                
                lines = [line.strip() for line in first_page_text.split("\n")]
                
                # 이름, 성별, 연령 추출
                name, gender, age = None, None, None
                for idx, line in enumerate(lines):
                    if "이름" in line and "성별" in line and "연령" in line:
                        if idx + 1 < len(lines):
                            val_line = lines[idx + 1]
                            # 데이터 줄 형태 예시: "김인사 남아 / 만 7세 3개월 남자 4–11세 2026.03.12"
                            if "/" in val_line:
                                left_part, right_part = val_line.split("/", 1)
                                
                                # 슬래시 기준 왼쪽 파싱: "김인사 남아"
                                left_tokens = left_part.strip().split()
                                if len(left_tokens) >= 2:
                                    name = left_tokens[0]
                                    gender = left_tokens[1]
                                elif len(left_tokens) == 1:
                                    name = left_tokens[0]
                                
                                # 슬래시 기준 오른쪽 파싱: "만 7세 3개월 남자 4–11세 2026.03.12"
                                # 적용 기준("남자", "여자" 등) 직전까지의 문자열을 연령으로 취급
                                right_tokens = right_part.strip().split()
                                age_tokens = []
                                for tok in right_tokens:
                                    if tok in ["남자", "여자", "남아", "여아"]:
                                        break
                                    age_tokens.append(tok)
                                age = " ".join(age_tokens)
                        break
                
                # T점수 추출 (내재화 문제, 외현화 문제, 총 문제행동 점수)
                internalizing, externalizing, total_problems = None, None, None
                for idx, line in enumerate(lines):
                    # T T T 헤더 검출
                    if re.match(r"^T\s+T\s+T$", line):
                        if idx - 1 >= 0:
                            score_line = lines[idx - 1]
                            score_tokens = score_line.split()
                            if len(score_tokens) >= 3:
                                # 보통 내재화, 외현화, 총 문제행동 순서로 구성됨
                                try:
                                    internalizing = int(score_tokens[0])
                                    externalizing = int(score_tokens[1])
                                    total_problems = int(score_tokens[2])
                                except ValueError:
                                    pass
                        break

                # 2페이지 추출: 증후군 영역별 점수
                syndrome_results = {
                    "내재화 증후군": {},
                    "혼합 증후군": {},
                    "외현화 증후군": {}
                }
                
                if len(pdf.pages) >= 2:
                    page2_text = pdf.pages[1].extract_text()
                    if page2_text:
                        p2_lines = [line.strip() for line in page2_text.split("\n") if line.strip()]
                        
                        category_map = {
                            "내재화 증후군": ["위축", "신체증상", "우울/불안"],
                            "혼합 증후군": ["사회적 미성숙", "사고의 문제", "주의집중 문제"],
                            "외현화 증후군": ["비행", "공격성"]
                        }
                        
                        current_category = None
                        for idx, line in enumerate(p2_lines):
                            if "내재화 증후군" in line:
                                current_category = "내재화 증후군"
                            elif "혼합 증후군" in line:
                                current_category = "혼합 증후군"
                            elif "외현화 증후군" in line:
                                current_category = "외현화 증후군"
                            
                            if current_category:
                                for subscale in category_map[current_category]:
                                    if line == subscale:
                                        if idx + 1 < len(p2_lines):
                                            score_line = p2_lines[idx + 1]
                                            match = re.match(r"^(\d+)", score_line)
                                            if match:
                                                score = int(match.group(1))
                                                syndrome_results[current_category][subscale] = score
                                        break
                
                # 3페이지 추출: 주요 관찰 소견 및 종합 해석
                observations = {}
                interpretation = ""
                
                if len(pdf.pages) >= 3:
                    page3_text = pdf.pages[2].extract_text()
                    if page3_text:
                        p3_lines = [line.strip() for line in page3_text.split("\n") if line.strip()]
                        
                        start_obs_idx = -1
                        start_interp_idx = -1
                        end_interp_idx = -1
                        
                        for idx, line in enumerate(p3_lines):
                            if "주요 관찰 소견" in line:
                                start_obs_idx = idx
                            elif "종합 해석" in line:
                                start_interp_idx = idx
                            elif ("보호자 참고 의견" in line or "해석 시 유의사항" in line) and end_interp_idx == -1:
                                end_interp_idx = idx
                                
                        # 주요 관찰 소견 파싱
                        if start_obs_idx != -1 and start_interp_idx != -1:
                            current_key = None
                            current_content = []
                            for idx in range(start_obs_idx + 1, start_interp_idx):
                                line = p3_lines[idx]
                                if "· T =" in line or "· T=" in line:
                                    if current_key:
                                        observations[current_key] = " ".join(current_content)
                                    current_key = line
                                    current_content = []
                                else:
                                    current_content.append(line)
                            if current_key:
                                observations[current_key] = " ".join(current_content)
                                
                        # 종합 해석 파싱
                        if start_interp_idx != -1:
                            end_idx = end_interp_idx if end_interp_idx != -1 else len(p3_lines)
                            interp_lines = []
                            for idx in range(start_interp_idx + 1, end_idx):
                                interp_lines.append(p3_lines[idx])
                            interpretation = "\n".join(interp_lines).strip()
                
                result = {
                    "이름": mask_name(name) if name else None,
                    "성별": gender,
                    "연령": age,
                    "내재화 문제 점수": internalizing,
                    "외현화 문제 점수": externalizing,
                    "총 문제행동 점수": total_problems,
                    "내재화 증후군": syndrome_results["내재화 증후군"],
                    "혼합 증후군": syndrome_results["혼합 증후군"],
                    "외현화 증후군": syndrome_results["외현화 증후군"],
                    "주요 관찰 소견": observations,
                    "종합 해석": interpretation
                }
                
                # 추출된 데이터를 지정된 출력 폴더에 JSON 파일로 저장
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                output_file_path = os.path.join(output_dir, f"{base_name}.json")
                with open(output_file_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
                print(f"성공적으로 데이터를 JSON 파일로 저장했습니다: {output_file_path}")
                
        except Exception as e:
            print(f"파싱 중 에러 발생 {pdf_path}: {e}")
        print("=" * 80 + "\n")
