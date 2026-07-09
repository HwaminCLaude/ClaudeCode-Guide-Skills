#!/usr/bin/env python
"""Render a ServerSpec JSON into a FastMCP server.py (+ project files). Stdlib only.

Usage:
  python render_server.py <spec.json> --stdout          # preview server.py only
  python render_server.py <spec.json> --out <dir>       # write all files into <dir>

Bakes in the lecture's design principles + Ch4 guardrails:
  - ordered  -> docstring gets "[N단계 - 필수 선행]" prefix
  - returnShape result_next_step   -> return dict includes next_step
  - returnShape number_interpretation -> return dict includes effect_size/n/interpretation
    (a bare scalar return is refused by construction)
  - secrets  -> os.environ fail-fast load, never hardcoded
  - approvalGate + sideEffecting -> confirm gate
  - stdio    -> logging to stderr only, never print() to stdout
"""
import argparse
import json
import os
import sys

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")

TYPE_HINT = {"str": "str", "int": "int", "float": "float",
             "bool": "bool", "list": "list", "dict": "dict"}
DICT_SHAPES = {"result_next_step", "number_interpretation", "status"}


def read_template(name):
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as f:
        return f.read()


def indent(text, n=4):
    pad = " " * n
    return "\n".join(pad + line if line else line for line in text.split("\n"))


def error_return(shape):
    if shape == "string":
        return 'return "입력이 유효하지 않습니다."'
    return 'return {"status": "invalid_input", "message": "입력값을 확인하세요."}'


def success_return(shape):
    if shape == "string":
        return 'return "TODO: 결과 문자열을 반환하세요."'
    if shape == "result_next_step":
        return ('return {\n'
                '    "result": None,  # TODO: 실제 결과\n'
                '    # "recommendation": {...},  # 필요하면 추천 포함\n'
                '    "next_step": "AI에게 다음에 무엇을 하라고 안내하세요.",\n'
                '}')
    if shape == "number_interpretation":
        # 원칙3: 맨 값 반환 금지 — 맥락을 강제
        return ('return {\n'
                '    "value": None,        # TODO: 계산 값\n'
                '    "effect_size": {"name": "", "value": None},\n'
                '    "n": None,            # 표본 수\n'
                '    "interpretation": "값의 의미와 주의점을 문장으로 적으세요.",\n'
                '}')
    # status
    return 'return {"status": "ok", "message": "완료"}'


def render_tool(t, spec):
    name = t["name"]
    params = list(t.get("params", []) or [])
    shape = t.get("returnShape", "result_next_step")
    side = bool(t.get("sideEffecting"))
    approval = bool(spec.get("security", {}).get("approvalGate", True))
    validation = set(spec.get("security", {}).get("validation", []) or [])
    gate = side and approval

    # signature
    sig = [f"{p['name']}: {TYPE_HINT.get(p.get('type', 'str'), 'str')}" for p in params]
    if gate:
        sig.append("confirm: bool = False")
    ret_hint = "dict" if (shape in DICT_SHAPES or gate) else "str"

    # docstring
    doc = (t.get("docstring") or "").strip()
    order_tag = t.get("orderTag")
    if spec.get("ordered") and order_tag:
        doc = f"{order_tag} {doc}"
    lines = [f'    """{doc}']
    if params:
        lines.append("")
        lines.append("    Args:")
        for p in params:
            lines.append(f"        {p['name']}: {p.get('desc', '') or '...'}")
    if gate:
        lines.append("        confirm: 위험 작업이므로 True 일 때만 실제로 실행합니다.")
    lines.append('    """')
    docstring = "\n".join(lines)

    body = []
    # 입력 검증 (Ch4)
    str_params = [p["name"] for p in params if p.get("type", "str") == "str"]
    if "type-schema" in validation and str_params:
        body.append("    # 입력 검증 (Ch4)")
        cond = " or ".join(f"not {n} or not str({n}).strip()" for n in str_params)
        body.append(f"    if {cond}:")
        body.append(f"        {error_return(shape if not gate else 'status')}")
    if "whitelist" in validation:
        body.append("    # 허용 목록만 통과 (Ch4). 예: ALLOWED = {\"a\", \"b\"}")
    if "injection-block" in validation:
        body.append("    # 인젝션 차단: 문자열 결합 금지, 파라미터 바인딩/shell=False 사용")
    if "regex" in validation:
        body.append("    # 형식 검사: re.fullmatch(...) 로 검증")

    # 승인 게이트 (Ch4)
    if gate:
        body.append("    if not confirm:")
        body.append('        return {"status": "confirmation_required",')
        body.append('                "preview": "이 작업은 되돌리기 어렵습니다.",')
        body.append('                "next_step": "확인했으면 confirm=True 로 다시 호출하세요."}')

    # 성공 반환 골격 (returnShape 에 따라 구조 강제)
    body.append(indent(success_return(shape), 4))

    out = ["@mcp.tool()",
           f"def {name}({', '.join(sig)}) -> {ret_hint}:",
           docstring]
    out.extend(body)
    return "\n".join(out)


