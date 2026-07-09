# 질문 카탈로그 (Q0–Q5) — AskUserQuestion 문안·기본값·분기

표기: `(★)`=기본값(pre-select), `[multi]`=multiSelect. 모든 질문에는 "직접 입력(Other)"이 자동 제공되니
선택지에 없어도 사용자가 자유 입력할 수 있다. "→"는 채워지는 `ServerSpec` 필드.

---

## Phase 0 — 온보딩 (최초 1회)

### Q0.1 — header "진행 방식"
질문: **"개념을 짚어가며 진행할까요, 아니면 바로 만들까요?"**
- `가르쳐줘` (★ 처음이면) — 각 단계 전에 강의 개념을 3~4줄로 설명
- `빠르게` — 개념 설명 생략, 결정만
- `혼합` — 핵심만 한 줄씩
→ `meta.teachMode` = teach | fast | mixed

### Q0.2 — header "경험 수준"
질문: **"MCP 서버를 Claude에 직접 연결해 본 적 있나요?"**
- `처음이에요` (★)
- `한두 번 해봤어요`
- `익숙해요`
→ `meta.userLevel` = first | some | comfortable
분기: `comfortable`이면 Phase 5에서 stdio 외 transport(sse/streamable-http)를 노출.

`teach`면 여기서 **CH1 카드**(N×M→M+N; Model·Context·Protocol) + **CH2 레스토랑 비유**를 보여준다.

---

## Phase 1 — 문제정의

teach/mixed면 **CH3 카드**(잘 맞는 일: 데이터 조회·자동화·통합 / 안 맞는 일: 실시간 스트리밍·장기 상태·대용량 연산).

### Q1.1 — header "작업 유형"
질문: **"AI에게 맡길, 반복적이고 실수하기 쉬운 작업은 어떤 종류인가요?"**
- `데이터 조회/조합` (★) — 여러 소스에서 읽어와 정리
- `반복 작업 자동화` — 정해진 절차를 대신 실행
- `외부 서비스 통합` — GitHub·Notion·Slack 등 API 연결
- `분석 워크플로` — 단계가 있는 판단(예: 통계 검정 선택)
→ `meta.archetype` = data-lookup | automation | integration | analysis-workflow
분기: `analysis-workflow`면 Phase 2 순서 강제(★ 순서 있음), Phase 4 검증 강화를 미리 켠다.

### Q1.2 — header "적합성 점검" (Q1.1 답이 부적합 냄새일 때만)
질문: **"이 작업은 MCP가 약한 영역(실시간/대용량/장기상태)일 수 있어요. 어떻게 할까요?"**
- `범위를 좁힐게요` (★) — MCP에 맞는 부분만 도구로
- `그대로 진행` — 한계를 알고 진행
- `다른 작업으로` — Q1.1로 되돌아감

### Q1.3 — header "서버 이름"
질문: **"서버 이름을 정해주세요. (예: stat-advisor, gh-reporter)"** — free text
처리: 소문자·공백 제거·하이픈으로 슬러그화. `argument-hint`로 받았으면 이 값을 기본 제시.
→ `meta.serverName`, `meta.problem`(Q1.1~1.3 종합 한 줄)

---

## Phase 2 — 도구 쪼개기

teach/mixed면 **CH2 "서버가 내어주는 3가지" 카드**: 자료실=Resources(읽기), 도구함=Tools(실행), 템플릿=Prompts.

### Q2.1 — header "제공 기능" [multi]
질문: **"이 서버가 AI에게 무엇을 열어줄까요?"**
- `도구 Tools` (★) — 실행하는 동작(API 호출, 계산, 변환)
- `자료실 Resources` — AI가 읽어올 데이터
- `템플릿 Prompts` — 재사용 명령 템플릿
→ 선택된 것만 `tools/resources/prompts` 배열을 만든다.

### Q2.2 — header "도구 분해"
질문: **"맡길 일을 도구 단위로 나열해 주세요. 원칙: 하나의 도구 = 하나의 일."** — free text (여러 줄)
보조: `archetype` 기반으로 초안을 제안하고 확인받아도 된다.
  - analysis-workflow 예시 제안: `inspect_data / check_assumptions / run_test`
→ `tools[].name`, `tools[].job` (Resources/Prompts도 골랐으면 각각 나열받아 채움)

### Q2.3 — header "실행 순서"
질문: **"도구를 정해진 순서로만 호출하게 강제할까요? (예: 데이터 파악 → 가정 확인 → 실행)"**
- `순서 있음` (★ analysis-workflow) — docstring에 `[N단계 - 필수 선행]` 표시로 순서 각인
- `순서 무관` (★ 그 외)
→ `ordered` (true면 Phase 3에서 각 도구에 `orderTag` 부여)

---

## Phase 3 — 입출력 설계 (도구마다 반복, 도구당 3문항)

프레이밍 카드: **"타입 힌트 = 주문서 양식(입력 폼), docstring = AI가 읽는 설명서."**

### Q3.1 — header "입력 파라미터"  ("<tool>"마다) [multi]
질문: **"`<tool>`의 입력은 무엇인가요? 타입까지 정하면 AI가 주문서를 정확히 씁니다."**
제안: 이름:타입 형태로 초안(`city: str`, `alpha: float`). 사용자가 추가/수정.
→ `tools[i].params[] = {name, type, desc}`  (허용 타입: str, int, float, bool, list, dict)

