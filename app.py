import streamlit as st
from groq import Groq
import os
import json
from datetime import datetime
from collections import Counter

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
.rcard-top-closed  { background:#fff1f1; border-bottom:2px solid #E24B4A; padding:14px 18px 12px; }
.rcard-top-partial { background:#fffbf0; border-bottom:2px solid #EF9F27; padding:14px 18px 12px; }
.rcard-top-open    { background:#f3faf0; border-bottom:2px solid #639922; padding:14px 18px 12px; }
.rcard-top-check   { background:#f0f4ff; border-bottom:2px solid #378ADD; padding:14px 18px 12px; }

.verdict-label-closed  { font-size:1.25rem; font-weight:500; color:#A32D2D; margin-bottom:3px; }
.verdict-label-partial { font-size:1.25rem; font-weight:500; color:#854F0B; margin-bottom:3px; }
.verdict-label-open    { font-size:1.25rem; font-weight:500; color:#3B6D11; margin-bottom:3px; }
.verdict-label-check   { font-size:1.25rem; font-weight:500; color:#185FA5; margin-bottom:3px; }
.verdict-sub { font-size:0.78rem; color:#666; }

.rcard-body { padding:14px 18px; font-size:0.83rem; line-height:1.8; color:#333; }

.verification-steps {
    display: flex;
    justify-content: space-between;
    margin: 15px 0;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 8px;
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    padding: 8px;
}
.step-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 6px;
}
.step-pending { background: #e0e0e0; color: #666; }
.step-active { background: #378ADD; color: white; animation: pulse 1.5s infinite; }
.step-complete { background: #639922; color: white; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.review-box {
    background: #fffef5;
    border: 1px solid #f0e68c;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    font-size: 0.82rem;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
}

.confidence-bar {
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    overflow: hidden;
    margin-top: 8px;
}
.confidence-fill {
    height: 100%;
    border-radius: 3px;
}
.confidence-high { background: #639922; }
.confidence-medium { background: #EF9F27; }
.confidence-low { background: #E24B4A; }

.chat-msg-user {
    background:#dbeafe;
    border-radius:12px 12px 3px 12px;
    padding:9px 13px;
    font-size:0.85rem;
    color:#1e3a5f;
    margin-left:auto;
    max-width:88%;
    margin-bottom:6px;
}
.chat-msg-ai {
    background:#f5f5f5;
    border-radius:12px 12px 12px 3px;
    padding:9px 13px;
    font-size:0.85rem;
    color:#333;
    line-height:1.7;
    max-width:88%;
    margin-bottom:6px;
}

.stat-rank {
    display:flex;
    align-items:center;
    gap:10px;
    padding:7px 12px;
    border-radius:8px;
    background:#f8f9fa;
    margin-bottom:5px;
    font-size:0.85rem;
}
.rank-num {
    min-width:24px;
    height:24px;
    border-radius:50%;
    background:#1a4a8a;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:0.72rem;
    font-weight:500;
    flex-shrink:0;
}
.rank-num.top3 { background:#E24B4A; }

.stButton > button { border-radius:8px; font-weight:500; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 3단계 검증 시스템 프롬프트
# ══════════════════════════════════════════════════════════════════════════════

AGENT_1_SYSTEM_PROMPT = """당신은 정보공개 1차 판단 에이전트입니다.
사용자가 입력한 키워드/상황에 대해 초기 분석을 수행합니다.

## 참고 법령
- 정보공개법 제9조 제1항 각호 (비공개 사유)
- 서울특별시교육청 비공개대상정보 세부기준 (E1~E8)

## 비공개 대상 정보 (제9조 제1항)
1호: 법령상 비밀·비공개 정보
2호: 국가안전보장·국방·통일·외교
3호: 국민 생명·신체·재산 보호
4호: 진행 중인 재판·수사
5호: 감사·감독·시험·계약·의사결정 과정
6호: 개인정보 (사생활 비밀·자유 침해)
7호: 법인·단체 경영·영업상 비밀
8호: 부동산 투기·매점매석 유발

## 세부기준 예시
- E1-11: 학폭위 회의록·피해가해학생 자료 (학폭법 제21조)
- E1-16: 징계위원회 회의내용 (교육공무원 징계령)
- E5-03: 채점답안지, 면접채점표, 출제위원
- E5-10: 위원회 회의록 중 발언자 성명
- E5-11: 근무성적평정, 인사위원회 회의록
- E6-01: 개인식별정보 (성명·연락처·주소)

## 출력 형식 (반드시 아래 형식 준수)
[1차 판단 결과]
- 정보유형: (해당 정보 유형)
- 관련법조항: 제9조 제1항 제X호
- E코드: EX-XX
- 초기판단: 공개|비공개|부분공개|추가확인필요
- 판단근거: (구체적 이유)
- 공개가능부분: (부분공개시)
- 비공개대상부분: (비공개 해당 부분)
- 신뢰도: 상|중|하
- 불확실요소: (있다면 기재)
- 참고사례: (유사 사례)"""

AGENT_2_SYSTEM_PROMPT = """당신은 정보공개 법적 검토 에이전트입니다.
1차 판단 결과를 법적 관점에서 엄격하게 검증합니다.

## 검토 체크리스트

### 비공개 사유 적정성
- [ ] 비공개 사유가 제9조 제1항 각호에 명확히 해당하는가?
- [ ] 추상적 사유(업무 혼란, 관행)로만 판단하지 않았는가?
- [ ] 비공개 범위가 최소한으로 한정되었는가?

### 부분공개 검토 (필수)
- [ ] 전체 비공개 전 부분공개 가능성을 검토했는가?
- [ ] 개인식별정보만 삭제하면 공개 가능하지 않은가?
- [ ] 비공개 부분과 공개 부분이 분리 가능한가?

### 공익 vs 사익 비교형량
- [ ] 공개로 인한 공익이 비공개 이익보다 크지 않은가?
- [ ] 시간 경과로 비공개 사유가 소멸되지 않았는가?

### 판례 일치 여부
- 완료된 감사결과 → 공개 원칙 (대법원 2022두45586)
- 수사 종결 후 자료 → 제4호 해당 안 됨 (부산지법 2022구합23051)

## 출력 형식 (반드시 아래 형식 준수)
[법적 검토 결과]
- 검토결과: 적정|수정필요|재검토필요
- 적정성점수: 1-10점
- 발견된문제점: (있다면 기재)
- 수정권고사항: (수정 필요시)
- 누락된검토사항: (있다면)
- 부분공개가능성: 있음|없음|검토필요
- 부분공개방법: (구체적 방법)
- 공익비교형량: 공익우선|사익우선|균형
- 참고판례: (관련 판례)
- 최종권고: 원안유지|수정후승인|재검토요청"""

AGENT_3_SYSTEM_PROMPT = """당신은 정보공개 최종 판단 에이전트입니다.
1차 판단과 법적 검토 결과를 종합하여 최종 결론을 도출합니다.

## 최종 판단 원칙
1. 1차 판단과 검토 결과가 일치하면 해당 판단 확정
2. 의견 충돌 시 법적 근거가 명확한 쪽 우선
3. 불확실한 경우 공개 원칙 적용 (정보공개법 제3조)
4. 부분공개 가능성 최종 확인

## 자가 검증 (모두 "예"여야 함)
1. 이 판단이 행정심판에서 유지될 수 있는가?
2. 비공개 사유가 구체적이고 명확한가?
3. 부분공개로 목적 달성이 불가능한가?
4. 동일 유형 청구에 일관 적용 가능한가?
5. 국민의 알권리를 최대한 보장했는가?

## 출력 형식 (반드시 아래 형식 준수)

[판정: 공개|비공개|부분공개|추가확인필요]
[신뢰도: 상|중|하] [검토단계: 3단계 완료]
[판정 요약: 핵심 근거 한 줄]

---

## 📋 3단계 검증 결과

### 🔍 검토 과정 요약
| 단계 | 판단 | 주요 근거 |
|------|------|-----------|
| 1차 판단 | OOO | 근거 |
| 법적 검토 | OOO | 근거 |
| 최종 판단 | OOO | 확정 근거 |

### 1. 관련 조항
- 정보공개법 제9조 제1항 제X호: 조항 내용
- 관련 개별 법령: (해당시)

### 2. 비공개대상정보 세부기준
- 코드: EX-XX
- 유형: 세부기준 유형명

### 3. 판단 근거
- 1차 판단: ...
- 법적 검토 보완: ...
- 참고 판례/사례: ...

### 4. 부분공개 검토 결과
- 부분공개 가능 여부: 가능|불가능
- 공개 가능 부분: ...
- 비공개 부분: ...
- 처리 방법: ...

### 5. 실무 처리 방법
① 처리 절차 1
② 처리 절차 2
③ 처리 절차 3

### 6. 유의사항
⚠️ 이 판단은 3단계 AI 검증을 거친 참고용 안내입니다.
⚠️ 법적 효력이 없으며 최종 결정은 담당자가 해야 합니다.
⚠️ 판단이 어려운 경우 정보공개 전담부서와 협의하시기 바랍니다."""

CASE_SYSTEM_PROMPT = """당신은 서울특별시동부교육지원청 정보공개 업무 전문 AI 도우미입니다.
담당자가 입력한 구체적인 상황에 대해 유사 사례를 안내합니다.

## 참고 자료
- 2024년 정보공개 운영안내서 (행정안전부)
- 2026 정보공개 업무 매뉴얼 (서울특별시)
- 2023 정보공개 연차보고서 교육청 사례

## 답변 형식

### 상황 요약
한 줄 요약

### 유사 사례 1
- 출처: (구체적 출처)
- 내용: (사례 내용)
- 결정: 공개/비공개/부분공개
- 근거: 제9조 제1항 제X호

### 유사 사례 2
- 출처: (구체적 출처)
- 내용: (사례 내용)
- 결정: 공개/비공개/부분공개

### 적용 방향
현재 상황에 대한 판단 방향

### 처리 방법
① 단계별 처리

### 유의사항
참고용 안내입니다. 최종 결정은 담당자가 해야 합니다."""


# ══════════════════════════════════════════════════════════════════════════════
# 통계 관리
# ══════════════════════════════════════════════════════════════════════════════
STATS_FILE = "search_stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"keywords": [], "cases": []}

def save_stats(data):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def record_keyword(keyword, verdict, confidence="중"):
    stats = load_stats()
    stats["keywords"].append({
        "keyword": keyword,
        "verdict": verdict,
        "confidence": confidence,
        "verification_steps": 3,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_stats(stats)

def record_case(query):
    stats = load_stats()
    stats["cases"].append({
        "query": query[:80],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_stats(stats)


# ══════════════════════════════════════════════════════════════════════════════
# AI 호출
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_client():
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def call_ai(messages_list, system):
    client = get_client()
    if not client:
        return "⚠️ API 키가 설정되지 않았습니다."
    try:
        full_messages = [{"role": "system", "content": system}] + messages_list
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            max_tokens=2000,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# 3단계 검증 시스템
# ══════════════════════════════════════════════════════════════════════════════

def render_verification_steps(current_step):
    steps = [("1", "1차 판단"), ("2", "법적 검토"), ("3", "최종 판단")]
    html = '<div class="verification-steps">'
    for i, (num, label) in enumerate(steps, 1):
        if current_step > 3:
            step_class = "step-complete"
        elif i < current_step:
            step_class = "step-complete"
        elif i == current_step:
            step_class = "step-active"
        else:
            step_class = "step-pending"
        html += f'<div class="step-item"><div class="step-icon {step_class}">{num}</div><div class="step-label">{label}</div></div>'
        if i < 3:
            html += '<div style="flex:0.3;display:flex;align-items:center;justify-content:center;color:#ccc;">→</div>'
    html += '</div>'
    return html

def step1_initial_assessment(keyword, progress_placeholder):
    progress_placeholder.markdown(render_verification_steps(1), unsafe_allow_html=True)
    prompt = f'정보공개 청구 대상: "{keyword}"\n\n위 정보에 대해 1차 판단을 수행하세요.'
    return call_ai([{"role": "user", "content": prompt}], system=AGENT_1_SYSTEM_PROMPT)

def step2_legal_review(keyword, step1_result, progress_placeholder):
    progress_placeholder.markdown(render_verification_steps(2), unsafe_allow_html=True)
    prompt = f'[검토 대상]\n"{keyword}"\n\n[1차 판단 결과]\n{step1_result}\n\n위 1차 판단을 법적으로 검증하세요.'
    return call_ai([{"role": "user", "content": prompt}], system=AGENT_2_SYSTEM_PROMPT)

def step3_final_decision(keyword, step1_result, step2_result, progress_placeholder):
    progress_placeholder.markdown(render_verification_steps(3), unsafe_allow_html=True)
    prompt = f'[검토 대상]\n"{keyword}"\n\n[STEP 1: 1차 판단]\n{step1_result}\n\n[STEP 2: 법적 검토]\n{step2_result}\n\n위 결과를 종합하여 최종 판단을 내리세요.'
    return call_ai([{"role": "user", "content": prompt}], system=AGENT_3_SYSTEM_PROMPT)

def run_3step_verification(keyword, progress_placeholder, status_placeholder):
    results = {"keyword": keyword, "step1": None, "step2": None, "step3": None, "final": None, "retry_count": 0}

    status_placeholder.info("🔍 STEP 1: 1차 판단 에이전트 분석 중...")
    results["step1"] = step1_initial_assessment(keyword, progress_placeholder)

    status_placeholder.info("⚖️ STEP 2: 법적 검토 에이전트 검증 중...")
    results["step2"] = step2_legal_review(keyword, results["step1"], progress_placeholder)

    if "재검토필요" in results["step2"] or "재검토요청" in results["step2"]:
        results["retry_count"] += 1
        status_placeholder.warning("🔄 재검토 수행 중...")
        retry_prompt = f'정보공개 청구 대상: "{keyword}"\n\n[피드백]\n{results["step2"]}\n\n피드백을 반영하여 다시 판단하세요.'
        results["step1"] = call_ai([{"role": "user", "content": retry_prompt}], system=AGENT_1_SYSTEM_PROMPT)
        results["step2"] = step2_legal_review(keyword, results["step1"], progress_placeholder)

    status_placeholder.info("✅ STEP 3: 최종 판단 도출 중...")
    results["step3"] = step3_final_decision(keyword, results["step1"], results["step2"], progress_placeholder)
    results["final"] = results["step3"]

    progress_placeholder.markdown(render_verification_steps(4), unsafe_allow_html=True)
    status_placeholder.success(f"✅ 3단계 검증 완료 (재검토: {results['retry_count']}회)")

    return results


# ══════════════════════════════════════════════════════════════════════════════
# 유틸리티
# ══════════════════════════════════════════════════════════════════════════════

def parse_verdict(text):
    t = text[:200]
    if "비공개" in t and "부분공개" not in t:
        return "closed"
    if "부분공개" in t:
        return "partial"
    if "추가확인" in t or "추가 확인" in t:
        return "check"
    if "공개" in t:
        return "open"
    return "check"

def parse_confidence(text):
    if "신뢰도: 상" in text:
        return "상"
    elif "신뢰도: 하" in text:
        return "하"
    return "중"

def render_result_card(result_text, verdict_type):
    top_class = {"closed": "rcard-top-closed", "partial": "rcard-top-partial", "open": "rcard-top-open", "check": "rcard-top-check"}.get(verdict_type, "rcard-top-check")
    label_map = {"closed": ("비공개", "verdict-label-closed"), "partial": ("부분공개", "verdict-label-partial"), "open": ("공개", "verdict-label-open"), "check": ("추가 확인 필요", "verdict-label-check")}
    label, label_class = label_map.get(verdict_type, ("추가 확인 필요", "verdict-label-check"))

    summary = ""
    for line in result_text.split('\n')[:10]:
        if "판정 요약" in line:
            summary = line.replace("[판정 요약:", "").replace("]", "").strip()
            break

    confidence = parse_confidence(result_text)
    confidence_width = {"상": "90%", "중": "60%", "하": "30%"}.get(confidence, "60%")
    confidence_class = {"상": "confidence-high", "중": "confidence-medium", "하": "confidence-low"}.get(confidence, "confidence-medium")

    body_html = result_text.replace('[판정: 비공개]', '').replace('[판정: 부분공개]', '').replace('[판정: 공개]', '').replace('[판정: 추가확인필요]', '').replace('\n', '<br>')

    st.markdown(f"""
    <div class="rcard">
        <div class="{top_class}">
            <div class="{label_class}">{label} <span style="font-size:0.7rem;background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:10px;margin-left:8px;">3단계 검증</span></div>
            <div class="verdict-sub">{summary}</div>
            <div style="margin-top:8px;">
                <span style="font-size:0.72rem;color:#666;">판단 신뢰도: {confidence}</span>
                <div class="confidence-bar"><div class="confidence-fill {confidence_class}" style="width:{confidence_width}"></div></div>
            </div>
        </div>
        <div class="rcard-body">{body_html}</div>
    </div>
    """, unsafe_allow_html=True)

def case_query(messages_list):
    return call_ai(messages_list, system=CASE_SYSTEM_PROMPT)


# ══════════════════════════════════════════════════════════════════════════════
# 세션 초기화
# ══════════════════════════════════════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = []
if "keyword_result" not in st.session_state:
    st.session_state.keyword_result = None
if "verification_results" not in st.session_state:
    st.session_state.verification_results = None
if "last_keyword" not in st.session_state:
    st.session_state.last_keyword = ""
if "trigger_search" not in st.session_state:
    st.session_state.trigger_search = False


# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
  <h1>정보공개 체크봇 <span style="font-size:0.8rem;background:rgba(255,255,255,0.2);padding:3px 10px;border-radius:12px;margin-left:10px;">3단계 검증</span></h1>
  <p>서울특별시동부교육지원청 정보공개 판단 지원 서비스</p>
  <p style="font-size:0.75rem;opacity:0.7;margin-top:6px">🔍 1차 판단 → ⚖️ 법적 검토 → ✅ 최종 판단 | AI 3단계 교차 검증으로 판단 오류 최소화</p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 🔍 공개/비공개 검토하기")
    st.caption("3단계 AI 검증 시스템으로 판단 오류를 최소화합니다")

    st.markdown("**자주 묻는 사례**")
    examples = ["학폭위 회의록", "면접채점표", "감사계획서", "청사 평면도", "교사 징계서류", "예산안(미확정)", "CCTV 영상", "근무성적평정", "입찰 예정가격"]
    btn_cols = st.columns(3)
    for i, ex in enumerate(examples):
        if btn_cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.last_keyword = ex
            st.session_state.trigger_search = True

    st.markdown("")
    keyword_input = st.text_input("키워드 입력", value=st.session_state.last_keyword if st.session_state.trigger_search else "", placeholder="예: 학폭위 회의록", label_visibility="collapsed", key="keyword_text_input")
    search_btn = st.button("🔍 3단계 검증 시작", type="primary", use_container_width=True)

    do_search = False
    search_keyword = ""

    if st.session_state.trigger_search:
        do_search = True
        search_keyword = st.session_state.last_keyword
        st.session_state.trigger_search = False

    if search_btn:
        kw = keyword_input.strip() or st.session_state.last_keyword
        if kw:
            do_search = True
            search_keyword = kw
            st.session_state.last_keyword = kw

    if do_search and search_keyword:
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        results = run_3step_verification(search_keyword, progress_placeholder, status_placeholder)
        st.session_state.keyword_result = results["final"]
        st.session_state.verification_results = results

        verdict = parse_verdict(results["final"])
        confidence = parse_confidence(results["final"])
        record_keyword(search_keyword, verdict, confidence)
        st.rerun()

    if st.session_state.keyword_result:
        result_text = st.session_state.keyword_result
        verdict_type = parse_verdict(result_text)
        render_result_card(result_text, verdict_type)

        if st.session_state.verification_results:
            with st.expander("📋 상세 검토 과정 보기"):
                results = st.session_state.verification_results
                st.markdown("#### STEP 1: 1차 판단")
                st.markdown(f'<div class="review-box">{results["step1"]}</div>', unsafe_allow_html=True)
                st.markdown("#### STEP 2: 법적 검토")
                st.markdown(f'<div class="review-box">{results["step2"]}</div>', unsafe_allow_html=True)
                if results["retry_count"] > 0:
                    st.warning(f"⚠️ {results['retry_count']}회 재검토 수행됨")

with col_right:
    st.markdown("### 📚 유사사례 확인하기")

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("상황 입력", placeholder="구체적인 상황을 입력하세요", height=100, label_visibility="collapsed")
        col_s, col_c = st.columns([3, 1])
        send = col_s.form_submit_button("확인하기", type="primary", use_container_width=True)
        clear = col_c.form_submit_button("초기화", use_container_width=True)

    if send and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        with st.spinner("유사 사례 검토 중..."):
            reply = case_query(st.session_state.messages)
            record_case(user_input.strip())
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if clear:
        st.session_state.messages = []
        st.rerun()

    chat_container = st.container(height=480)
    with chat_container:
        if not st.session_state.messages:
            st.markdown('<div style="color:#bbb;font-size:0.84rem;text-align:center;padding-top:80px;line-height:1.9;">정보공개 청구 상황을 입력하시면<br>유사 사례를 찾아 안내해 드립니다.</div>', unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-msg-ai">{msg["content"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 통계
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")

verdict_labels = {"closed": "비공개", "partial": "부분공개", "open": "공개", "check": "추가확인필요"}

with st.expander("📊 검색 통계 보기"):
    stats = load_stats()
    keywords = stats.get("keywords", [])
    cases = stats.get("cases", [])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("공개/비공개 검토", f"{len(keywords)}회")
    c2.metric("유사사례 검색", f"{len(cases)}회")
    c3.metric("총 이용 횟수", f"{len(keywords) + len(cases)}회")
    c4.metric("3단계 검증", f"{len([k for k in keywords if k.get('verification_steps', 0) == 3])}건")

    if keywords:
        col_stat1, col_stat2 = st.columns([1, 1])
        with col_stat1:
            st.markdown("**키워드 순위**")
            kw_counter = Counter([k["keyword"] for k in keywords])
            for rank, (kw, cnt) in enumerate(kw_counter.most_common(10), 1):
                st.markdown(f'<div class="stat-rank"><div class="rank-num {"top3" if rank <= 3 else ""}">{rank}</div><span style="flex:1">{kw}</span><span style="font-weight:500">{cnt}회</span></div>', unsafe_allow_html=True)
        with col_stat2:
            st.markdown("**판정 분포**")
            verdict_counter = Counter([k["verdict"] for k in keywords])
            colors = {"closed": "#E24B4A", "partial": "#EF9F27", "open": "#639922", "check": "#378ADD"}
            for v, cnt in verdict_counter.most_common():
                pct = round(cnt / len(keywords) * 100)
                st.markdown(f'<div class="stat-rank"><div style="width:10px;height:10px;border-radius:50%;background:{colors.get(v, "#888")}"></div><span style="flex:1">{verdict_labels.get(v, v)}</span><span style="font-weight:500">{cnt}건 ({pct}%)</span></div>', unsafe_allow_html=True)

st.markdown('<div style="font-size:0.72rem;color:#aaa;text-align:center;line-height:1.9;margin-top:12px;">🔒 3단계 AI 검증: 1차 판단 → 법적 검토 → 최종 판단<br>정보공개법 · 서울교육청 비공개대상정보 세부기준 · 행안부 운영안내서 · 서울시 업무매뉴얼</div>', unsafe_allow_html=True)
