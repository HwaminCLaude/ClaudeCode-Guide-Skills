# 등록 & 검증 — 클라이언트 탐지부터 붙이기까지

이 환경: **Claude Desktop 미설치, Claude Code 설치됨.** 그래서 기본 등록 대상은 Claude Code이고,
Desktop 설정은 스니펫으로 항상 남긴다(설치 후 사용).

---

## 1. 클라이언트 탐지
```
python "${CLAUDE_SKILL_DIR}/scripts/detect_clients.py"
```
→ JSON: `{ "code": bool, "desktop": bool, "desktopConfigPath": "...", "uvPath": "...", "python": "..." }`
- Claude Code: `claude --version` 성공 또는 `~/.claude.json` 존재.
- Claude Desktop: `%APPDATA%\Claude\` 존재 (없으면 MSIX 대체 경로 `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\`).
탐지 결과로 Q5.3(등록 대상) 선택지를 조정한다.

## 2. Claude Code에 등록 (기본, 권장)
`~/.claude.json`을 직접 손대지 말고 **CLI를 쓴다** (스키마가 안전하게 관리됨).

```
claude mcp add-json <serverName> --scope user "<json한줄>"
```
`<json한줄>` 예 (Windows, uv 실행, 절대경로):
```json
{"type":"stdio","command":"uv","args":["run","--directory","C:\\Users\\HOSEO\\Desktop\\claude","python","<serverName>.py"],"env":{"MY_API_KEY":"..."}}
```
- `--scope user` = 모든 프로젝트에서 사용 가능. 프로젝트 전용이면 스코프 생략(기본 local) 또는 `--scope project`(`.mcp.json` 생성).
- **절대경로 강제.** 상대경로는 조용히 실패한다(1순위 버그).
- `uv run --directory <절대경로>`를 쓰면 cwd와 무관하게 프로젝트 venv/의존성이 잡힌다.
- `uv`가 PATH에서 안 잡히면 `where uv`의 절대경로를 `command`에 넣는다.
- 비밀키: 값을 config에 박지 말고, 프로젝트 `.mcp.json`이면 `"env":{"MY_API_KEY":"${MY_API_KEY}"}` 확장을 쓴다.

확인:
```
claude mcp get <serverName>
claude mcp list
```
그리고 새 세션에서 `/mcp`로 서버 로드 여부 확인.

## 3. Claude Desktop 설정 (스니펫은 항상 생성)
스키마:
```json
{ "mcpServers": { "<serverName>": {
    "command": "uv",
    "args": ["run", "--directory", "C:\\Users\\HOSEO\\Desktop\\claude", "python", "<serverName>.py"],
    "env": { "MY_API_KEY": "..." }
} } }
```
- 파일 위치(Windows): `%APPDATA%\Claude\claude_desktop_config.json`. (mac: `~/Library/Application Support/Claude/…`)
- **JSON에서 백슬래시는 두 번**(`C:\\Users\\…`). 절대경로만.
- 설치돼 있으면 아래 안전 병합, 없으면 프로젝트 폴더에 `claude_desktop_config.snippet.json`으로 남긴다.

안전 병합:
```
python "${CLAUDE_SKILL_DIR}/scripts/merge_desktop_config.py" --server <serverName> --spec <spec.json> --config "<desktopConfigPath>"
```
원칙(스크립트가 보장): 없으면 생성 / 파싱 실패 시 중단(덮어쓰지 않음) / 쓰기 전 타임스탬프 `.bak-*` 백업 /
그 서버 키만 병합(기존 서버 보존) / 재직렬화 후 재파싱 검증 / 동일하면 쓰지 않음(idempotent) / 원자적 교체.

병합/생성 후: **완전 종료 후 재시작** 안내(창만 닫는 것 아님).
서버가 조용히 안 뜨면 MSIX 대체 경로 확인, `${APPDATA}`가 안 풀리면 그 서버 `env`에
`"APPDATA":"C:\\Users\\HOSEO\\AppData\\Roaming\\"`를 추가.

## 4. MCP Inspector 리허설 (등록 전 검증)
```
npx @modelcontextprotocol/inspector uv --directory <projectDir> run <serverName>.py
```
- 브라우저 UI(기본 :6274, 프록시 :6277)에서 Tools/Resources/Prompts 탭 확인,
  도구를 폼 인자로 직접 호출해 스키마·반환을 눈으로 검증.
- pip를 썼다면: `npx @modelcontextprotocol/inspector python <serverName>.py`.

## 5. 테스트 프롬프트 (등록 후 사용자에게 제시)
- "어떤 MCP 서버에 접근 가능해?" → 목록에 `<serverName>`이 보이면 성공.
- "`<tool>` 을(를) …로 호출해줘" → 실제 도구 호출/반환 확인.
- analysis-workflow면 순서대로 유도: 1단계 도구부터 호출하는지 확인.
