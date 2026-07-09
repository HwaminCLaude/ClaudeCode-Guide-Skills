# 설계 원칙 — STAT TEST ADVISOR 사례에서 뽑은 3가지

강의의 "통계 검정 자문 서버"(순수 파이썬 + FastMCP, 약 290줄,
`inspect_data → check_assumptions → run_test`)에서 뽑은 원칙. Phase 3~4 결정을 코드로 옮길 때 이 규칙을 적용한다.
셋 다 코드 기술이 아니라 **AI를 향한 커뮤니케이션 설계**다.

---

## 원칙 1 — 순서를 강제하라 (docstring에 순서를 새긴다)
`ordered=true`면 각 도구 docstring 앞에 순서 태그를 붙인다. AI는 도구 설명을 읽고 따르므로, **설명이 곧 규칙**이 된다.

```python
@mcp.tool()
def inspect_data(...):
    """[1단계 - 필수 선행] 데이터 구조를 파악합니다. 어떤 검정이든 반드시 이 도구를 먼저 호출하세요."""

@mcp.tool()
def check_assumptions(...):
    """[2단계 - 필수 선행] 정규성·등분산성을 검정하고 적절한 방법을 추천합니다. run_test 전에 필수."""

@mcp.tool()
def run_test(...):
    """[3단계] recommendation에 따라 선택하세요. 다른 검정을 쓰려면 이유를 사용자에게 설명해야 합니다."""
```

→ `render_server.py`는 `tools[i].orderTag`를 docstring 맨 앞에 넣는다.

## 원칙 2 — 답과 함께 길을 줘라 (모든 응답에 recommendation·next_step)
`returnShape="result_next_step"`인 도구는 dict를 반환하고 **`next_step`(그리고 필요하면 `recommendation`)** 을 포함한다.
"다음은 3번 창구입니다"처럼, AI가 다음 도구를 헤매지 않게.

```python
return {
    "recommendation": {"test": "welch", "reason": "정규성 충족, 등분산 위반"},
    "caution": "소표본은 검정력이 낮습니다.",
    "next_step": "run_test('welch') 를 호출하세요.",
}
```

→ 도구 설명은 *호출 전*의 길잡이, 응답의 `next_step`은 *호출 후*의 길잡이. 양쪽으로 AI를 안내한다.

## 원칙 3 — 숫자에 맥락을 붙여라 (맨 값 반환 금지)
`returnShape="number_interpretation"`인 도구는 값만 던지지 않는다. **효과크기 · 표본 수 · 해석 가이드**를 함께 반환해
AI의 성급한 결론을 도구 차원에서 막는다. (통계 예: p값만 반환 ✗)

```python
return {
    "p_value": 0.032,
    "effect_size": {"name": "cohen_d", "value": 0.41},
    "n": 28,
    "interpretation": "유의하지만 효과크기는 중간 이하이고 표본이 작아 재현 확인이 필요합니다.",
}
```

→ `render_server.py`는 이 반환 형태에서 **단일 스칼라 반환을 거부**하고, 위 dict 골격을 생성한다.

---

## 요약 매핑
| ServerSpec | 코드에 반영 |
|---|---|
| `ordered=true` + `orderTag` | docstring 맨 앞 `[N단계 - 필수 선행]` |
| `returnShape=result_next_step` | 반환 dict에 `next_step`(+`recommendation`) |
| `returnShape=number_interpretation` | 반환 dict에 `effect_size`·`n`·`interpretation` (맨 값 ✗) |
