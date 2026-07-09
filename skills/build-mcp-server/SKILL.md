---
name: build-mcp-server
description: Interactively design, generate, and register a FastMCP MCP server through a guided 6-phase wizard that mirrors the MCP design worksheet (problem → tools → I/O → guardrails → rehearse/register). Use when the user wants to build an MCP server, create MCP tools/resources/prompts, scaffold a FastMCP server.py, connect a custom server to Claude Code or Claude Desktop, or says "MCP 서버 만들기", "MCP 만들어줘", "FastMCP".
disable-model-invocation: true
argument-hint: "[server-name]"
allowed-tools: AskUserQuestion, Read, Write, Edit, Bash
---

# build-mcp-server — 대화형 MCP 서버 빌더

강의 "MCP로 AI 효용성 높이기(6주차)"의 커리큘럼을 그대로 위저드로 옮긴 스킬이다.
사용자가 **모든 설계 결정을 직접 고르면**, 그 결정을 `ServerSpec` 객체에 누적하고,
마지막에 FastMCP `server.py`를 **생성**하고 Claude에 **등록**하고 **검증**한다.

> 사용자에게 보이는 모든 질문·설명·개념 카드는 **한국어**로 낸다.
> (코드 주석과 식별자는 영어 허용.) 이 파일의 지시는 Claude가 읽는 것이지 사용자에게 보이지 않는다.

## 절대 규칙 (footgun 방지)
1. **미리보기 승인 게이트 전에는 어떤 파일도 쓰지 않는다.** 위저드는 순수하게 결정만 모은다.
2. 매 단계 결정은 `AskUserQuestion`으로 받는다. 선택지는 항상 2~4개 + "직접 입력(Other)"이 자동 제공됨.
3. 기본값은 항상 **최소 권한·안전한 쪽**으로 pre-select 한다 (Phase 4, `references/security-guardrails.md`).
4. 등록 시 **절대경로**를 강제한다. 상대경로는 조용히 실패하는 1순위 버그다.
5. stdio 서버는 **stdout에 print 금지** — 생성 코드는 로그를 stderr로만 보낸다.
6. 비밀키는 **하드코딩 선택지를 제공하지 않는다**. `.env` + `.gitignore` + 로드 실패 예외만.

## Checklist (진행하며 하나씩 체크)
- [ ] Phase 0  온보딩: `teachMode` + `userLevel` 설정, CH1/CH2 개념 카드
- [ ] Phase 1  문제정의: 작업 유형, 적합성 점검(CH3), `serverName` + `archetype`
- [ ] Phase 2  도구 쪼개기: Tools/Resources/Prompts, 도구 분해, 순서 강제 여부
- [ ] Phase 3  입출력 설계: 도구별 입력 + 반환 형태 + docstring
- [ ] Phase 4  가드레일: 권한·비밀키·검증·승인 게이트 (CH4)
- [ ] Phase 5  리허설·등록: transport, Inspector 리허설, 등록 대상
- [ ] 미리보기 게이트 → 생성 → 등록 → 검증

## ServerSpec (단계마다 채워지는 상태 객체)
위저드 내내 이 JSON을 머릿속(그리고 스크래치패드 파일)에 누적한다. 각 질문이 어느 필드를 채우는지는
`references/question-flow.md`에 표로 있다. 스키마 검증은 `scripts/validate_spec.py`가 한다.

```json
{
  "meta":    { "serverName": "", "teachMode": "teach|fast|mixed",
               "userLevel": "first|some|comfortable",
               "problem": "", "archetype": "data-lookup|automation|integration|analysis-workflow" },
  "tools":   [ { "name": "", "job": "", "docstring": "", "orderTag": null,
                 "sideEffecting": false,
                 "params": [ { "name": "", "type": "str", "desc": "" } ],
                 "returnShape": "result_next_step|number_interpretation|string|status" } ],
  "resources": [ { "name": "", "uri": "", "job": "" } ],
  "prompts":   [ { "name": "", "job": "" } ],
  "ordered":  false,
  "security": { "privilege": "readonly-dir|select-db|scoped-key|write",
                "secrets": { "mode": "env|none", "keys": [] },
                "validation": [],
                "approvalGate": true },
  "runtime":  { "transport": "stdio|sse|streamable-http", "rehearse": true,
                "register": "code|desktop|both|none",
                "projectDir": "" }
}
```

## 오케스트레이션 절차

**시작 시**
- `${CLAUDE_SKILL_DIR}` = 이 스킬 폴더. 참조 파일은 필요할 때만 Read (progressive disclosure).
- `argument-hint`로 서버 이름이 넘어왔으면 `meta.serverName`에 미리 채운다.
- `python "${CLAUDE_SKILL_DIR}/scripts/detect_clients.py"`를 실행해 어떤 클라이언트(Claude Code/Desktop)와
  `uv`·python 버전이 있는지 JSON으로 받는다. 결과를 `runtime`·등록 선택지에 반영한다.
- `runtime.projectDir`는 현재 작업 디렉토리로 둔다 (생성 파일이 여기 떨어진다).

**각 Phase 공통**
1. `teachMode ∈ {teach, mixed}`이면, 그 Phase에 해당하는 `references/teach-ins.md` 카드를 Read 해서
   **3~4줄로** 먼저 보여준다. `fast`면 한 줄 "왜? ▸ …"로 압축.
2. `references/question-flow.md`에서 그 Phase의 질문 정의(선택지·기본값·분기 규칙)를 확인하고
   `AskUserQuestion`으로 낸다. 답을 `ServerSpec`에 기록한다.
