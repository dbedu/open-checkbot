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

.detail-section {
    background: #fafbfc;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.detail-section-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #1a4a8a;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e0e0e0;
}
.detail-section-content {
    font-size: 0.82rem;
    line-height: 1.75;
    color: #444;
}

.disclaimer-box {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-left: 4px solid #6c757d;
    border-radius: 4px;
    padding: 12px 16px;
    margin-top: 16px;
    font-size: 0.78rem;
    color: #555;
    line-height: 1.6;
}
.disclaimer-box strong {
    color: #333;
}

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

.verified-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #e8f5e9;
    color: #2e7d32;
    font-size: 0.7rem;
    padding: 3px 8px;
    border-radius: 10px;
    margin-left: 8px;
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
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius:8px;
    border:1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ── 3단계 검증 시스템 프롬프트 ──────────────────────────────────────
STEP1_SYSTEM_PROMPT = """당신은 정보공개 판단을 위한 1차 분석 에이전트입니다.

## 참고 자료
① 공공기관의 정보공개에 관한 법률 [법률 제19408호, 2023.11.17]
② 정보공개법 시행령 [대통령령 제35948호, 2026.1.2]
③ 정보공개법 시행규칙 [행정안전부령 제576호, 2025.9.19]
④ 서울특별시교육청 행정정보 공개 조례 [제9796호, 2025.10.2]
⑤ 서울특별시교육청 비공개대상정보 세부기준 (E1~E8 코드 체계)
⑥ 2024년 정보공개 운영안내서 (행정안전부)
⑦ 2026 정보공개 업무 매뉴얼 (서울특별시, 289페이지)
⑧ 2023 서울특별시 비공개 세부기준
⑨ 2023 정보공개 연차보고서

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

## 정보공개 연차보고서(2023) 교육청 실제 공개·비공개 사례

### 서울특별시교육청 사례
공개: 교육환경개선사업 예산 현황, 언론 홍보비 집행 현황, 교원의 음주운전 건수, 각급학교 석면건축물 현황
비공개:
- 교원 임용시험 감독관 교육자료 → 제5호 (시험관리 공정성)
- 교육감 선발 후기 일반고 지원 현황 등 배정 관련 자료 → 제5호
- 교과서 채택 정보 → 제7호 (경영·영업상 비밀)

### 시도교육청 비공개 사례 모음 (2023 연차보고서 p.50~51)
- 학생별 배정 희망 및 실제 배정학교 → 제6호 개인정보
- 유치원 원장 감사보고서 → 제5호·제6호
- 학교별 자율감사 결과보고서 → 제6호
- 학생선도위원회 회의내용 및 결과 → 제6호
- 교원소청심사위원회 판결문 → 제1호 (법령상 비밀)
- 중등학교 교사임용 감독관 교육자료 → 제5호
- 성고충심의위원회 회의록 → 제4호·제6호
- 교육청 대변인 공모 배점 기준 → 제5호
- 특정인에 대한 감사결과 및 보고서 → 제6호
- 채점기준 및 등수 (입시) → 제5호
- 중고교 임용자 현황 → 제5호
- 징계처분 변경 청구 회의록 → 제1호
- 학교혁신의회 사안보고서 → 제1호
- 교육환경보호구역 심의 정보 → 제5호
- 직장내 괴롭힘 판단 전문위원회 회의록 → 제1호·제5호·제6호
- 행정심판 구술심리 회의록 → 제1호·제5호
- 학폭위결정통지문과 관련 회의록 → 제1호 (학폭법 제21조)
- 학교폭력 관련 회의록 → 제1호·제5호·제6호
- 학교폭력대책심의위원 위원 명단 → 제1호
- 학교 건축도면 → 제3호 (안전 우려)
- 대안교육기관 등록위원회 구성내역 및 명부 → 제5호·제6호

### 시도교육청 공개 사례 모음 (2023 연차보고서)
- 급식실 현대화 대상 학교 현황 → 공개
- 학교 CCTV 설치 현황 및 인력 현황 → 공개 (설치 현황만, 위치·경비정보 제외)
- 공립학교별 지방공무원 정원 현황 → 공개
- 학교 안전사고 발생 신고서 → 공개
- 학교알리미 학교폭력 발생 현황 자료 (통계) → 공개
- 학교 석면 해체공사 시행 예정 학교 현황 → 공개
- 초등돌봄교실 운영 현황 → 공개
- 학원 및 교습소 현황 → 공개
- 기간제교사 성과상여금 지급 계획 → 공개
- 교원 관련 연구회 운영 현황 → 공개
- 폐교재산 활용 계획 → 공개
- 건강장애 학생 복귀 프로그램 운영 현황 → 공개

## 정보공개 행정소송 판례 (2023 연차보고서 p.59~61)

### 대법원 2022두45586 — 학교 교육부 감사결과 및 신축공사 자료
- 판결: 완료된 교육부 감사결과 원본, 이행 조치사항 원본 → 공개 인용
- 진행 중인 건물 신축공사 관련 자료 → 비공개 유지
- 핵심: 감사 완료 후에는 원칙적 공개 대상

### 서울행정법원 2021구합85068 — 건축 현장점검 결과보고서
- 판결: 현장점검 결과보고서 → 공개 (제7호 비공개 사유 해당 안 됨)
- 전문 공법·기술이 포함된 내부심의서류 → 비공개 유지
- 핵심: 단순 점검·확인 결과는 경영·영업상 비밀이 아님

### 서울행정법원 2022구합70162 — 심사위원회 심사자료
- 판결: 제7호(경영·영업상 비밀) 적용 불가 → 공개 인용
- 핵심: 제7호 비공개는 정당한 이익 존재 여부를 엄격하게 판단해야 함

### 부산지방법원 2022구합23051 — 혐의없음 처분 후 수사 자료
- 판결: 혐의없음 처분된 사건의 수사자료는 제4호 비공개 사유 해당 안 됨
- 개인식별정보 제외 후 공개
- 핵심: 수사 종결 후 자료는 알권리 보장 목적으로 공개 가능

## 1차 판단 출력 형식 (JSON)
다음 JSON 형식으로만 출력하세요:
{
  "정보유형": "정보의 종류",
  "초기판단": "공개|비공개|부분공개",
  "법적근거": {
    "정보공개법": "제9조 제1항 제X호 - 조항 내용",
    "개별법령": "해당 법령 조항 (있는 경우)",
    "E코드": "EX-XX",
    "E코드페이지": "p.XX",
    "E코드내용": "세부기준 내용"
  },
  "판단근거": {
    "근거설명": "비공개/부분공개 판단의 구체적 이유",
    "행안부운영안내서": "Q.XXX (p.XXX) - 관련 내용 (해당시)",
    "서울시매뉴얼": "p.XXX - 관련 내용 (해당시)"
  },
  "관련사례": {
    "연차보고서": "관련 사례 내용 (해당시)",
    "기타사례": "운영안내서/매뉴얼 사례 (해당시)"
  },
  "참고판례": "관련 판례 (해당시, 없으면 '해당없음')",
  "부분공개검토": {
    "가능여부": "가능|불가능|검토필요",
    "방법": "부분공개 가능시 구체적 방법"
  },
  "신뢰도": "상|중|하",
  "불확실요소": ["불확실한 부분 목록"]
}"""

