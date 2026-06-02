import os
import sys
import io

# PDF 내의 유니코드 문자를 정상적으로 출력하기 위해 stdout/stderr 인코딩을 UTF-8로 설정
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# paser 패키지를 정상적으로 임포트할 수 있도록 프로젝트 루트 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scr.paser.pdf_parser import parse_pdf_files
from scr.LLM_model.briefing_generator import generate_briefing

def main():
    # 현재 스크립트 위치 기준으로 input 및 output 디렉토리 경로 지정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.abspath(os.path.join(current_dir, "input"))
    user_data_dir = os.path.abspath(os.path.join(current_dir, "data_base", "user_data"))
    guide_dir = os.path.abspath(os.path.join(current_dir, "data_base", "guide_data"))
    briefing_output_dir = os.path.abspath(os.path.join(current_dir, "output"))
    
    # 필요한 폴더가 존재하지 않는 경우 자동으로 생성
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(user_data_dir, exist_ok=True)
    os.makedirs(guide_dir, exist_ok=True)
    os.makedirs(briefing_output_dir, exist_ok=True)
    
    # 1단계: PDF에서 데이터 파싱하여 JSON 형태로 저장
    print(f"1단계: PDF 파일 읽는 중: {input_dir}")
    print(f"JSON 결과 저장 경로: {user_data_dir}")
    parse_pdf_files(input_dir, user_data_dir)
    print("-" * 80)
    
    # 2단계: 저장된 JSON 파일을 바탕으로 AI 스마트 브리핑 생성
    print("2단계: AI 스마트 브리핑 생성 중...")
    import glob
    json_files = glob.glob(os.path.join(user_data_dir, "*.json"))
    
    if not json_files:
        print("경고: 생성된 JSON 파일이 존재하지 않아 브리핑을 진행할 수 없습니다.")
        return
        
    for json_path in json_files:
        generate_briefing(json_path, guide_dir, briefing_output_dir)

if __name__ == "__main__":
    main()