3. Phase가 끝나면 스크래치패드에 `<serverName>.spec.json`으로 저장(재개 가능).

**Phase별 요점** (전체 질문 문안은 `references/question-flow.md`)
- **Phase 0 온보딩**: `Q0.1 Pace`(가르쳐줘/빠르게/혼합) → `teachMode`; `Q0.2 경험`(처음/한두번/익숙) → `userLevel`.
  teach면 CH1(N×M→M+N, Model·Context·Protocol) + CH2(레스토랑 비유) 카드.
- **Phase 1 문제정의**: `Q1.1 작업유형` → `archetype`; 부적합 냄새(실시간 스트리밍/장기 상태/대용량 연산)면
  `Q1.2 적합성 점검`; `Q1.3 이름` → 슬러그화 → `serverName`.
- **Phase 2 도구 쪼개기**: CH2 "서버 3요소" 카드. `Q2.1 무엇을 제공`(Tools/Resources/Prompts, multi);
  `Q2.2 도구 분해`("하나의 도구=하나의 일"); `Q2.3 순서 강제` → `ordered`.
- **Phase 3 입출력 설계** (도구마다 반복): "타입 힌트=주문서 양식, docstring=설명서" 카드.
  `Q3.1 입력`(타입 있는 파라미터); `Q3.2 반환 형태`(next_step 포함 / 숫자+해석 / 문자열 / 상태);
  `Q3.3 docstring`(언제 호출해야 하는지 한 문장). `ordered`면 `[N단계 - 필수 선행]`을 자동 프리픽스해 확인받는다.
  설계 원칙은 `references/design-principles.md` 참고 — 반환에 `next_step`, 숫자엔 맥락(맨 p값 금지).
- **Phase 4 가드레일**: CH4 카드. `Q4.1 권한`(최소권한 pre-select); `Q4.2 비밀키`(.env 강제, API 쓸 때만);
  `Q4.3 입력검증`(multi); `Q4.4 승인 게이트`(위험 작업 전 사용자 승인, 기본 예).
  매핑 상세는 `references/security-guardrails.md`.
- **Phase 5 리허설·등록**: CH5 카드. `Q5.1 transport`(stdio 기본; sse/streamable-http는 `comfortable`만 노출);
  `Q5.2 Inspector 리허설`(기본 예, 처음 사용자에겐 건너뛰기 비권장);
  `Q5.3 등록 대상`(`references/registration.md`의 탐지 결과 기반).

**미리보기 승인 게이트 (필수)**
1. `python "${CLAUDE_SKILL_DIR}/scripts/validate_spec.py" <spec.json>`으로 스키마 검증. 실패하면 해당 Phase로 되돌아간다.
2. 사용자에게 **(a)** 평문 요약, **(b)** 실제 `server.py` 렌더 결과, **(c)** 등록 설정 JSON을 보여준다.
   - 렌더 미리보기: `python "${CLAUDE_SKILL_DIR}/scripts/render_server.py" <spec.json> --stdout` (파일은 아직 안 씀).
3. `AskUserQuestion`으로 확인: `이대로 생성` / `수정할 게 있어`(→ 어느 결정을 고칠지 점프 메뉴) / `취소`.

**생성 → 등록 → 검증** (게이트 승인 후에만)
1. `python "${CLAUDE_SKILL_DIR}/scripts/render_server.py" <spec.json> --out <projectDir>`
   → `<serverName>.py`, `pyproject.toml`, `.env.example`, `.gitignore` 생성.
2. 의존성: `uv init`이 아직이면 안내하고, `uv add "mcp[cli]"` 실행(또는 사용자가 pip 원하면 `pip install "mcp[cli]"`).
   Python은 3.12로 핀(`uv venv --python 3.12`) — 3.14는 휠 호환 리스크.
3. 등록 (`references/registration.md`대로):
   - `register ∈ {code, both}`: `claude mcp add-json <serverName> --scope user '<json>'`
     (`command:"uv", args:["run","--directory","<projectDir 절대경로>","python","<serverName>.py"]`, `env`엔 키 자리만).
   - `register ∈ {desktop, both}`: `python "${CLAUDE_SKILL_DIR}/scripts/merge_desktop_config.py"`로
     `claude_desktop_config.json`에 안전 병합(없으면 스니펫만 생성). **완전 종료 후 재시작** 안내.
4. 검증:
   - `rehearse`면 Inspector 리허설 명령을 실제로 실행하거나 사용자에게 실행을 안내:
     `npx @modelcontextprotocol/inspector uv --directory <projectDir> run <serverName>.py`
   - Claude Code면 `claude mcp get <serverName>`로 등록 확인, 그리고 `/mcp`로 로드 확인하도록 안내.
   - 테스트 프롬프트 2~3개 제시(도구를 실제로 호출하게).

**"수정" 처리**: 언제든 사용자가 되돌리고 싶어 하면, 이전 결정들의 점프 메뉴를 내고, 고친 필드에
의존하는 하위 질문만 다시 낸다. `ServerSpec`은 스크래치패드 파일에서 이어서 로드한다.

## 완성 예시로 감 잡기
막히면 `assets/stat-advisor.example.json`(강의의 STAT TEST ADVISOR 사례:
`inspect_data → check_assumptions → run_test`, 순서 강제·읽기 전용)을 참고 스펙으로 보여주고,
사용자 작업에 맞게 변형하도록 유도한다.