STEP2_SYSTEM_PROMPT = """당신은 정보공개 판단의 법적 검토를 수행하는 2차 검증 에이전트입니다.
1차 판단 결과를 검토하여 법적 정확성을 검증합니다.

## 검토 체크리스트

### 비공개 사유 검토 (정보공개법 제9조 제1항)
| 호 | 비공개 사유 | 검토 포인트 |
|----|-------------|-------------|
| 1호 | 법률에 의해 비밀/비공개로 규정된 정보 | 구체적 법령 조항 존재 여부 |
| 2호 | 국가안전보장·국방·통일·외교관계 | 실질적 위험 존재 여부 |
| 3호 | 국민의 생명·신체·재산 보호 | 구체적 위험 발생 가능성 |
| 4호 | 수사·재판·공소제기/유지 관련 | 진행 중 여부 확인 |
| 5호 | 감사·감독·규제·입찰·계약 등 공정성 | 의사결정 완료 여부 |
| 6호 | 개인정보 (사생활 비밀·자유 침해) | 개인식별 가능 여부, 공익 비교 |
| 7호 | 법인·단체의 경영·영업비밀 | 정당한 이익 침해 여부 |
| 8호 | 부동산 투기·매점매석 유발 우려 | 실질적 우려 존재 여부 |

### 필수 검토 사항
1. 비공개 사유가 제9조 제1항 각호에 명확히 해당하는가?
2. 추상적 사유(업무 혼란, 관행)로만 판단하지 않았는가?
3. 부분공개 가능성을 충분히 검토했는가?
4. 개인식별정보만 삭제하면 공개 가능하지 않은가?
5. 공익이 비공개 이익보다 크지 않은가?
6. 관련 판례와 일치하는가?

## 출력 형식 (JSON)
{
  "검토결과": "적정|부적정|재검토필요",
  "적정성점수": 1-10,
  "발견된문제점": ["문제점 목록"],
  "수정권고사항": ["권고사항 목록"],
  "부분공개가능성": {
    "검토결과": "검토완료|미검토|추가검토필요",
    "의견": "부분공개 관련 의견"
  },
  "공익비교형량": "공익/사익 비교 의견",
  "판례일치여부": "일치|불일치|해당판례없음"
}"""