def render_resource(r):
    return "\n".join([
        f'@mcp.resource("{r["uri"]}")',
        f'def {r["name"]}() -> str:',
        f'    """{(r.get("job") or "자료").strip()}"""',
        '    return "TODO: 이 자료의 내용을 반환하세요."',
    ])


def render_prompt(p):
    return "\n".join([
        "@mcp.prompt()",
        f'def {p["name"]}(text: str) -> str:',
        f'    """{(p.get("job") or "프롬프트 템플릿").strip()}"""',
        '    return f"TODO 템플릿: {text}"',
    ])


def render_server_py(spec):
    name = spec["meta"]["serverName"]
    transport = spec.get("runtime", {}).get("transport", "stdio")
    secrets = spec.get("security", {}).get("secrets", {}) or {}
    keys = secrets.get("keys", []) if secrets.get("mode") == "env" else []

    parts = []
    parts.append('# ' + name + ' — /build-mcp-server 로 생성된 MCP 서버')
    parts.append("# ① 준비")
    parts.append("import sys")
    parts.append("import logging")
    if keys:
        parts.append("import os")
    parts.append("")
    parts.append("from mcp.server.fastmcp import FastMCP")
    parts.append("")
    parts.append("# stdio 위생: stdout 은 JSON-RPC 전용. 로그는 stderr 로만.")
    parts.append("logging.basicConfig(level=logging.INFO, stream=sys.stderr)")
    parts.append(f'log = logging.getLogger("{name}")')
    parts.append("")
    if keys:
        parts.append("# 비밀키 로드 (Ch4): 코드에 두지 말고 .env 에서. 없으면 실행 거부(fail-fast).")
        for k in keys:
            parts.append(f'{k} = os.environ.get("{k}")')
            parts.append(f'if not {k}:')
            parts.append(f'    raise RuntimeError("{k} 가 없습니다. .env 를 확인하세요.")')
        parts.append("")
    parts.append(f'mcp = FastMCP("{name}")')
    parts.append("")

    tools = spec.get("tools", []) or []
    resources = spec.get("resources", []) or []
    prompts = spec.get("prompts", []) or []

    if tools:
        parts.append("# ② 도구 · Tools")
        for t in tools:
            parts.append("")
            parts.append(render_tool(t, spec))
        parts.append("")
    if resources:
        parts.append("# ③ 자료실 · Resources")
        for r in resources:
            parts.append("")
            parts.append(render_resource(r))
        parts.append("")
    if prompts:
        parts.append("# ④ 레시피 · Prompts")
        for p in prompts:
            parts.append("")
            parts.append(render_prompt(p))
        parts.append("")

    parts.append("# ⑤ 실행")
    parts.append('if __name__ == "__main__":')
    parts.append(f'    mcp.run(transport="{transport}")')
    parts.append("")
    return "\n".join(parts)


def render_env_example(spec):
    tmpl = read_template("env.example.template")
    secrets = spec.get("security", {}).get("secrets", {}) or {}
    keys = secrets.get("keys", []) if secrets.get("mode") == "env" else []
    body = "\n".join(f"{k}=" for k in keys) if keys else "# (이 서버는 API 키가 필요 없습니다)"
    return tmpl.replace("{{serverName}}", spec["meta"]["serverName"]).replace("{{envKeys}}", body)


def render_pyproject(spec):
    return read_template("pyproject.toml.template").replace(
        "{{serverName}}", spec["meta"]["serverName"])


def write_files(spec, out_dir):
    name = spec["meta"]["serverName"]
    written = []

    def write(fn, content):
        path = os.path.join(out_dir, fn)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        written.append(path)

    write(f"{name}.py", render_server_py(spec))
    write("pyproject.toml", render_pyproject(spec))
    write(".env.example", render_env_example(spec))
    write(".gitignore", read_template("gitignore.template"))
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--stdout", action="store_true", help="print server.py only (preview)")
    ap.add_argument("--out", help="output directory to write all files")
    args = ap.parse_args()

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)

    if args.stdout or not args.out:
        sys.stdout.write(render_server_py(spec))
        return

    os.makedirs(args.out, exist_ok=True)
    written = write_files(spec, args.out)
    print(json.dumps({"written": written}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
