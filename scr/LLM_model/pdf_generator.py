import os
import urllib.request
from fpdf import FPDF

def download_fonts():
    """
    NOTE: K-CBCL 스마트 브리핑 PDF에 한글을 지원하기 위해 나눔고딕(NanumGothic) 폰트를 다운로드합니다.
    """
    font_dir = os.path.join("data_base", "fonts")
    os.makedirs(font_dir, exist_ok=True)
    
    fonts = {
        "NanumGothic-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
        "NanumGothic-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf"
    }
    
    for font_name, url in fonts.items():
        font_path = os.path.join(font_dir, font_name)
        if not os.path.exists(font_path):
            print(f"다운로드 중: {font_name}...")
            try:
                urllib.request.urlretrieve(url, font_path)
                print(f"다운로드 완료: {font_name}")
            except Exception as e:
                print(f"폰트 다운로드 실패 ({font_name}): {e}")

class BriefingPDF(FPDF):
    """
    스마트 브리핑 PDF 템플릿 생성을 위한 FPDF 커스텀 클래스
    """
    def __init__(self):
        super().__init__()
        # 폰트 다운로드 확인 및 등록
        download_fonts()
        font_dir = os.path.join("data_base", "fonts")
        
        reg_path = os.path.join(font_dir, "NanumGothic-Regular.ttf")
        bold_path = os.path.join(font_dir, "NanumGothic-Bold.ttf")
        
        if os.path.exists(reg_path):
            self.add_font("NanumGothic", "", reg_path)
        if os.path.exists(bold_path):
            self.add_font("NanumGothic", "B", bold_path)

    def header(self):
        # 상단 네이비 바 장식
        self.set_fill_color(30, 58, 138)  # Deep Navy
        self.rect(0, 0, 210, 4, "F")

    def footer(self):
        # 하단 페이지 번호
        self.set_y(-15)
        self.set_font("NanumGothic", "", 8)
        self.set_text_color(156, 163, 175)  # Gray 400
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def generate_pdf(child_data: dict, summary: str, guide_content: str, output_path: str):
    """
    정형 데이터 및 AI 요약본, 가이드를 받아 고품질의 PDF 브리핑 리포트를 생성합니다.
    """
    pdf = BriefingPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. 문서 헤더 타이틀
    pdf.ln(5)
    pdf.set_font("NanumGothic", "B", 18)
    pdf.set_text_color(30, 58, 138)  # Deep Navy
    pdf.cell(0, 12, "우리 아이 스마트 브리핑 (CBCL 결과 분석)", ln=True, align="L")
    
    # 구분선
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    # 2. 대상 아동 정보 영역
    pdf.set_font("NanumGothic", "B", 11)
    pdf.set_text_color(55, 65, 81)  # Gray 700
    pdf.cell(0, 8, "대상 아동 정보", ln=True)
    pdf.ln(1)
    
    # 아동 정보 카드형 배경 박스
    pdf.set_fill_color(243, 244, 246)  # Gray 100
    pdf.set_draw_color(209, 213, 219)  # Gray 300
    pdf.set_line_width(0.2)
    
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.rect(x, y, 190, 15, "FD")
    
    # 텍스트 출력
    pdf.set_y(y + 4.5)
    pdf.set_x(x + 10)
    
    pdf.set_font("NanumGothic", "B", 10)
    pdf.write(6, "이름: ")
    pdf.set_font("NanumGothic", "", 10)
    pdf.write(6, f"{child_data.get('이름', '미지정')}         |         ")
    
    pdf.set_font("NanumGothic", "B", 10)
    pdf.write(6, "성별: ")
    pdf.set_font("NanumGothic", "", 10)
    pdf.write(6, f"{child_data.get('성별', '미지정')}         |         ")
    
    pdf.set_font("NanumGothic", "B", 10)
    pdf.write(6, "연령: ")
    pdf.set_font("NanumGothic", "", 10)
    pdf.write(6, f"{child_data.get('연령', '미지정')}")
    
    pdf.set_y(y + 20)
    pdf.ln(4)
    
    # 3. 1. 요약 브리핑 섹션
    pdf.set_font("NanumGothic", "B", 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 8, "1. 요약 브리핑", ln=True)
    
    pdf.set_draw_color(147, 197, 253)  # Blue 300
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("NanumGothic", "", 10)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(0, 6.5, summary.strip(), border=0)
    pdf.ln(6)
    
    # 4. 2. 맞춤형 양육/심리 가이드 섹션
    pdf.set_font("NanumGothic", "B", 13)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 8, "2. 맞춤형 양육/심리 가이드", ln=True)
    
    pdf.set_draw_color(147, 197, 253)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("NanumGothic", "", 10)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(0, 6.5, guide_content.strip(), border=0)
    pdf.ln(10)
    
    # 5. 면책 조항 / 안내 문구 (하단 고정 느낌)
    pdf.set_font("NanumGothic", "", 8)
    pdf.set_text_color(156, 163, 175)
    disclaimer = "* 본 스마트 브리핑은 CBCL 표준 검사 데이터를 기반으로 AI와 맞춤 가이드라인을 분석하여 제공하는 참고용 보고서입니다. 의학적 판단이나 구체적인 치료는 소아 청소년 정신과 등 전문 의료기관과 상담을 권장합니다."
    pdf.multi_cell(0, 5, disclaimer, border=0, align="C")
    
    # 파일 쓰기
    pdf.output(output_path)
    print(f"PDF 리포트 생성 완료: {output_path}")