STEP3_SYSTEM_PROMPT = """당신은 정보공개 판단의 최종 결론을 도출하는 3차 종합 에이전트입니다.
1차 판단과 2차 법적 검토를 종합하여 최종 결론을 제시합니다.

## 자가 검증 질문 (반드시 확인)
1. "이 판단이 법원에서 다퉈지면 유지될 수 있는가?"
2. "비공개 사유가 구체적이고 명확한가?"
3. "부분공개로 공익 목적을 달성할 수 있지 않은가?"
4. "동일 유형의 다른 청구에도 일관되게 적용 가능한가?"
5. "국민의 알권리를 최대한 보장했는가?"

## 최종 출력 형식

다음 형식으로 정확히 출력하세요:

[최종판정: 공개|비공개|부분공개]
[판정요약: 한 줄 요약]

---

## 1. 법적근거

### 정보공개법
- 제9조 제1항 제X호: 조항 내용

### 개별 법령
- 해당 법령 조항 (있는 경우, 없으면 "해당없음")

### 서울특별시교육청 비공개대상정보 세부기준
- 코드: EX-XX (p.XX)
- 내용: 세부기준 내용

---

## 2. 판단근거

[비공개/부분공개 판단의 구체적 이유를 상세히 설명]

### 참고 자료
- 행정안전부 정보공개 운영안내서(2024): Q.XXX (p.XXX) - 관련 내용
- 서울특별시 정보공개 업무매뉴얼(2026): p.XXX - 관련 내용

---

## 3. 관련사례

### 정보공개 연차보고서(2023) 사례
- [관련 사례 내용]

### 기타 참고 사례
- [운영안내서/매뉴얼 등의 유사 사례]

---

## 4. 참고 판례

[관련 판례가 있는 경우 기재, 없으면 "관련 판례 없음" 표시]
- 판례명: 
- 판결요지:
- 시사점:

---

## 5. 실무 처리 방법

① [첫 번째 처리 단계]
② [두 번째 처리 단계]
③ [세 번째 처리 단계]

---

## 6. 부분공개 검토 (해당시)

- 공개 가능 부분:
- 비공개 대상 부분:
- 처리 방법:

---"""