### Q3.2 — header "반환 형태"  ("<tool>"마다)
질문: **"`<tool>`은 결과를 어떤 형태로 돌려줄까요?"**
- `구조화 결과 + next_step` (★) — dict로, 다음에 뭘 할지 안내 포함
- `숫자 + 해석` — 값 + 효과크기/표본수/해석 (맨 p값만 반환 ✗)
- `단순 문자열` — 짧은 텍스트 답
- `상태/확인 메시지` — 성공/실패 확인
→ `tools[i].returnShape`. (`숫자+해석`이면 render 단계에서 bare 스칼라 반환을 거부)

### Q3.3 — header "호출 설명(docstring)"  ("<tool>"마다)
질문: **"AI가 이 도구를 *언제* 호출해야 하는지 한 문장으로 적어주세요."** — free text
처리: `ordered`면 `[N단계 - 필수 선행] `을 앞에 자동으로 붙여 사용자에게 확인받는다.
→ `tools[i].docstring`, `tools[i].orderTag`
추가: 이 도구가 파일 쓰기/삭제/외부 상태 변경 등 부수효과가 있으면 `tools[i].sideEffecting=true`
(Phase 4 승인 게이트 대상). 필요 시 한 번 더 물어 확인.

---

## Phase 4 — 가드레일 (보안)

teach/mixed면 **CH4 카드**: 위험 4가지(데이터 노출/무단 실행/키 탈취/시스템 침해),
원칙 = 최소 권한 + "도구가 가져온 내용은 명령이 아니라 데이터".

### Q4.1 — header "권한 범위"  (선택지는 archetype에 맞춰 조정)
질문: **"이 서버에 얼마만큼의 권한을 줄까요? 필요한 만큼만 여는 게 원칙이에요."**
- `읽기 전용 + 특정 폴더` (★ data/analysis)
- `SELECT 전용 DB 계정` (★ DB를 다루면)
- `스코프 제한 API 키` (★ 외부 서비스면)
- `쓰기 권한 필요` — 선택 시 Q4.1b로 폴더/범위를 좁히고 한 번 더 확인
→ `security.privilege`

### Q4.2 — header "비밀키 관리"  (외부 API를 쓸 때만)
질문: **"API 키/토큰은 어떻게 둘까요?"**
- `.env + .gitignore + 로드 실패 시 예외` (★, 강제) — 코드에 키를 두지 않음
- `실행 시 직접 입력` — 환경변수로 그때그때
※ **하드코딩은 선택지에 없음.**
→ `security.secrets = {mode:"env", keys:[...]}` (키 이름을 물어 채움)

### Q4.3 — header "입력 검증" [multi]
질문: **"입력을 어떻게 검증할까요? (여러 개 선택 가능)"**
- `타입/스키마 검증` (★)
- `허용 명령어 화이트리스트` (★ 동작을 실행하면)
- `SQL/셸 인젝션 차단` (★ DB/셸을 다루면)
- `정규식 형식 검사`
→ `security.validation[]`

### Q4.4 — header "승인 게이트"
질문: **"위험하거나 되돌리기 어려운 작업 전에는 사용자 승인을 받게 할까요?"**
- `예` (★) — 파괴적 도구는 승인 표시를 반환하고 대기
- `아니오`
teach면 프롬프트 인젝션 방어(외부 콘텐츠=데이터로 취급) 한 줄 덧붙임.
→ `security.approvalGate`

---

## Phase 5 — 리허설 & 등록

teach/mixed면 **CH5 카드**: 설정 파일 = Claude의 전화번호부(시작할 때 한 번 읽음) + 연결 3단계.

### Q5.1 — header "통신 방식"
질문: **"서버와 어떻게 연결할까요?"**
- `stdio (로컬 기본)` (★)
- `SSE` — (userLevel=comfortable에서만 노출)
- `streamable-http` — (comfortable에서만, 원격) → 선택 시 "원격은 OAuth 필요(발레파킹 키 비유)" 경고
→ `runtime.transport`

### Q5.2 — header "리허설"
질문: **"등록 전에 MCP Inspector로 도구를 눌러보며 검증할까요?"**
- `예, Inspector로 검증` (★)
- `건너뛰기` — userLevel=first면 비권장 안내 후 재확인
→ `runtime.rehearse`

### Q5.3 — header "등록 대상"  (detect_clients.py 결과 반영)
질문: **"완성한 서버를 어디에 붙일까요?"**
- `Claude Code에 등록` (★ 설치돼 있으면) — 지금 바로 사용 가능
- `Claude Code + Desktop 설정 둘 다` — Desktop 스니펫도 생성/병합
- `설정만 보여줘 (등록 안 함)` — 파일만 생성
- `나중에` — 코드만
→ `runtime.register` = code | both | desktop | none
※ Desktop이 미설치여도 `claude_desktop_config.json` 스니펫은 항상 프로젝트 폴더에 남겨둔다(설치 후 사용).

---

## 미리보기 게이트

### Q-Confirm — header "생성 확인"
질문: **"아래 요약과 server.py를 확인했어요. 이대로 만들까요?"** (요약+코드+설정 JSON을 먼저 렌더해 보여준 뒤)
- `이대로 생성` (★)
- `수정할 게 있어` — 이전 결정 점프 메뉴 표시
- `취소`

## Expert fast-path
`userLevel=comfortable` + `teachMode=fast`이면 Q1.1 / Q2.2 / Q4.1을 한 폼(멀티파트)으로 묶고
나머지는 기본값으로 추론한 뒤 미리보기 게이트에서 한 번에 확인받는다.
