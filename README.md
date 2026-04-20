# 정보공개 체크봇 — 서울특별시동부교육지원청

정보공개 담당자를 위한 AI 기반 공개/부분공개/비공개 판단 도우미입니다.

## 적용 법령
- 공공기관의 정보공개에 관한 법률 (2023.11.17)
- 정보공개법 시행령 (2026.1.2)
- 정보공개법 시행규칙 (2025.9.19)
- 서울특별시교육청 행정정보 공개 조례 (2025.10.2)
- 서울특별시교육청 비공개대상정보 세부기준 (E1~E8호)
- 2024년 정보공개 운영안내서 (행정안전부)

---

## 배포 방법 (Streamlit Cloud — 무료)

### 1단계: GitHub 업로드
1. https://github.com 접속 → 회원가입
2. 우측 상단 [+] → [New repository]
3. Repository name: `disclosure-chatbot` 입력 → [Create repository]
4. 이 폴더의 파일들을 모두 업로드
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `.gitignore`
   - ⚠️ `.streamlit/secrets.toml` 은 올리지 마세요 (API 키 노출 위험)

### 2단계: Streamlit Cloud 배포
1. https://share.streamlit.io 접속 → Google/GitHub 계정으로 로그인
2. [New app] 클릭
3. Repository: `disclosure-chatbot` 선택
4. Main file path: `app.py` 입력
5. [Advanced settings] → Secrets 탭에 아래 내용 입력:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
6. [Deploy!] 클릭

### 3단계: URL 공유
배포 완료 후 생성된 URL (예: `https://disclosure-chatbot.streamlit.app`)을 담당자들에게 공유하면 됩니다.

---

## Anthropic API 키 발급 방법
1. https://console.anthropic.com 접속
2. 회원가입 후 로그인
3. 좌측 메뉴 [API Keys] → [Create Key]
4. 생성된 키(`sk-ant-...`)를 복사하여 Streamlit Secrets에 입력

---

## 파일 구조
```
disclosure-chatbot/
├── app.py                    ← 메인 앱 (이것만 있으면 됨)
├── requirements.txt          ← 필요한 패키지 목록
├── .gitignore                ← GitHub 업로드 제외 파일 목록
└── .streamlit/
    ├── config.toml           ← 테마 설정
    └── secrets.toml          ← API 키 (GitHub에 올리지 말 것!)
```