CASE_SYSTEM_PROMPT = """당신은 서울특별시동부교육지원청 정보공개 업무 전문 AI 도우미입니다.
담당자가 입력한 구체적인 상황에 대해 행정안전부 운영안내서와 서울특별시 매뉴얼의 실제 사례를 조합하여 유사 사례를 안내합니다.

## 참고 자료
- 2024년 정보공개 운영안내서 (행정안전부)
- 2026 정보공개 업무 매뉴얼 (서울특별시)
- 2023 서울특별시 비공개 세부기준
- 2023 정보공개 연차보고서 교육청 공개·비공개 사례 (p.50~51)
- 2023 정보공개 행정소송·심판 판례 (p.59~61)
- 공공기관의 정보공개에 관한 법률 및 시행령

## 교육청 실제 사례 요약 (2023 연차보고서)

### 비공개로 결정된 교육청 사례
- 교원 임용시험 감독관 교육자료 → 제5호
- 학생별 배정 희망 및 실제 배정학교 → 제6호
- 학교별 자율감사 결과보고서 → 제6호
- 학생선도위원회 회의내용 및 결과 → 제6호
- 교원소청심사위원회 판결문 → 제1호
- 성고충심의위원회 회의록 → 제4호·제6호
- 직장내 괴롭힘 판단 전문위원회 회의록 → 제1호·제5호·제6호
- 학폭위결정통지문과 관련 회의록 → 제1호 (학폭법 제21조)
- 학교폭력 관련 회의록 → 제1호·제5호·제6호
- 학교폭력대책심의위원 위원 명단 → 제1호
- 입시 채점기준 및 등수 → 제5호
- 학교 건축도면 → 제3호

### 공개로 결정된 교육청 사례
- 급식실 현대화 대상 학교 현황, 공립학교별 정원 현황, 학교 안전사고 신고서, 학교폭력 발생 현황 통계, 초등돌봄교실 운영 현황, 폐교재산 활용 계획

### 행정소송 핵심 판례
- 완료된 감사결과 → 원칙적 공개 (대법원 2022두45586)
- 단순 현장점검 결과보고서 → 제7호 비공개 사유 해당 안 됨 (서울행정법원 2021구합85068)
- 제7호 비공개는 정당한 이익 엄격 판단 필요 (서울행정법원 2022구합70162)
- 혐의없음 처분 후 수사자료 → 제4호 비공개 사유 해당 안 됨 (부산지법 2022구합23051)

## 유사사례 답변 형식 (반드시 준수)

### 상황 요약
입력된 상황을 한 줄로 요약

### 유사 사례 1 — 행정안전부 운영안내서
- 출처: 행정안전부 정보공개 운영안내서(2024) Q.XXX (p.XXX)
- 사례 내용: 해당 사례의 구체적 내용
- 결정 결과: 공개 / 비공개 / 부분공개
- 적용 근거: 정보공개법 제9조 제1항 제X호

### 유사 사례 2 — 서울특별시 업무매뉴얼
- 출처: 서울특별시 정보공개 업무매뉴얼(2026) p.XXX
- 사례 내용: 해당 사례의 구체적 내용
- 결정 결과: 공개 / 비공개 / 부분공개
- 심의회 결과: (해당하는 경우 심의회 차수와 결정 내용)

### 현재 상황에 적용
입력된 상황에 위 사례들을 적용한 판단 방향 안내

### 권고 처리 방법
① 단계별 실무 처리 방법

---

⚠️ **안내사항**
본 내용은 정보공개 판단을 위한 참고자료입니다. 공개 여부에 대한 최종 결정은 해당 기관 및 담당자의 권한과 책임이며, AI는 관련 법령·사례·자료를 제공하여 판단을 지원하는 역할을 수행합니다.

한국어로 명확하게 작성하세요."""

# ── 통계 저장·불러오기 ────────────────────────────────────
STATS_FILE = "search_stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"keywords": [], "cases": []}

