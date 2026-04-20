import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(
    page_title="정보공개 체크봇",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

.main-header {
    background: #1a4a8a;
    color: white;
    padding: 20px 24px;
    border-radius: 12px;
    margin-bottom: 20px;
}
.main-header h1 {
    font-size: 1.7rem;
    font-weight: 500;
    margin: 0 0 6px 0;
    color: white;
    letter-spacing: -0.01em;
}
.main-header p {
    font-size: 0.9rem;
    opacity: 0.85;
    margin: 0;
    color: white;
}

.rcard {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    overflow: hidden;
    margin-top: 10px;
}
.rcard-top-closed  { background: #fff1f1; border-bottom: 2px solid #E24B4A; padding: 14px 18px 12px; }
.rcard-top-partial { background: #fffbf0; border-bottom: 2px solid #EF9F27; padding: 14px 18px 12px; }
.rcard-top-open    { background: #f3faf0; border-bottom: 2px solid #639922; padding: 14px 18px 12px; }
.rcard-top-check   { background: #f0f4ff; border-bottom: 2px solid #378ADD; padding: 14px 18px 12px; }

.verdict-label-closed  { font-size: 1.25rem; font-weight: 500; color: #A32D2D; margin-bottom: 3px; }
.verdict-label-partial { font-size: 1.25rem; font-weight: 500; color: #854F0B; margin-bottom: 3px; }
.verdict-label-open    { font-size: 1.25rem; font-weight: 500; color: #3B6D11; margin-bottom: 3px; }
.verdict-label-check   { font-size: 1.25rem; font-weight: 500; color: #185FA5; margin-bottom: 3px; }
.verdict-sub { font-size: 0.78rem; color: #666; }

.rcard-body { padding: 14px 18px; font-size: 0.83rem; line-height: 1.8; color: #333; }

.chat-msg-user {
    background: #dbeafe;
    border-radius: 12px 12px 3px 12px;
    padding: 9px 13px;
    font-size: 0.85rem;
    color: #1e3a5f;
    margin-left: auto;
    max-width: 88%;
    margin-bottom: 6px;
}
.chat-msg-ai {
    background: #f5f5f5;
    border-radius: 12px 12px 12px 3px;
    padding: 9px 13px;
    font-size: 0.85rem;
    color: #333;
    line-height: 1.7;
    max-width: 88%;
    margin-bottom: 6px;
}

.stButton > button { border-radius: 8px; font-weight: 500; }
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 8px;
    border: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ── 시스템 프롬프트 ──────────────────────────────────────
SYSTEM_PROMPT = """당신은 서울특별시동부교육지원청 정보공개 업무 전문 AI 도우미입니다.
공개/부분공개/비공개 여부를 판단할 때 아래 자료를 모두 근거로 활용합니다.

## 참고 자료
① 공공기관의 정보공개에 관한 법률 [법률 제19408호, 2023.11.17]
② 정보공개법 시행령 [대통령령 제35948호, 2026.1.2]
③ 정보공개법 시행규칙 [행정안전부령 제576호, 2025.9.19]
④ 서울특별시교육청 행정정보 공개 조례 [제9796호, 2025.10.2]
⑤ 서울특별시교육청 비공개대상정보 세부기준 (E1~E8 코드 체계)
⑥ 2024년 정보공개 운영안내서 (행정안전부)
⑦ 2026 정보공개 업무 매뉴얼 (서울특별시, 289페이지)
⑧ 2023 서울특별시 비공개 세부기준

## 핵심 원칙
- 원칙: 모든 정보는 공개 대상 (정보공개법 제3조)
- 비공개 가능: 제9조 제1항 각 호 해당 시
- 부분공개: 비공개 해당 부분만 제외, 나머지 공개 (제14조)
- 6호: 개인식별정보만 삭제하면 공개 가능한 경우 많음

## 비공개 대상 정보 세부기준 (서울특별시교육청 비공개대상정보 세부기준, E코드)

### 1호 [E1] 법령상 비밀·비공개
- E1-02 (p.5): 공판 개시 전 소송 관련 기록 (형사소송법 제47조)
- E1-04 (p.4): 공직자 재산등록사항·금융거래자료 (공직자윤리법 제10조)
- E1-05 (p.4): 민원인 신상정보·민원내용 (민원처리법 제26조)
- E1-11 (p.5): 학교폭력대책자치위원회 회의록·피해·가해학생 관련 자료 (학폭법 제21조), 성폭력 범죄·피해자 신상정보, 가정폭력 피해자 신상정보
- E1-16 (p.6): 징계위원회 회의내용 (교육공무원 징계령 제18조·19조)
- E1-19 (p.6): 보존기간 기산일부터 10년 이내 속기록·녹음기록
- E1-21 (p.6): 행정심판위원회 위원 발언내용·회의록 (행정심판법 제41조)

### 2호 [E2] 안보·국방·통일·외교
- E2-03 (p.8~9): 정보통신망구성도, IP정보, 시스템 로그, 사용자계정·비밀번호, 보안성 검토 취약점 보고
- E2-06 (p.8): 청사 입체도면, 보안시설 도면, 경비초소 위치, 순찰경로·시간표, CCTV 위치·장비명

### 3호 [E3] 국민 생명·신체·재산보호
- E3-01 (p.10): 범죄 피의자·참고인·통보자 명단
- E3-06 (p.11): 인감·주민등록 관리 사항
- E3-08 (p.11): 위험시설·장비 위치·설계도·구조

### 4호 [E4] 진행 중인 재판·수사
- E4-01 (p.13): 진행 중 재판 관련 소장·답변서·소송진행상황·법률자문결과
- E4-04 (p.13): 수사 중 사건 증거자료·수사조서·진행상황보고서·참고인 명단
- E4-07 (p.14): 수형자 신분기록·교화작업 관련자료

### 5호 [E5] 감사·감독·계약·의사결정
- E5-02 (p.16~17): 불시감사·조사·단속 계획, 문답서·확인서, 사안기강 감사계획
- E5-03 (p.17): 채점답안지, 출제·채점위원, 면접채점표, 학력평가 출제위원, 개별학교 교과별 성적결과 비교자료
- E5-04 (p.17): 예정가격, 입찰참가신청서, 낙찰업체 외 업체 평가점수, 교섭완료 전 계약교섭방침
- E5-10 (p.18): 소청심사위원회 회의록, 예산안(확정 전), 사업검토서, 연구용역 중간보고, 심사위원 후보자 명단, 위원회 회의록 중 발언자 성명
- E5-11 (p.18~19): 근무성적평정결과, 승진심사위원회 심사내용, 인사위원회 회의록, 교직원 징계위원회 회의록

### 6호 [E6] 개인정보
- E6-01 (p.23): 이름·주민등록번호·연락처·주소·증명사진 등 개인식별정보 (단, 공무원 성명·직위는 공개)
- E6-04 (p.24): 개인 의료·질병정보, 학생정신건강관련정보
- E6-07 (p.24): 징계의결 요구서, 소청심사청구서·결정서
- E6-09 (p.25): 채용후보자명부, 근무성적평정서, 초과근무내역
- E6-10 (p.25): 시험답안지, 성적·석차, 임용후보자 시험 성적대장

### 7호 [E7] 경영·영업상 비밀
- E7-02 (p.28): 용역수행 민간업체의 기존기술·신공법·시공실적·내부관리 정보
- E7-03 (p.28): 용역 제안업체 기술평가 결과·점수집계표

### 8호 [E8] 부동산 투기·매점매석
- E8-04 (p.30): 학교 부지 선정 관련 정보, 학교 부지 매수계약서

## 서울시 정보공개 업무매뉴얼(2026) 주요 사례
- 청사 배치도·평면도·단면도: 비공개, 입면도(외관)는 공개 (p.91)
- 학폭위 회의록(개인별 발언): 비공개 (p.88)
- 면접시험 채점표: 비공개 (p.95)
- 불시감사계획: 비공개, 감사결과는 종료 후 공개 원칙 (p.94)
- 의사결정 과정 중 사업검토서: 비공개, 확정 후 공개 (p.96)
- 소청심사위원회·인사위원회 회의록: 비공개 (p.96)
- 공무원 휴대전화·자택주소: 비공개, 성명·직위는 공개 (p.97~98)
- 행정심판위원회 위원 발언·회의록: 비공개 (p.87)
- 시청 본관·별관·신관 설계도면: 비공개 (p.120)

## 행정안전부 운영안내서(2024) 주요 Q&A
- Q.041 (p.77): 개괄적 사유만으로 비공개 불가, 구체적 근거 제시 필요
- Q.044 (p.78): 청구 목적(졸업논문 등)은 공개 여부 판단에 영향 없음
- Q.062 (p.126): 감사결과: 감사완료 후 원칙적 공개
- Q.065 (p.128): 면접점수(본인 청구): 채점위원 도장 부분 제외 후 부분공개 검토
- Q.069 (p.132): 근무성적평정표(본인 청구): 비공개 가능
- Q.070 (p.132): 위원회 회의록: 발언자 성명 삭제 후 부분공개 검토
- Q.077 (p.143): CCTV 영상: 타인 모자이크 후 부분공개 검토
- Q.082 (p.145): 인사발령: 공무원 성명·직위 공개, 개인연락처·주소 비공개
- Q.083 (p.145): 공무원 개인정보: 성명·직위 공개, 자택주소·연락처·주민번호 비공개

## 처리 절차
- 결정기간: 청구일로부터 10일 이내 (10일 연장 가능)
- 비공개 전 협의: 정보공개책임관 사전 협의 (서울교육청 조례 제14조)
- 심의회: 비공개·부분공개 결정 시 정보공개심의회 심의 원칙
- 이의신청: 30일 이내, 처리 7일 이내

## 답변 형식 (반드시 준수)

[판정: 공개 | 부분공개 | 비공개 | 추가확인필요]
[판정 요약: 한 줄로 핵심 근거 명시]

1. 관련 조항
- 정보공개법 제9조 제1항 제X호: 조항 내용
- 관련 개별 법령: 해당 조항 및 내용

2. 서울특별시교육청 비공개대상정보 세부기준
- 코드: EX-XX (p.XX)
- 유형: 세부기준 유형명

3. 판단 근거 및 유사 사례
- 행정안전부 운영안내서(2024): Q.XXX (p.XXX) — 내용
- 서울특별시 정보공개 업무매뉴얼(2026): p.XXX — 내용

4. 실무 처리 방법
① 처리 단계 순서대로 안내

5. 유의사항
- 이 판단은 참고용 안내입니다. 법적 효력이 없으며 최종 결정은 담당자가 해야 합니다.
- 분쟁 가능성이 있는 경우 상급자 및 정보공개 전담부서와 협의하시기 바랍니다.

한국어로, 실무 담당자가 즉시 활용할 수 있도록 명확하게 작성하세요."""

# ── Gemini 클라이언트 ─────────────────────────────────────
@st.cache_resource
def get_gemini_model():
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )
    return model

# ── 세션 초기화 ──────────────────────────────────────────
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "keyword_result" not in st.session_state:
    st.session_state.keyword_result = None
if "last_keyword" not in st.session_state:
    st.session_state.last_keyword = ""

def get_chat_session():
    if st.session_state.chat_session is None:
        model = get_gemini_model()
        if model:
            st.session_state.chat_session = model.start_chat(history=[])
    return st.session_state.chat_session

def call_ai_keyword(keyword):
    model = get_gemini_model()
    if not model:
        return "⚠️ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에서 GOOGLE_API_KEY를 설정해 주세요."
    try:
        prompt = (
            f'"{keyword}"에 대해 정보공개 판단을 해주세요. '
            f'반드시 아래 5단계 형식으로 작성해 주세요:\n'
            f'1. 관련 조항 (정보공개법 제9조 제1항 각 호 + 관련 개별 법령)\n'
            f'2. 서울특별시교육청 비공개대상정보 세부기준 (E코드, 유형, 페이지)\n'
            f'3. 판단 근거 및 유사 사례 (행안부 운영안내서 Q번호·페이지, 서울시 매뉴얼 페이지 구분하여 작성)\n'
            f'4. 실무 처리 방법 (단계별)\n'
            f'5. 유의사항 (참고용임을 명시, 분쟁 가능성 시 상급자 협의 권장)'
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"오류: {str(e)}"

def call_ai_chat(user_input):
    chat = get_chat_session()
    if not chat:
        return "⚠️ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에서 GOOGLE_API_KEY를 설정해 주세요."
    try:
        response = chat.send_message(user_input)
        return response.text
    except Exception as e:
        return f"오류: {str(e)}"

def parse_verdict(text):
    t = text[:100]
    if "비공개" in t and "부분공개" not in t: return "closed"
    if "부분공개" in t: return "partial"
    if "추가확인" in t or "추가 확인" in t: return "check"
    if "공개" in t: return "open"
    return "check"

def render_result_card(result_text, verdict_type):
    top_class = {
        "closed": "rcard-top-closed",
        "partial": "rcard-top-partial",
        "open":    "rcard-top-open",
        "check":   "rcard-top-check"
    }.get(verdict_type, "rcard-top-check")

    label_map = {
        "closed":  ("비공개",          "verdict-label-closed"),
        "partial": ("부분공개",         "verdict-label-partial"),
        "open":    ("공개",             "verdict-label-open"),
        "check":   ("추가 확인 필요",   "verdict-label-check")
    }
    label, label_class = label_map.get(verdict_type, ("추가 확인 필요", "verdict-label-check"))

    summary = ""
    for line in result_text.split('\n')[:6]:
        if "판정 요약" in line:
            summary = line.replace("[판정 요약:", "").replace("]", "").strip()
            break

    body_html = result_text \
        .replace('[판정: 비공개]', '') \
        .replace('[판정: 부분공개]', '') \
        .replace('[판정: 공개]', '') \
        .replace('[판정: 추가확인필요]', '') \
        .replace('[판정: 추가 확인 필요]', '') \
        .replace('\n', '<br>')

    st.markdown(f"""
    <div class="rcard">
        <div class="{top_class}">
            <div class="{label_class}">{label}</div>
            <div class="verdict-sub">{summary}</div>
        </div>
        <div class="rcard-body">{body_html}</div>
    </div>
    """, unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>정보공개 체크봇</h1>
  <p>서울특별시동부교육지원청 정보공개 판단 지원 서비스 입니다</p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

# ━━━━ 왼쪽: 키워드 확인 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with col_left:
    st.markdown("### 키워드 확인")
    st.caption("핵심 단어 입력 → 공개 여부 및 근거 확인")

    keyword = st.text_input(
        "키워드 입력",
        placeholder="예: 학폭위 회의록, 면접채점표, 청사 평면도...",
        label_visibility="collapsed"
    )

    st.caption("자주 묻는 사례")
    examples = [
        "학폭위 회의록", "면접채점표", "감사계획서",
        "청사 평면도", "교사 징계서류", "예산안(미확정)",
        "CCTV 영상", "근무성적평정", "입찰 예정가격"
    ]
    cols = st.columns(3)
    for i, ex in enumerate(examples):
        if cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
            keyword = ex
            st.session_state.last_keyword = ex

    st.markdown("")
    search_btn = st.button("확인하기", type="primary", use_container_width=True)

    if search_btn and keyword:
        st.session_state.last_keyword = keyword
        with st.spinner("법령·세부기준·매뉴얼 검토 중..."):
            result = call_ai_keyword(keyword)
            st.session_state.keyword_result = result

    if st.session_state.keyword_result:
        result_text = st.session_state.keyword_result
        verdict_type = parse_verdict(result_text)
        render_result_card(result_text, verdict_type)

        st.markdown("")
        if st.button("💬 이 사례로 추가 질문하기 →", use_container_width=True):
            kw = st.session_state.last_keyword
            init_msg = f'"{kw}" 관련 추가 질문입니다. 부분공개가 가능한 경우 구체적인 처리 방법을 알려주세요.'
            st.session_state.messages.append({"role": "user", "content": init_msg})
            with st.spinner("답변 생성 중..."):
                reply = call_ai_chat(init_msg)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

# ━━━━ 오른쪽: 상세 질문 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with col_right:
    st.markdown("### 상세 질문")
    st.caption("구체적인 상황을 설명하면 세부기준 코드·페이지·유사 사례 출처를 포함한 5단계 판단을 받을 수 있습니다.")

    chat_container = st.container(height=480)
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="color:#bbb;font-size:0.84rem;text-align:center;padding-top:80px;line-height:1.9;">
                아래 입력창에 상황을 자세히 설명해 주세요.<br><br>
                예: "학부모가 학폭위 가해학생 징계 결과를 청구했습니다."<br>
                예: "감사 진행 중인 학교 감사계획서를 언론사에서 청구했습니다."<br>
                예: "청사 평면도를 연구 목적으로 청구했습니다."
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="chat-msg-user">{msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="chat-msg-ai">{msg["content"].replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True
                    )

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "질문 입력",
            placeholder="구체적인 상황을 입력하세요...",
            height=80,
            label_visibility="collapsed"
        )
        col_s, col_c = st.columns([3, 1])
        send  = col_s.form_submit_button("전송 →", type="primary", use_container_width=True)
        clear = col_c.form_submit_button("초기화", use_container_width=True)

    if send and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("법령·매뉴얼 검토 중..."):
            reply = call_ai_chat(user_input.strip())
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if clear:
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# ── 하단 ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="font-size:0.72rem;color:#aaa;text-align:center;line-height:1.9;">
    정보공개법(법률 제19408호, 2023.11.17) · 시행령(대통령령 제35948호, 2026.1.2) · 시행규칙(행정안전부령 제576호, 2025.9.19)<br>
    서울특별시교육청 행정정보 공개 조례(제9796호, 2025.10.2) · 서울교육청 비공개대상정보 세부기준(E1~E8)<br>
    2024 정보공개 운영안내서(행정안전부) · 2026 정보공개 업무 매뉴얼(서울특별시) · 2023 서울특별시 비공개 세부기준
</div>
""", unsafe_allow_html=True)
