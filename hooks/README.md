# hooks/ — 훅 설정 모음 (예정)

Claude Code [Hooks](https://code.claude.com/docs/en/hooks)는 특정 이벤트(도구 실행 전후, 세션 종료 등)에
자동으로 명령을 실행하게 하는 설정입니다. 이 카테고리에는 재사용 가능한 훅 예제와 설정을 모을 예정입니다.

> 🚧 준비 중 — 곧 예제가 추가됩니다.

## 다룰 내용 (계획)

- `PreToolUse` / `PostToolUse` — 도구 실행 전후 검사·포맷·로깅
- `Stop` / `SubagentStop` — 작업 종료 시 알림·정리
- `UserPromptSubmit` — 프롬프트 전처리
- `settings.json` 에 훅을 등록하는 표준 패턴과 주의점

## 폴더 구성 (예정)

```
hooks/
├── README.md
└── <hook-name>/
    ├── README.md          # 무엇을·언제·왜
    ├── settings.snippet.json   # settings.json 에 병합할 훅 블록
    └── scripts/           # 훅이 호출하는 스크립트
```
