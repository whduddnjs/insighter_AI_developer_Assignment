import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from scr.LLM_model.pdf_generator import generate_pdf


# .env 파일로부터 환경 변수 로드
load_dotenv()

def generate_briefing(user_json_path: str, guide_dir: str, output_dir: str):
    """
    TODO: 현재 Gemini Free Tear를 사용하여 보낸 데이터가 LLM학습에 사용되는 중, 차후 데이터 보안 대책이 필요합니다.(현재 이름 마스킹 적용 중)
    NOTE: 파싱된 JSON 아동 데이터를 바탕으로 Gemini API를 호출하여 맞춤형 브리핑 요약을 얻고, 추천된 가이드 파일과 결합하여 최종 브리핑 결과 파일(.md)을 생성합니다.
    """
    # 1. API 키 검사 및 설정
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        print("에러: .env 파일에서 AI_API_KEY를 찾을 수 없습니다.")
        return

    genai.configure(api_key=api_key)

    # 2. 파싱된 아동 결과 JSON 파일 로드
    if not os.path.exists(user_json_path):
        print(f"에러: 아동 결과 파일이 존재하지 않습니다: {user_json_path}")
        return

    with open(user_json_path, "r", encoding="utf-8") as f:
        child_data = json.load(f)

    # 3. 프롬프트 구성 및 Gemini API 호출
    prompt = f"""
역할: 너는 임상 심리 전문가가 아니며, 어떠 상황에서도  병명이나 장애를 진단해서는 안돼. 오직 수치의 의미와 종합 해석을 보호자가 이해하기 쉽게 풀어서 설명해 줘
데이터: 아래 제공된 아동의 K-CBCL 검사 결과 데이터를 분석해줘.

아동 데이터:
{json.dumps(child_data, ensure_ascii=False, indent=2)}

제약 조건:
1. 제공된 검사 수치(T점수)를 바탕으로 절대로 의학적/정신의학적 병명을 진단(예: ADHD, 불안장애, 우울증 등)하지 마.
2. 부모가 상처받지 않고 아이의 상태를 이해할 수 있도록 부드럽고 따뜻한 어조(해요체)로 2~3문장의 요약 해석을 작성해줘.
3. 아래 네 가지 가이드 아이디(ID) 중에서 아동의 점수가 가장 높거나 두드러진 취약점(T점수 60 이상인 준임상/임상 수준 항목)에 가장 잘 매칭되는 1개의 가이드 ID를 추천해줘.
   - 'anxiety': 우울/불안, 걱정, 긴장 등 정서적 정서불안이 두드러지는 경우
   - 'attention': 주의집중 문제, 산만함, 집중 유지의 어려움이 두드러지는 경우
   - 'social': 사회적 미성숙, 의존적 행동, 또래 관계 서툼 등이 두드러지는 경우
   - 'withdrawal': 위축, 소극적 태도, 혼자 있기를 선호하는 경향이 두드러지는 경우

반드시 아래 스키마의 JSON 포맷으로만 응답해줘:
{{
  "summary": "여기에 부모를 향한 따뜻한 2~3문장의 요약 해석 내용을 작성",
  "recommended_guide_id": "anxiety, attention, social, withdrawal 중 가장 적절한 ID 1개 선택"
}}
"""

    try:
        # gemini-2.5-flash 모델을 사용하여 JSON 형식 응답 요청
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # API 응답 파싱
        ai_response = json.loads(response.text.strip())
        summary = ai_response.get("summary", "")
        recommended_guide_id = ai_response.get("recommended_guide_id", "")
        
    except Exception as e:
        print(f"Gemini API 호출 및 파싱 중 에러 발생: {e}")
        return

    # 4. 추천된 가이드 데이터 로드
    guide_file_path = os.path.join(guide_dir, f"guide_{recommended_guide_id}.txt")
    guide_content = ""
    if os.path.exists(guide_file_path):
        with open(guide_file_path, "r", encoding="utf-8") as f:
            guide_content = f.read().strip()
    else:
        print(f"경고: 추천된 가이드 파일을 찾을 수 없습니다: {guide_file_path}")
        # 기본값 폴백
        guide_content = "추천 가이드 내용을 불러올 수 없습니다."

    # 5. 최종 리포트 마크다운 콘텐츠 결합
    child_name = child_data.get("이름", "우리 아이")
    
    briefing_md = f"""# 📑 우리 아이 스마트 브리핑 (CBCL 결과 분석)

## 👤 대상 아동 정보
- **이름**: {child_name}
- **성별**: {child_data.get("성별", "미지정")}
- **연령**: {child_data.get("연령", "미지정")}

---

## ✉️ 1. 요약 브리핑
{summary}

---

## 🏠 2. 맞춤형 양육/심리 가이드
{guide_content}

---

*본 브리핑은 CBCL 표준 검사 데이터를 기반으로 AI와 전문 가이드가 함께 매칭하여 제공하는 참고용 정보입니다. 상세 진단은 전문가 상담을 권장합니다.*
"""

    # 6. 마크다운 및 PDF 파일로 저장
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(user_json_path))[0]
    
    # 6-1. 마크다운 저장
    output_file_path = os.path.join(output_dir, f"{base_name}_스마트_브리핑.md")
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(briefing_md)
        
    # 6-2. PDF 저장
    pdf_file_path = os.path.join(output_dir, f"{base_name}_스마트_브리핑.pdf")
    try:
        generate_pdf(child_data, summary, guide_content, pdf_file_path)
    except Exception as e:
        print(f"PDF 리포트 생성 중 에러 발생: {e}")
        
    print("=" * 80)
    print(f"스마트 브리핑 파일이 성공적으로 생성되었습니다:")
    print(f"  - 마크다운: {output_file_path}")
    print(f"  - PDF: {pdf_file_path}")
    print("=" * 80)
    print(briefing_md)
    print("=" * 80)
