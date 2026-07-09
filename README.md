# ClaudeCode-Guide-Skills

Claude Code를 확장하는 **스킬(Skills)·훅(Hooks) 모음**입니다.
강의 "MCP로 AI 효용성 높이기(6주차)"의 내용을 실제로 쓸 수 있는 도구로 옮기는 것을 목표로,
개념을 짚어가며 **대화형으로** 결과물을 만들어 주는 확장들을 카테고리별로 모읍니다.

> A collection of Claude Code extensions (skills, hooks, …). Each skill is interactive and
> teaches while it builds. Korean-first UX.

---

## 📁 저장소 구조 (계층형)

카테고리 폴더 아래에 개별 확장이 들어갑니다. 새 확장은 알맞은 카테고리 하위에 추가하세요.

```
ClaudeCode-Guide-Skills/
├── README.md                  # (이 파일) 저장소 개요 · 카탈로그 · 설치법
├── LICENSE                    # MIT
├── skills/                    # 에이전트 스킬 (Agent Skills)
│   ├── README.md
│   └── build-mcp-server/      # 대화형 MCP 서버 빌더 위저드
├── hooks/                     # 훅 설정 모음 (예정)
│   └── README.md
└── …                          # 앞으로: commands/, agents/, mcp/ 등 카테고리 확장
```

## 🧩 스킬 카탈로그

| 스킬 | 설명 | 상태 |
|---|---|---|
| [`build-mcp-server`](skills/build-mcp-server/) | 개념부터 등록까지 6단계로 짚어가며 **FastMCP MCP 서버를 대화형으로 설계·생성·등록**하는 위저드 | ✅ 사용 가능 |

## 🚀 설치 (스킬)

Claude Code 스킬은 `~/.claude/skills/<이름>/` (사용자 전역) 또는
프로젝트의 `.claude/skills/<이름>/` (프로젝트 한정)에 두면 자동으로 인식됩니다.

**전역 설치** (모든 프로젝트에서 사용):
```bash
# 이 저장소를 클론한 뒤, 원하는 스킬 폴더를 통째로 복사
git clone https://github.com/HwaminCLaude/ClaudeCode-Guide-Skills.git
cp -r ClaudeCode-Guide-Skills/skills/build-mcp-server ~/.claude/skills/
```

Windows PowerShell:
```powershell
git clone https://github.com/HwaminCLaude/ClaudeCode-Guide-Skills.git
Copy-Item -Recurse ClaudeCode-Guide-Skills\skills\build-mcp-server $env:USERPROFILE\.claude\skills\
```

설치 후 Claude Code를 새로 시작하면 `/build-mcp-server` 처럼 슬래시 명령으로 실행할 수 있습니다.

## 🗺️ 로드맵

- [x] `skills/build-mcp-server` — 대화형 MCP 서버 빌더
- [ ] `hooks/` — 훅 설정 예제 모음 (Stop/PreToolUse/PostToolUse 등)
- [ ] `skills/` — 강의 후속 주제 스킬 추가
- [ ] `commands/`, `agents/` 등 카테고리 확장

## 🤝 기여 / 새 확장 추가하기

1. 알맞은 카테고리 폴더(`skills/`, `hooks/`, …) 하위에 새 폴더를 만든다.
2. 스킬이면 `SKILL.md`(frontmatter 포함)를 두고, 필요한 `references/`·`scripts/`·`templates/`·`assets/`를 함께 둔다.
3. 해당 카테고리의 `README.md`와 이 파일의 카탈로그 표에 한 줄 추가한다.

## 📄 라이선스

MIT © 2026 HwaminCLaude — [LICENSE](LICENSE) 참고.