def save_stats(data):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def record_keyword(keyword, verdict, confidence="중"):
    stats = load_stats()
    stats["keywords"].append({
        "keyword": keyword,
        "verdict": verdict,
        "confidence": confidence,
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

# ── Groq 클라이언트 ───────────────────────────────────────
@st.cache_resource
def get_client():
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def call_ai(messages_list, system=None):
    client = get_client()
    if not client:
        return "⚠️ API 키가 설정되지 않았습니다."
    try:
        full_messages = [{"role": "system", "content": system}] + messages_list
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_messages,
            max_tokens=2500,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류: {str(e)}"

# ── 3단계 검증 시스템 ─────────────────────────────────────
def run_step1(keyword):
    """1차 판단 에이전트"""
    prompt = f'"{keyword}"에 대해 정보공개 판단을 수행하세요. 반드시 지정된 JSON 형식으로만 출력하세요.'
    return call_ai([{"role": "user", "content": prompt}], system=STEP1_SYSTEM_PROMPT)

def run_step2(keyword, step1_result):
    """2차 법적 검토 에이전트"""
    prompt = f"""다음 1차 판단 결과를 법적으로 검토하세요.

키워드: "{keyword}"

1차 판단 결과:
{step1_result}

반드시 지정된 JSON 형식으로만 출력하세요."""
    return call_ai([{"role": "user", "content": prompt}], system=STEP2_SYSTEM_PROMPT)

def run_step3(keyword, step1_result, step2_result):
    """3차 최종 판단 에이전트"""
    prompt = f"""다음 1차 판단과 2차 법적 검토를 종합하여 최종 결론을 도출하세요.

키워드: "{keyword}"

1차 판단 결과:
{step1_result}

2차 법적 검토 결과:
{step2_result}

반드시 지정된 형식으로 출력하세요. 자가 검증 질문을 모두 확인한 후 답변하세요."""
    return call_ai([{"role": "user", "content": prompt}], system=STEP3_SYSTEM_PROMPT)

def run_3step_verification(keyword, progress_placeholder):
    """3단계 검증 전체 실행"""
    results = {}

    # Step 1
    progress_placeholder.markdown("🔍 **1단계: 초기 분석 중...**")
    results["step1"] = run_step1(keyword)

    # Step 2
    progress_placeholder.markdown("⚖️ **2단계: 법적 검토 중...**")
    results["step2"] = run_step2(keyword, results["step1"])

    # 재검토 필요 여부 확인
    if "재검토필요" in results["step2"]:
        progress_placeholder.markdown("🔄 **재검토 수행 중...**")
        results["step1"] = run_step1(keyword + " (재검토: 부분공개 가능성 및 구체적 근거 보완)")
        results["step2"] = run_step2(keyword, results["step1"])

    # Step 3
    progress_placeholder.markdown("✅ **3단계: 최종 판단 종합 중...**")
    results["step3"] = run_step3(keyword, results["step1"], results["step2"])

    progress_placeholder.markdown("✨ **3단계 검증 완료!**")

    return results

def case_query(messages_list):
    return call_ai(messages_list, system=CASE_SYSTEM_PROMPT)

# ── 세션 초기화 ──────────────────────────────────────────
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

def parse_verdict(text):
    t = text[:150]
    if "비공개" in t and "부분공개" not in t: return "closed"
    if "부분공개" in t: return "partial"
    if "추가확인" in t or "추가 확인" in t: return "check"
    if "공개" in t: return "open"
    return "check"

def parse_confidence(text):
    if '"신뢰도": "상"' in text or "신뢰도: 상" in text:
        return "상"
    elif '"신뢰도": "하"' in text or "신뢰도: 하" in text:
        return "하"
    return "중"

def render_result_card(result_text, verdict_type, verification_results=None):
    top_class = {
        "closed": "rcard-top-closed",
        "partial": "rcard-top-partial",
        "open":    "rcard-top-open",
        "check":   "rcard-top-check"
    }.get(verdict_type, "rcard-top-check")

    label_map = {
        "closed":  ("비공개",        "verdict-label-closed"),
        "partial": ("부분공개",       "verdict-label-partial"),
        "open":    ("공개",           "verdict-label-open"),
        "check":   ("추가 확인 필요", "verdict-label-check")
    }
    label, label_class = label_map.get(verdict_type, ("추가 확인 필요", "verdict-label-check"))

    # 판정 요약 추출
    summary = ""
    for line in result_text.split('\n'):
        if "판정요약" in line or "판정 요약" in line:
            summary = line.replace("[판정요약:", "").replace("[판정 요약:", "").replace("]", "").strip()
            break

    # 메인 결과 카드
    st.markdown(f"""
    <div class="rcard">
        <div class="{top_class}">
            <div class="{label_class}">{label} <span class="verified-badge">✓ 3단계 검증 완료</span></div>
            <div class="verdict-sub">{summary}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 상세 검토내용 (Expander)
    with st.expander("📋 상세 검토내용"):
        # 최종 결과에서 섹션별로 파싱하여 표시
        sections = parse_final_result_sections(result_text)

        # 1. 법적근거
        if sections.get("법적근거"):
            st.markdown("""
            <div class="detail-section">
                <div class="detail-section-title">1. 법적근거</div>
                <div class="detail-section-content">{}</div>
            </div>
            """.format(sections["법적근거"].replace("\n", "<br>")), unsafe_allow_html=True)

        # 2. 판단근거
        if sections.get("판단근거"):
            st.markdown("""
            <div class="detail-section">
                <div class="detail-section-title">2. 판단근거</div>
                <div class="detail-section-content">{}</div>
            </div>
            """.format(sections["판단근거"].replace("\n", "<br>")), unsafe_allow_html=True)

        # 3. 관련사례
        if sections.get("관련사례"):
            st.markdown("""
            <div class="detail-section">
                <div class="detail-section-title">3. 관련사례</div>
                <div class="detail-section-content">{}</div>
            </div>
            """.format(sections["관련사례"].replace("\n", "<br>")), unsafe_allow_html=True)

        # 4. 참고 판례
        if sections.get("참고판례"):
            st.markdown("""
            <div class="detail-section">
                <div class="detail-section-title">4. 참고 판례</div>
                <div class="detail-section-content">{}</div>
            </div>
            """.format(sections["참고판례"].replace("\n", "<br>")), unsafe_allow_html=True)

        # 5. 실무 처리 방법
        if sections.get("실무처리"):
            st.markdown("""
            <div class="detail-section">
                <div class="detail-section-title">5. 실무 처리 방법</div>
                <div class="detail-section-content">{}</div>
            </div>
            """.format(sections["실무처리"].replace("\n", "<br>")), unsafe_allow_html=True)

        # 6. 부분공개 검토 (해당시)
        if sections.get("부분공개") and verdict_type == "partial":
            st.markdown("""
            <div class="detail-section">
                <div class="detail-section-title">6. 부분공개 검토</div>
                <div class="detail-section-content">{}</div>
            </div>
            """.format(sections["부분공개"].replace("\n", "<br>")), unsafe_allow_html=True)

        # 면책 조항
        st.markdown("""
        <div class="disclaimer-box">
            <strong>⚠️ 안내사항</strong><br>
            본 내용은 정보공개 판단을 위한 <strong>참고자료</strong>입니다.<br>
            공개 여부에 대한 <strong>최종 결정은 해당 기관 및 담당자의 권한과 책임</strong>이며, 
            AI는 관련 법령·사례·자료를 제공하여 판단을 지원하는 역할을 수행합니다.<br>
            분쟁 가능성이 있는 사안은 정보공개 전담부서 또는 상급자와 협의하시기 바랍니다.
        </div>
        """, unsafe_allow_html=True)

def parse_final_result_sections(text):
    """최종 결과 텍스트에서 섹션별로 내용 추출"""
    sections = {
        "법적근거": "",
        "판단근거": "",
        "관련사례": "",
        "참고판례": "",
        "실무처리": "",
        "부분공개": ""
    }

    current_section = None
    current_content = []

    for line in text.split("\n"):
        line_stripped = line.strip()

        # 섹션 헤더 감지
        if "## 1. 법적근거" in line or "1. 법적근거" in line_stripped:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "법적근거"
            current_content = []
        elif "## 2. 판단근거" in line or "2. 판단근거" in line_stripped:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "판단근거"
            current_content = []
        elif "## 3. 관련사례" in line or "3. 관련사례" in line_stripped:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "관련사례"
            current_content = []
        elif "## 4. 참고 판례" in line or "4. 참고 판례" in line_stripped or "## 4. 참고판례" in line:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "참고판례"
            current_content = []
        elif "## 5. 실무 처리" in line or "5. 실무 처리" in line_stripped:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "실무처리"
            current_content = []
        elif "## 6. 부분공개" in line or "6. 부분공개" in line_stripped:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "부분공개"
            current_content = []
        elif current_section:
            # 다음 대섹션 시작 전까지 내용 수집
            if line_stripped and not line_stripped.startswith("[최종판정") and not line_stripped.startswith("[판정요약"):
                current_content.append(line)

    # 마지막 섹션 저장
    if current_section and current_content:
        sections[current_section] = "\n".join(current_content)

    return sections

# ── 헤더 ─────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>정보공개 체크봇</h1>
  <p>서울특별시동부교육지원청 정보공개 판단 지원 서비스입니다</p>
  <p style="font-size:0.75rem;opacity:0.7;margin-top:6px">
    참고자료: 정보공개법·시행령·서울교육청 조례·비공개 세부기준(E1~E8)·행안부 운영안내서(2024)·서울시 업무매뉴얼(2026)·정보공개 연차보고서(2023)·행정소송 판례
  </p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

# ━━━━ 왼쪽: 공개/비공개 검토하기 ━━━━━━━━━━━━━━━━━━━━━━━━
with col_left:
    st.markdown("### 공개/비공개 검토하기")

    st.caption("자주 묻는 사례")
    examples = [
        "학폭위 회의록", "면접채점표", "감사계획서",
        "청사 평면도", "교사 징계서류", "예산안(미확정)",
        "CCTV 영상", "근무성적평정", "입찰 예정가격"
    ]
    btn_cols = st.columns(3)
    for i, ex in enumerate(examples):
        if btn_cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.last_keyword = ex
            st.session_state.trigger_search = True

    st.markdown("")

    keyword_input = st.text_input(
        "키워드 직접 입력",
        value=st.session_state.last_keyword if st.session_state.trigger_search else "",
        placeholder="예: 학폭위 회의록, 면접채점표, 청사 평면도",
        label_visibility="collapsed",
        key="keyword_text_input"
    )

    search_btn = st.button("확인하기", type="primary", use_container_width=True)

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

        with st.spinner(f"'{search_keyword}' 3단계 검증 중..."):
            results = run_3step_verification(search_keyword, progress_placeholder)
            st.session_state.verification_results = results
            st.session_state.keyword_result = results["step3"]

            verdict = parse_verdict(results["step3"])
            confidence = parse_confidence(results["step1"])
            record_keyword(search_keyword, verdict, confidence)

        progress_placeholder.empty()
        st.rerun()

    if st.session_state.keyword_result:
        result_text = st.session_state.keyword_result
        verdict_type = parse_verdict(result_text)
        render_result_card(result_text, verdict_type, st.session_state.verification_results)

# ━━━━ 오른쪽: 유사사례 확인하기 ━━━━━━━━━━━━━━━━━━━━━━━━━
with col_right:
    st.markdown("### 유사사례 확인하기")

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "상황 입력",
            placeholder="구체적인 상황을 입력하세요",
            height=100,
            label_visibility="collapsed"
        )
        col_s, col_c = st.columns([3, 1])
        send  = col_s.form_submit_button("확인하기", type="primary", use_container_width=True)
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
            st.markdown("""
            <div style="color:#bbb;font-size:0.84rem;text-align:center;padding-top:80px;line-height:1.9;">
                정보공개 청구 상황을 입력하시면<br>
                행정안전부 운영안내서와 서울특별시 매뉴얼의<br>
                유사 사례를 찾아 안내해 드립니다.<br><br>
                예: "학부모가 학폭위 가해학생 징계 결과를 청구했습니다."<br>
                예: "감사 진행 중인 학교 감사계획서를 언론사에서 청구했습니다."
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

# ── 통계 섹션 ─────────────────────────────────────────────
st.markdown("---")

verdict_labels = {
    "closed": "비공개",
    "partial": "부분공개",
    "open": "공개",
    "check": "추가확인필요"
}

with st.expander("📊 검색 통계 보기"):
    stats = load_stats()
    keywords = stats.get("keywords", [])
    cases    = stats.get("cases", [])
    total    = len(keywords) + len(cases)

    c1, c2, c3 = st.columns(3)
    c1.metric("공개/비공개 검토", f"{len(keywords)}회")
    c2.metric("유사사례 검색", f"{len(cases)}회")
    c3.metric("총 이용 횟수", f"{total}회")

    st.markdown("")

    if keywords:
        col_stat1, col_stat2 = st.columns([1, 1])

        with col_stat1:
            st.markdown("**키워드 검색 순위 (상위 10개)**")
            kw_counter = Counter([k["keyword"] for k in keywords])
            for rank, (kw, cnt) in enumerate(kw_counter.most_common(10), 1):
                top3_class = "top3" if rank <= 3 else ""
                st.markdown(
                    f'<div class="stat-rank">'
                    f'<div class="rank-num {top3_class}">{rank}</div>'
                    f'<span style="flex:1">{kw}</span>'
                    f'<span style="font-weight:500;color:#1a4a8a">{cnt}회</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        with col_stat2:
            st.markdown("**판정 결과 분포**")
            verdict_counter = Counter([k["verdict"] for k in keywords])
            verdict_colors = {
                "closed":  "#E24B4A",
                "partial": "#EF9F27",
                "open":    "#639922",
                "check":   "#378ADD"
            }
            total_kw = len(keywords)
            for v, cnt in verdict_counter.most_common():
                label = verdict_labels.get(v, v)
                color = verdict_colors.get(v, "#888")
                pct   = round(cnt / total_kw * 100) if total_kw else 0
                st.markdown(
                    f'<div class="stat-rank">'
                    f'<div style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0"></div>'
                    f'<span style="flex:1">{label}</span>'
                    f'<span style="font-weight:500;color:{color}">{cnt}건 ({pct}%)</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown("")
        st.markdown("**최근 검색 10건**")
        recent = keywords[-10:][::-1]
        for r in recent:
            vlabel = verdict_labels.get(r.get("verdict", ""), "")
            st.markdown(
                f'<div style="font-size:0.8rem;padding:5px 0;border-bottom:0.5px solid #f0f0f0;">'
                f'<span style="color:#999;margin-right:10px">{r["time"]}</span>'
                f'<span style="margin-right:8px">{r["keyword"]}</span>'
                f'<span style="color:#666">→ {vlabel}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("아직 검색 데이터가 없습니다.")

    if cases:
        st.markdown("")
        st.markdown("**유사사례 검색 최근 10건**")
        recent_cases = cases[-10:][::-1]
        for c in recent_cases:
            st.markdown(
                f'<div style="font-size:0.8rem;padding:5px 0;border-bottom:0.5px solid #f0f0f0;">'
                f'<span style="color:#999;margin-right:10px">{c["time"]}</span>'
                f'<span>{c["query"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

# ── 하단 ─────────────────────────────────────────────────
st.markdown("""
<div style="font-size:0.72rem;color:#aaa;text-align:center;line-height:1.9;margin-top:12px;">
    정보공개법(법률 제19408호) · 시행령(대통령령 제35948호) · 시행규칙(행정안전부령 제576호)<br>
    서울특별시교육청 행정정보 공개 조례(제9796호) · 서울교육청 비공개대상정보 세부기준(E1~E8)<br>
    2024 정보공개 운영안내서(행정안전부) · 2026 정보공개 업무 매뉴얼(서울특별시) · 2023 정보공개 연차보고서
</div>
<div style="font-size:0.7rem;color:#888;text-align:center;margin-top:8px;padding:10px;background:#f9f9f9;border-radius:6px;">
    ⚠️ 본 서비스는 정보공개 판단을 위한 <b>참고자료 제공 목적</b>입니다.<br>
    공개 여부에 대한 <b>최종 결정 권한과 책임은 해당 기관 및 담당자</b>에게 있으며, AI는 판단 지원 역할을 수행합니다.
</div>
""", unsafe_allow_html=True)
