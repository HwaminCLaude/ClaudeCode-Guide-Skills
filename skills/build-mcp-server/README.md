# build-mcp-server 🛠️

**개념부터 등록까지, 대화하면서 MCP 서버를 만들어 주는 Claude Code 스킬.**

강의 "MCP로 AI 효용성 높이기(6주차)"의 5단계 설계 워크시트를 그대로 위저드로 옮겼습니다.
사용자가 **모든 설계 결정을 직접 고르면**, 그 결정을 `ServerSpec`으로 모아
FastMCP `server.py`를 생성하고 Claude에 등록·검증합니다.

## 실행

```
/build-mcp-server
# 서버 이름을 미리 정하려면:
/build-mcp-server stat-advisor
```

## 6단계 흐름 (강의 챕터 ↔ 단계)

| 단계 | 강의 근거 | 사용자가 정하는 것 |
|---|---|---|
| 0 온보딩 | CH1·CH2 개념 | 가르치며/빠르게, 경험 수준 |
| 1 문제정의 | CH3 강점/한계 | 어떤 반복·오류 작업, 서버 이름 |
| 2 도구 쪼개기 | CH2 서버 3요소 | Tools/Resources/Prompts, 순서 강제 여부 |
| 3 입출력 설계 | 설계원칙 ②③ | 입력 타입, 반환 형태, docstring |
| 4 가드레일 | CH4 보안 | 권한·비밀키·검증·승인 게이트 |
| 5 리허설·등록 | CH5 실습 | transport, Inspector, 등록 대상 |
| 미리보기 → 생성 → 등록 → 검증 | 따라하기 1~3 | 요약+코드 확인 후 승인 |

## 강의 설계 원칙이 코드로 박힘

- **순서 강제** → docstring에 `[N단계 - 필수 선행]` 자동 삽입
- **응답에 `next_step`** → AI가 다음 도구를 헤매지 않게
- **숫자엔 맥락** → 효과크기·표본수·해석 포함(맨 p값 반환 거부)
- **보안(CH4)** → `.env` fail-fast 비밀키, 최소 권한 기본값, 입력 검증, 위험 작업 승인 게이트, stdio→stderr 로깅

## 구성

```
SKILL.md                 # 6단계 오케스트레이션 + ServerSpec 계약
references/              # 질문 카탈로그 · 개념 카드 · 설계원칙 · 보안 · 등록법
templates/              # server.py / pyproject / env / gitignore / desktop 스니펫
scripts/                # detect_clients · validate_spec · render_server · merge_desktop_config
assets/                 # STAT ADVISOR 완성 예시 스펙
```

## 요구 사항

- **uv** (권장) 또는 pip — 생성 서버는 Python **3.12**로 핀(`uv venv --python 3.12`)하고 `mcp[cli]` 설치
- **node/npx** — MCP Inspector 리허설용 (`npx @modelcontextprotocol/inspector`)
- 등록 대상: **Claude Code**(`claude mcp add-json`) 기본. Claude Desktop이 있으면 `claude_desktop_config.json`에도 안전 병합

## 검증됨

`assets/stat-advisor.example.json`(강의의 통계검정 자문 서버: `inspect_data → check_assumptions → run_test`)으로
파이프라인 전체를 확인: 스펙 검증 → 코드 렌더 → `py_compile` → **py3.12 venv에서 실제 실행**(stdio 핸드셰이크,
도구 4개 등록, 타입힌트→스키마 자동 생성, 도구 호출·검증 경로 동작).

## 생성 코드에 대해

생성되는 `server.py`는 **인터페이스가 완성된 스캐폴드**입니다 — 도구 시그니처·스키마·docstring·반환 구조·보안
가드레일은 바로 실행/연결되지만, 각 도구의 **실제 로직은 `TODO` 자리**로 둡니다(위저드는 "행동 설계"를 하고
알맹이 구현은 사용자 몫 — 강의의 설계 철학 그대로).
