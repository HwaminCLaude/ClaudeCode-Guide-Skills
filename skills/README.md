# skills/ — 에이전트 스킬 모음

Claude Code [Agent Skills](https://code.claude.com/docs/en/skills)를 모아둔 카테고리입니다.
각 스킬은 하위 폴더 하나로, 최소한 `SKILL.md`(YAML frontmatter + 지시문)를 포함합니다.

## 목록

| 스킬 | 한 줄 설명 |
|---|---|
| [`build-mcp-server`](build-mcp-server/) | 개념부터 등록까지 6단계로 짚어가며 FastMCP MCP 서버를 대화형으로 설계·생성·등록하는 위저드 |

## 스킬 폴더의 표준 구성

```
<skill-name>/
├── SKILL.md          # 필수. frontmatter(name, description, …) + 오케스트레이션 지시
├── references/       # 선택. 필요할 때만 읽는 참고 문서(progressive disclosure)
├── scripts/          # 선택. 실행 로직(파이썬/노드 등). 무거운 로직은 여기에
├── templates/        # 선택. 코드/설정 템플릿
└── assets/           # 선택. 예시 데이터 등
```

## 설치

```bash
cp -r skills/<skill-name> ~/.claude/skills/          # 전역
# 또는 프로젝트 한정
cp -r skills/<skill-name> <project>/.claude/skills/
```
설치 후 Claude Code 재시작 → `/<skill-name>` 으로 실행.
