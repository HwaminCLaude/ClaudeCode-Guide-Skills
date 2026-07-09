#!/usr/bin/env python
"""Validate a ServerSpec JSON before code generation. Stdlib only.

Usage:  python validate_spec.py <spec.json>
Prints JSON {ok, errors, warnings} to stdout. Exit code 1 if invalid.
"""
import json
import re
import sys

IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
URI = re.compile(r"^[a-z][a-z0-9+.-]*://.+", re.IGNORECASE)
ENVVAR = re.compile(r"^[A-Z_][A-Z0-9_]*$")

TYPES = {"str", "int", "float", "bool", "list", "dict"}
ARCHETYPES = {"data-lookup", "automation", "integration", "analysis-workflow"}
RETURN_SHAPES = {"result_next_step", "number_interpretation", "string", "status"}
PRIVILEGES = {"readonly-dir", "select-db", "scoped-key", "write"}
TRANSPORTS = {"stdio", "sse", "streamable-http"}
REGISTERS = {"code", "desktop", "both", "none"}


def validate(spec):
    errors, warnings = [], []

    def err(m):
        errors.append(m)

    def warn(m):
        warnings.append(m)

    meta = spec.get("meta", {})
    name = meta.get("serverName", "")
    if not name:
        err("meta.serverName 이 비어 있습니다.")
    elif not SLUG.match(name):
        err(f"meta.serverName '{name}' 은 소문자/숫자/하이픈 슬러그여야 합니다.")

    if meta.get("archetype") and meta["archetype"] not in ARCHETYPES:
        warn(f"meta.archetype '{meta['archetype']}' 은 알려진 값이 아닙니다.")

    tools = spec.get("tools", []) or []
    resources = spec.get("resources", []) or []
    prompts = spec.get("prompts", []) or []
    if not (tools or resources or prompts):
        err("tools / resources / prompts 중 최소 하나는 있어야 합니다.")

    seen = set()
    for i, t in enumerate(tools):
        tn = t.get("name", "")
        loc = f"tools[{i}]"
        if not tn:
            err(f"{loc}.name 이 비어 있습니다.")
        elif not IDENT.match(tn):
            err(f"{loc}.name '{tn}' 은 유효한 파이썬 식별자여야 합니다(소문자·밑줄).")
        elif tn in seen:
            err(f"도구 이름 '{tn}' 이 중복됩니다.")
        seen.add(tn)

        if not (t.get("docstring") or "").strip():
            err(f"{loc}({tn}).docstring 이 비어 있습니다. AI가 언제 호출할지 한 문장 필요.")

        rs = t.get("returnShape", "result_next_step")
        if rs not in RETURN_SHAPES:
            err(f"{loc}({tn}).returnShape '{rs}' 이 유효하지 않습니다: {sorted(RETURN_SHAPES)}")

        for j, p in enumerate(t.get("params", []) or []):
            pn = p.get("name", "")
            if not IDENT.match(pn or ""):
                err(f"{loc}({tn}).params[{j}].name '{pn}' 이 유효한 식별자가 아닙니다.")
            pt = p.get("type", "str")
            if pt not in TYPES:
                err(f"{loc}({tn}).params[{j}].type '{pt}' 미지원. 허용: {sorted(TYPES)}")

        if t.get("sideEffecting") and not spec.get("security", {}).get("approvalGate", True):
            warn(f"{tn} 은 부수효과가 있는데 승인 게이트가 꺼져 있습니다.")

    for i, r in enumerate(resources):
        if not IDENT.match(r.get("name", "") or ""):
            err(f"resources[{i}].name '{r.get('name')}' 이 유효한 식별자가 아닙니다.")
        if not URI.match(r.get("uri", "") or ""):
            err(f"resources[{i}].uri '{r.get('uri')}' 은 'scheme://...' 형식이어야 합니다.")

    for i, p in enumerate(prompts):
        if not IDENT.match(p.get("name", "") or ""):
            err(f"prompts[{i}].name '{p.get('name')}' 이 유효한 식별자가 아닙니다.")

    sec = spec.get("security", {}) or {}
    if sec.get("privilege") and sec["privilege"] not in PRIVILEGES:
        err(f"security.privilege '{sec['privilege']}' 유효하지 않음: {sorted(PRIVILEGES)}")
    secrets = sec.get("secrets", {}) or {}
    if secrets.get("mode") == "env":
        for k in secrets.get("keys", []) or []:
            if not ENVVAR.match(k):
                err(f"security.secrets.keys 의 '{k}' 은 대문자 환경변수 이름이어야 합니다.")

    rt = spec.get("runtime", {}) or {}
    if rt.get("transport", "stdio") not in TRANSPORTS:
        err(f"runtime.transport '{rt.get('transport')}' 유효하지 않음: {sorted(TRANSPORTS)}")
    if rt.get("register", "code") not in REGISTERS:
        err(f"runtime.register '{rt.get('register')}' 유효하지 않음: {sorted(REGISTERS)}")

    if spec.get("ordered") and not any(t.get("orderTag") for t in tools):
        warn("ordered=true 이지만 orderTag 가 하나도 없습니다. render 단계에서 자동 부여됩니다.")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "errors": ["spec 경로 인자가 필요합니다."],
                          "warnings": []}, ensure_ascii=False))
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    result = validate(spec)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
