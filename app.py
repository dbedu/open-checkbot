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
.disclaimer-box strong { color: #333; }

.input-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #1a4a8a;
    margin-bottom: 6px;
    margin-top: 4px;
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

/* 모바일 반응형 */
@media (max-width: 768px) {
    .main-header h1 { font-size: 1.3rem !important; }
    .main-header p  { font-size: 0.82rem !important; }
    .rcard-body     { font-size: 0.8rem !important; }
    .detail-section { padding: 10px 12px !important; }
    [data-testid="column"] { min-width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)

# ── 3단계 검증 시스템 프롬프트 ────────────────────────────
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
- 학생별 배정 희망 및 실제 배정학교 → 제6호
- 유치원 원장 감사보고서 → 제5호·제6호
- 학교별 자율감사 결과보고서 → 제6호
- 학생선도위원회 회의내용 및 결과 → 제6호
- 교원소청심사위원회 판결문 → 제1호
- 중등학교 교사임용 감독관 교육자료 → 제5호
- 성고충심의위원회 회의록 → 제4호·제6호
- 교육청 대변인 공모 배점 기준 → 제5호
- 특정인에 대한 감사결과 및 보고서 → 제6호
- 채점기준 및 등수 (입시) → 제5호
- 직장내 괴롭힘 판단 전문위원회 회의록 → 제1호·제5호·제6호
- 행정심판 구술심리 회의록 → 제1호·제5호
- 학폭위결정통지문과 관련 회의록 → 제1호 (학폭법 제21조)
- 학교폭력 관련 회의록 → 제1호·제5호·제6호
- 학교폭력대책심의위원 위원 명단 → 제1호
- 학교 건축도면 → 제3호
- 대안교육기관 등록위원회 구성내역 및 명부 → 제5호·제6호

### 시도교육청 공개 사례 모음 (2023 연차보고서)
- 급식실 현대화 대상 학교 현황, 학교 CCTV 설치 현황(위치·경비정보 제외), 공립학교별 지방공무원 정원 현황, 학교 안전사고 발생 신고서, 학교알리미 학교폭력 발생 현황 통계, 초등돌봄교실 운영 현황, 학원 및 교습소 현황, 기간제교사 성과상여금 지급 계획, 폐교재산 활용 계획

## 정보공개 행정소송 판례 (2023 연차보고서 p.59~61)
- 대법원 2022두45586: 완료된 감사결과 원본 → 공개, 진행 중인 공사자료 → 비공개
- 서울행정법원 2021구합85068: 현장점검 결과보고서 → 제7호 해당 안 됨 → 공개
- 서울행정법원 2022구합70162: 제7호 비공개는 정당한 이익 엄격 판단 필요
- 부산지방법원 2022구합23051: 혐의없음 처분 후 수사자료 → 제4호 해당 안 됨 → 공개

## 서울특별시동부교육지원청 2025년 실제 정보공개 처리 사례 (처리대장 기반)

### 공개 결정 사례 (2025년)
- 특수학급 과밀현황(초등과) → 공개
- 출장비·출장내역·조직개편(행지과) → 공개
- 전기요금·공공요금(행지과) → 공개
- 석면해체공사 현황(시설과) → 공개 (교육시설안전과 홈페이지 게시물 안내)
- 공사계약·설계용역 낙찰 현황(재정지원과) → 공개
- 조리실 공기질·환기장치(평건과) → 공개 (일부 부존재 포함)
- 학교도면 배치도·입면도(시설과) → 공개, 평면도·단면도는 보안상 열람·시청으로만 공개(제3호)
- 학원·교습소 운영 현황(평건과) → 공개
- 기록물관리 계획(행지과) → 공개 (2022년분 부존재)
- 개인 근무성적평정점(본인 청구, 중등과) → 공개 (교육공무원 승진규정 제26조)
- 홍보비·광고비 집행현황(행지과) → 공개
- 판결문(부동산인도소송, 재정지원과) → 개인정보 제외 부분공개(제6호)
- 담당자 연락처·기록연구사 정보(행지과) → 즉시공개 (홈페이지 공개자료)
- 학교 연락처·주소록(행지과) → 즉시공개 (홈페이지·학교알리미 안내)
- 신문구독 내역(행지과) → 정보부존재 (해당 신문 미구독)

### 비공개 결정 사례 (2025년)
- 학교폭력 사안조사 보고서(생활교육과) → 비공개 [제1호·제6호, 학폭법 제21조]
- 학교폭력 신고건수·심의위 심의건수(생활교육과) → 비공개 [부존재, 제11조제5항제1호]
- 그린스마트 공간재구조화 업체 제안서(재정지원과) → 비공개 [제7호, 경영·영업상 비밀]
- 교과서 채택 학교 현황(맞춤협력과) → 비공개 [제7호, 출판사 영업상 비밀]
- 식중독 의심환자 일일상황보고(평건과) → 비공개 [제5호, 역학조사 진행 중]
- 학생생활규정 점검 결과(중등과) → 비공개 [제5호, 내부검토 과정]
- SEM119 교권보호 상담기록·내부결재문서(생활교육과) → 비공개 [제1·5·6호, 부존재]
- 평생교육시설 등록확인서(제3자 청구, 평건과) → 비공개 [제7호, 법인 영업상 비밀]
- 지능형 CCTV 설치 지원교 선정 결과(통지과) → 비공개 [제5호, 의사결정 과정]
- 학교운동부지도자 비위행위 사안보고서(중등과) → 비공개 [제6호, 개인정보]

### 부분공개 결정 사례 (2025년)
- 개인과외교습자 신고현황(평건과): 성명·학력·전화번호 비공개(제6호), 나머지 공개
- 위험근무수당 내역(재정지원과): 성명 등 개인정보 제외 후 공개(제6호)
- 교습비 조정위원회 회의록(평건과): 발언자 성명·직장 비공개(제5·6호), 교습비 기준단가 공개
- 특수교육대상자 배치 자료(초등과): 배치기준·회의록 비공개(제5·6호), 위원회 구성·결정 건수 공개
- 학교도면 전체(시설과): 배치도·입면도 공개, 평면도·단면도는 열람·시청만 허용(제3호)
- 교권보호위원회 회의록(생활교육과): 학생·위원 개인정보 비공개(제1·6호), 청구인 본인 제출자료 공개
- 특별장학 관련(중등과): 목적·대상·지적사항·조치 비공개(제5·6호), 운영 기준·지침 공개
- 급식실 공사 자료(시설과): 개인정보(성명·주민번호) 제외, 공사대장·계약서 공개(제6호)
- 무등록 학원 신고 처리(평건과): 고발 이첩 일자·사실만 공개, 조사내용·이첩문서 비공개(제6호)
- 공사 관련 서류(시설과): 개인정보 제외 후 부분공개, 하도급 자재·노무비 부존재

## 판정 결과에 따른 출력 형식

### 판정이 "공개"인 경우 — 아래 형식으로 출력
[최종판정: 공개]
[판정요약: 한 줄 요약]

---

## 유사 사례

### 행정안전부 운영안내서(2024) 관련 사례
- Q.XXX (p.XXX): 사례 내용

### 서울특별시 업무매뉴얼(2026) 관련 사례
- p.XXX: 사례 내용

### 연차보고서(2023) 관련 사례
- 사례 내용

---

⚠️ **안내사항**
본 내용은 정보공개 판단을 위한 참고자료입니다. 공개 여부에 대한 최종 결정은 해당 기관 및 담당자의 권한과 책임이며, AI는 관련 법령·사례·자료를 제공하여 판단을 지원하는 역할을 수행합니다. 분쟁 가능성이 있는 사안은 정보공개 전담부서 또는 상급자와 협의하시기 바랍니다.

---

### 판정이 "비공개" 또는 "부분공개"인 경우 — 아래 형식으로 출력
[최종판정: 비공개|부분공개]
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

비공개/부분공개 판단의 구체적 이유를 상세히 설명

### 참고 자료
- 행정안전부 정보공개 운영안내서(2024): Q.XXX (p.XXX) - 관련 내용
- 서울특별시 정보공개 업무매뉴얼(2026): p.XXX - 관련 내용

---

## 3. 관련사례

### 정보공개 연차보고서(2023) 사례
- 관련 사례 내용

### 기타 참고 사례
- 운영안내서/매뉴얼 등의 유사 사례

---

## 4. 참고 판례

관련 판례가 있는 경우 기재, 없으면 "관련 판례 없음" 표시
- 판례명:
- 판결요지:
- 시사점:

---

## 5. 실무 처리 방법

① 첫 번째 처리 단계
② 두 번째 처리 단계
③ 세 번째 처리 단계

---

## 6. 부분공개 검토 (부분공개인 경우만)

- 공개 가능 부분:
- 비공개 대상 부분:
- 처리 방법:

---

⚠️ **안내사항**
본 내용은 정보공개 판단을 위한 참고자료입니다. 공개 여부에 대한 최종 결정은 해당 기관 및 담당자의 권한과 책임이며, AI는 관련 법령·사례·자료를 제공하여 판단을 지원하는 역할을 수행합니다. 분쟁 가능성이 있는 사안은 정보공개 전담부서 또는 상급자와 협의하시기 바랍니다.

한국어로, 실무 담당자가 즉시 활용할 수 있도록 명확하게 작성하세요."""

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

## 서울동부교육지원청 2025년 실제 처리 사례 (처리대장 기반)

### 비공개 사례
- 학교폭력 사안조사 보고서 → 비공개 [제1호·제6호, 학폭법 제21조]
- 학교폭력 신고·심의건수(타 교육청 관할) → 부존재로 비공개
- 그린스마트 공간재구조화 업체 제안서 → 비공개 [제7호, 영업상 비밀]
- 교과서 채택 학교 현황 → 비공개 [제7호, 출판사 영업상 비밀]
- 식중독 의심환자 일일상황보고 → 비공개 [제5호, 역학조사 진행 중]
- 학생생활규정 점검 결과 → 비공개 [제5호, 내부검토 과정; 완료 후 공개 예정 안내]
- SEM119 교권보호 상담기록·내부결재문서 → 비공개 [제1·5·6호]
- 평생교육시설 등록확인서(제3자 청구) → 비공개 [제7호, 법인 영업상 비밀]
- CCTV 설치 지원교 선정 결과 → 비공개 [제5호, 의사결정 과정]
- 학교운동부지도자 비위행위 사안보고서 → 비공개 [제6호, 개인정보]

### 부분공개 사례
- 개인과외교습자 신고현황: 성명·학력·전화번호 비공개(제6호), 교습 과목·지역 공개
- 위험근무수당 내역: 성명 등 개인정보 제외 후 공개(제6호), 학교분 부존재
- 교습비 조정위원회 회의록: 발언자 성명·직장 비공개(제5·6호), 교습비 기준단가는 공개
- 특수교육대상자 배치자료: 배치기준·회의록 비공개(제5·6호), 위원회 구성·결정 건수 공개
- 교권보호위원회 회의록: 학생·위원 개인정보 비공개(제1·6호), 청구인 본인 제출 자료 공개
- 특별장학 관련: 목적·대상·지적사항·조치 비공개(제5·6호), 운영 기준·지침 공개
- 급식실 공사 서류: 개인정보 제외, 공사대장·계약서·설계변경서 공개(제6호)
- 학원 무등록 신고 처리: 고발 이첩 사실만 공개, 조사내용 비공개(제6호)
- 판결문(부동산인도소송): 개인정보 제외 후 부분공개(제6호)

### 공개 사례 중 주요 패턴
- 학교도면: 배치도·입면도 공개, 평면도·단면도는 열람·시청으로만 공개(제3호)
- 개인 근무성적평정점(본인 청구): 공개 (교육공무원 승진규정 제26조)
- 석면해체 공사 현황: 교육청 홈페이지 게시물로 안내(즉시공개 처리)
- 담당자 연락처(홈페이지 공개 정보): 즉시공개 또는 정보소재 안내
- 기록물관리 계획: 공개 (일부 연도 부존재 포함)

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

# ── Groq 클라이언트 ───────────────────────────────────────
@st.cache_resource
def get_client():
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def call_ai(messages_list, system=None, model="llama-3.3-70b-versatile"):
    client = get_client()
    if not client:
        return "⚠️ API 키가 설정되지 않았습니다."
    try:
        full_messages = [{"role": "system", "content": system}] + messages_list
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=2000,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류: {str(e)}"

# ── 2단계 검증 함수 ───────────────────────────────────────
STEP2_VERIFY_PROMPT = """당신은 정보공개 판단 결과를 검토하는 검증 에이전트입니다.
아래 1단계 판단 결과를 확인하고, 문제가 있으면 수정하여 최종 결과를 출력합니다.

## 검토 항목
1. [최종판정: ...] 태그가 정확히 있는가? (공개/비공개/부분공개 중 하나)
2. [판정요약: ...] 태그가 있는가?
3. 비공개/부분공개인 경우 — 1.법적근거 / 2.판단근거 / 3.관련사례 / 4.참고판례 / 5.실무처리방법 섹션이 모두 있는가?
4. 공개인 경우 — 유사사례 섹션과 안내사항이 있는가?
5. 판정 결과가 명확한가? (모호하거나 "추가확인필요"가 부적절하게 사용되었는가?)

## 처리 규칙
- 내용이 충실하고 형식이 맞으면 그대로 출력
- 형식 누락 시 보완하여 출력
- 판정이 불명확하면 법령 근거를 바탕으로 명확히 재판정
- 출력은 수정된 최종 결과만 출력 (검토 과정 설명 불필요)

한국어로 작성하세요."""

def run_keyword_check(keyword, progress_placeholder):
    """2단계 검증: 1단계(판단) → 2단계(검증·보완)"""

    # 1단계: 판단 생성
    progress_placeholder.markdown("🔍 **1단계: 법령·세부기준 검토 중...**")
    prompt1 = (
        f'"{keyword}"에 대해 정보공개 판단을 해주세요. '
        f'반드시 지정된 출력 형식(공개/비공개/부분공개)에 맞게 작성하세요.'
    )
    step1 = call_ai(
        [{"role": "user", "content": prompt1}],
        system=STEP1_SYSTEM_PROMPT,
        model="llama-3.3-70b-versatile"
    )

    # 오류 시 바로 반환
    if step1.startswith("오류:") or step1.startswith("⚠️"):
        progress_placeholder.markdown("❌ **오류 발생**")
        return {"step3": step1}

    # 2단계: 검증·보완
    progress_placeholder.markdown("⚖️ **2단계: 결과 검증 및 보완 중...**")
    prompt2 = f"""다음 1단계 판단 결과를 검토하고 최종 결과를 출력하세요.

키워드: "{keyword}"

1단계 판단 결과:
{step1}"""
    step2 = call_ai(
        [{"role": "user", "content": prompt2}],
        system=STEP2_VERIFY_PROMPT,
        model="llama-3.3-70b-versatile"
    )

    # 2단계도 오류면 1단계 결과 사용
    if step2.startswith("오류:") or step2.startswith("⚠️"):
        progress_placeholder.markdown("✅ **검토 완료!** (1단계 결과 사용)")
        return {"step3": step1}

    progress_placeholder.markdown("✅ **검토 완료!**")
    return {"step3": step2}

# ── 세션 초기화 ──────────────────────────────────────────
if "keyword_result" not in st.session_state:
    st.session_state.keyword_result = None
if "verification_results" not in st.session_state:
    st.session_state.verification_results = None
if "last_keyword" not in st.session_state:
    st.session_state.last_keyword = ""
if "quick_selected" not in st.session_state:
    st.session_state.quick_selected = None

def parse_verdict(text):
    t = text[:150]
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
        "closed":  ("비공개",        "verdict-label-closed"),
        "partial": ("부분공개",       "verdict-label-partial"),
        "open":    ("공개",           "verdict-label-open"),
        "check":   ("추가 확인 필요", "verdict-label-check")
    }
    label, label_class = label_map.get(verdict_type, ("추가 확인 필요", "verdict-label-check"))

    summary = ""
    for line in result_text.split('\n'):
        if "판정요약" in line or "판정 요약" in line:
            summary = line.replace("[판정요약:", "").replace("[판정 요약:", "").replace("]", "").strip()
            break

    st.markdown(f"""
    <div class="rcard">
        <div class="{top_class}">
            <div class="{label_class}">{label} <span class="verified-badge">✓ 검토 완료</span></div>
            <div class="verdict-sub">{summary}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 공개인 경우: 유사사례 + 안내사항만 표시
    if verdict_type == "open":
        sections = parse_final_result_sections(result_text)
        with st.expander("📋 유사 사례 및 안내사항 보기", expanded=True):
            if sections.get("유사사례"):
                st.markdown("""
                <div class="detail-section">
                    <div class="detail-section-title">유사 사례</div>
                    <div class="detail-section-content">{}</div>
                </div>
                """.format(sections["유사사례"].replace("\n", "<br>")), unsafe_allow_html=True)
            st.markdown("""
            <div class="disclaimer-box">
                <strong>⚠️ 안내사항</strong><br>
                본 내용은 정보공개 판단을 위한 <strong>참고자료</strong>입니다.<br>
                공개 여부에 대한 <strong>최종 결정은 해당 기관 및 담당자의 권한과 책임</strong>이며,
                AI는 관련 법령·사례·자료를 제공하여 판단을 지원하는 역할을 수행합니다.<br>
                분쟁 가능성이 있는 사안은 정보공개 전담부서 또는 상급자와 협의하시기 바랍니다.
            </div>
            """, unsafe_allow_html=True)
        return

    # 비공개/부분공개인 경우: 전체 섹션 표시
    with st.expander("📋 상세 검토내용 보기", expanded=True):
        sections = parse_final_result_sections(result_text)

        section_order = [
            ("법적근거",  "1. 법적근거"),
            ("판단근거",  "2. 판단근거"),
            ("관련사례",  "3. 관련사례"),
            ("참고판례",  "4. 참고 판례"),
            ("실무처리",  "5. 실무 처리 방법"),
        ]
        for key, title in section_order:
            content = sections.get(key, "").strip()
            if content:
                st.markdown(f"""
                <div class="detail-section">
                    <div class="detail-section-title">{title}</div>
                    <div class="detail-section-content">{content.replace(chr(10), "<br>")}</div>
                </div>
                """, unsafe_allow_html=True)

        if verdict_type == "partial" and sections.get("부분공개", "").strip():
            st.markdown(f"""
            <div class="detail-section">
                <div class="detail-section-title">6. 부분공개 검토</div>
                <div class="detail-section-content">{sections["부분공개"].replace(chr(10), "<br>")}</div>
            </div>
            """, unsafe_allow_html=True)

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
    sections = {
        "법적근거": "", "판단근거": "", "관련사례": "",
        "참고판례": "", "실무처리": "", "부분공개": "", "유사사례": ""
    }
    current_section = None
    current_content = []

    for line in text.split("\n"):
        ls = line.strip()

        # 공개 판정 시 유사사례 섹션
        if "## 유사 사례" in line or "유사 사례" == ls:
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "유사사례"
            current_content = []
        elif "## 1. 법적근거" in line or ls == "1. 법적근거":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "법적근거"; current_content = []
        elif "## 2. 판단근거" in line or ls == "2. 판단근거":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "판단근거"; current_content = []
        elif "## 3. 관련사례" in line or ls == "3. 관련사례":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "관련사례"; current_content = []
        elif "## 4. 참고 판례" in line or "## 4. 참고판례" in line or ls in ("4. 참고 판례", "4. 참고판례"):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "참고판례"; current_content = []
        elif "## 5. 실무 처리" in line or ls == "5. 실무 처리 방법":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "실무처리"; current_content = []
        elif "## 6. 부분공개" in line or ls == "6. 부분공개 검토 (해당시)":
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)
            current_section = "부분공개"; current_content = []
        elif current_section:
            if ls and not ls.startswith("[최종판정") and not ls.startswith("[판정요약") and "⚠️" not in ls and "안내사항" not in ls:
                current_content.append(line)

    if current_section and current_content:
        sections[current_section] = "\n".join(current_content)

    return sections

# ── 헤더 (참고자료 줄 삭제) ──────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>정보공개 체크봇</h1>
  <p>서울특별시동부교육지원청 정보공개 판단 지원 서비스입니다</p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([3, 2], gap="large")

# 자주 묻는 사례 + 간략 판정 데이터 (오른쪽 패널용)
QUICK_EXAMPLES = [
    {"kw": "학폭위 회의록",    "verdict": "closed",  "label": "비공개",   "basis": "제1호·제6호 (학폭법 제21조)"},
    {"kw": "면접채점표",       "verdict": "closed",  "label": "비공개",   "basis": "제5호 (E5-03)"},
    {"kw": "감사계획서",       "verdict": "closed",  "label": "비공개",   "basis": "제5호 (불시감사·감독 계획)"},
    {"kw": "청사 평면도",      "verdict": "closed",  "label": "비공개",   "basis": "제2호 (E2-06, 보안시설 도면)"},
    {"kw": "청사 입면도",      "verdict": "open",    "label": "공개",     "basis": "외관 도면은 공개 원칙"},
    {"kw": "교사 징계서류",    "verdict": "closed",  "label": "비공개",   "basis": "제1호·제6호 (E1-16, E6-07)"},
    {"kw": "예산안(미확정)",   "verdict": "closed",  "label": "비공개",   "basis": "제5호 (E5-10, 확정 전)"},
    {"kw": "CCTV 영상",        "verdict": "partial", "label": "부분공개", "basis": "제6호 (타인 모자이크 후 공개)"},
    {"kw": "근무성적평정",     "verdict": "closed",  "label": "비공개",   "basis": "제6호 (E6-09)"},
    {"kw": "입찰 예정가격",    "verdict": "closed",  "label": "비공개",   "basis": "제5호 (E5-04)"},
    {"kw": "감사결과보고서",   "verdict": "open",    "label": "공개",     "basis": "감사 완료 후 원칙적 공개"},
    {"kw": "인사위원회 회의록","verdict": "closed",  "label": "비공개",   "basis": "제5호·제6호 (E5-11)"},
    {"kw": "학교폭력 사안조사","verdict": "closed",  "label": "비공개",   "basis": "제1호·제6호 (학폭법 제21조)"},
    {"kw": "교과서 채택현황",  "verdict": "closed",  "label": "비공개",   "basis": "제7호 (출판사 영업상 비밀)"},
    {"kw": "교습비 조정위 회의록","verdict": "partial","label": "부분공개","basis": "제5·6호 (발언자 성명 제외)"},
    {"kw": "석면공사 현황",    "verdict": "open",    "label": "공개",     "basis": "공개 원칙 (홈페이지 안내)"},
    {"kw": "개인 근무평정(본인)","verdict": "open",  "label": "공개",     "basis": "승진규정 제26조 (본인 청구)"},
    {"kw": "소청심사위 회의록","verdict": "closed",  "label": "비공개",   "basis": "제5호·제6호 (E5-10)"},
]

verdict_colors_map = {
    "closed":  {"bg": "#fff1f1", "border": "#E24B4A", "text": "#A32D2D", "badge_bg": "#fde8e8"},
    "partial": {"bg": "#fffbf0", "border": "#EF9F27", "text": "#854F0B", "badge_bg": "#fef3dc"},
    "open":    {"bg": "#f3faf0", "border": "#639922", "text": "#3B6D11", "badge_bg": "#e6f4df"},
}

# ━━━━ 왼쪽: 공개/비공개 검토하기 ━━━━━━━━━━━━━━━━━━━━━━━━
with col_left:
    st.markdown("### 🔍 공개/비공개 검토하기")
    st.markdown('<div class="input-label">키워드 직접 입력</div>', unsafe_allow_html=True)

    keyword_input = st.text_input(
        "키워드 직접 입력",
        placeholder="예: 학폭위 회의록, 면접채점표, 청사 평면도",
        label_visibility="collapsed",
        key="keyword_text_input"
    )

    search_btn = st.button("확인하기", type="primary", use_container_width=True)

    if search_btn:
        kw = keyword_input.strip()
        if kw:
            st.session_state.last_keyword = kw
            progress_placeholder = st.empty()
            with st.spinner(f"'{kw}' 검토 중..."):
                results = run_keyword_check(kw, progress_placeholder)
                st.session_state.verification_results = results
                st.session_state.keyword_result = results["step3"]
                verdict = parse_verdict(results["step3"])
                record_keyword(kw, verdict)
            progress_placeholder.empty()
            st.rerun()
        else:
            st.warning("키워드를 입력해 주세요.")

    if st.session_state.keyword_result:
        result_text = st.session_state.keyword_result
        verdict_type = parse_verdict(result_text)
        render_result_card(result_text, verdict_type)

# ━━━━ 오른쪽: 자주 묻는 사례 패널 ━━━━━━━━━━━━━━━━━━━━━━━
with col_right:
    st.markdown("### 📋 자주 묻는 사례")
    st.markdown('<div style="font-size:0.78rem;color:#888;margin-bottom:10px;">키워드를 클릭하면 판정 결과를 확인할 수 있습니다</div>', unsafe_allow_html=True)

    # 선택된 빠른 예시 상태
    if "quick_selected" not in st.session_state:
        st.session_state.quick_selected = None

    for item in QUICK_EXAMPLES:
        c = verdict_colors_map.get(item["verdict"], verdict_colors_map["open"])
        is_selected = st.session_state.quick_selected == item["kw"]

        # 키워드 버튼
        if st.button(
            item["kw"],
            key=f"quick_{item['kw']}",
            use_container_width=True,
        ):
            if st.session_state.quick_selected == item["kw"]:
                st.session_state.quick_selected = None  # 토글 닫기
            else:
                st.session_state.quick_selected = item["kw"]
            st.rerun()

        # 선택된 항목 → 간략 결과 인라인 표시
        if is_selected:
            st.markdown(f"""
            <div style="
                background:{c['bg']};
                border-left:3px solid {c['border']};
                border-radius:0 6px 6px 0;
                padding:8px 12px;
                margin:-6px 0 6px 0;
                font-size:0.8rem;
                line-height:1.7;
            ">
                <span style="font-weight:600;color:{c['text']}">{item['label']}</span>
                <span style="color:#666;margin-left:8px;font-size:0.75rem">{item['basis']}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="margin-bottom:2px"></div>', unsafe_allow_html=True)

# ── 통계 섹션 ─────────────────────────────────────────────
st.markdown("---")

verdict_labels = {
    "closed": "비공개", "partial": "부분공개",
    "open": "공개", "check": "추가확인필요"
}

with st.expander("📊 검색 통계 보기"):
    stats = load_stats()
    keywords = stats.get("keywords", [])
    total    = len(keywords)

    c1, c2 = st.columns(2)
    c1.metric("공개/비공개 검토", f"{total}회")

    verdict_counter = Counter([k["verdict"] for k in keywords])
    dominant = verdict_counter.most_common(1)
    c2.metric("가장 많은 판정", verdict_labels.get(dominant[0][0], "-") if dominant else "-")

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
            verdict_colors = {
                "closed": "#E24B4A", "partial": "#EF9F27",
                "open": "#639922", "check": "#378ADD"
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
