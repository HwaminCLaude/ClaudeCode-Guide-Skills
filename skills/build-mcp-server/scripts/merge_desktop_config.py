#!/usr/bin/env python
"""Safely merge one MCP server into claude_desktop_config.json (or emit a snippet).

Usage:
  python merge_desktop_config.py --spec <spec.json> --config <path> [--apply]

Without --apply: writes a snippet next to the project (dry, non-destructive) and prints it.
With --apply: safely merges into <path> IF its parent dir exists (Claude Desktop installed).

Safety guarantees:
  - read-or-create; if existing file is unparseable -> ABORT (never clobber a recoverable file)
  - timestamped .bak-* backup before any write
  - deep-merge only this server key; sibling servers are preserved
  - re-serialize + re-parse to validate before replacing
  - idempotent: skip write if content is unchanged
  - atomic replace (os.replace)
Stdlib only.
"""
import argparse
import json
import os
import sys
import time


def build_block(spec):
    name = spec["meta"]["serverName"]
    project_dir = spec.get("runtime", {}).get("projectDir", "")
    if not project_dir:
        raise SystemExit("runtime.projectDir 가 비어 있습니다. 절대경로가 필요합니다.")
    project_dir = os.path.abspath(project_dir)
    secrets = spec.get("security", {}).get("secrets", {}) or {}
    keys = secrets.get("keys", []) if secrets.get("mode") == "env" else []
    block = {
        "command": "uv",
        "args": ["run", "--directory", project_dir, "python", f"{name}.py"],
    }
    if keys:
        # 값은 사용자가 채운다. 실제 키를 커밋하지 말 것.
        block["env"] = {k: "" for k in keys}
    return name, block


def load_existing(path):
    if not os.path.isfile(path):
        return {"mcpServers": {}}, False
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if not raw.strip():
        return {"mcpServers": {}}, True
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"기존 {path} 를 파싱할 수 없습니다({e}). 덮어쓰지 않고 중단합니다. "
            f"먼저 JSON을 고쳐 주세요.")
    if not isinstance(data.get("mcpServers"), dict):
        data["mcpServers"] = data.get("mcpServers") or {}
    return data, True


def atomic_write(path, data):
    tmp = path + ".tmp"
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)  # re-parse validation
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--config", required=True, help="target claude_desktop_config.json path")
    ap.add_argument("--apply", action="store_true", help="actually merge into --config")
    args = ap.parse_args()

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    name, block = build_block(spec)

    snippet = {"mcpServers": {name: block}}
    parent_exists = os.path.isdir(os.path.dirname(args.config))

    if not args.apply or not parent_exists:
        # 비파괴적: 프로젝트 폴더에 스니펫만 남긴다.
        out = os.path.join(os.path.abspath(spec.get("runtime", {}).get("projectDir", ".")),
                           "claude_desktop_config.snippet.json")
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(snippet, ensure_ascii=False, indent=2) + "\n")
        reason = "Desktop 미설치(부모 폴더 없음)" if not parent_exists else "--apply 미지정"
        print(json.dumps({
            "action": "snippet_only", "reason": reason, "path": out,
            "note": "설치 후 이 블록을 claude_desktop_config.json 에 병합하고 완전 재시작하세요.",
            "snippet": snippet,
        }, ensure_ascii=False, indent=2))
        return

    data, existed = load_existing(args.config)
    before = json.dumps(data, ensure_ascii=False, sort_keys=True)
    data.setdefault("mcpServers", {})[name] = block
    after = json.dumps(data, ensure_ascii=False, sort_keys=True)

    if existed and before == after:
        print(json.dumps({"action": "unchanged", "path": args.config,
                          "server": name}, ensure_ascii=False, indent=2))
        return

    backup = None
    if existed:
        backup = f"{args.config}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        with open(args.config, encoding="utf-8") as src, \
                open(backup, "w", encoding="utf-8", newline="\n") as dst:
            dst.write(src.read())

    atomic_write(args.config, data)
    print(json.dumps({
        "action": "merged", "path": args.config, "server": name,
        "backup": backup,
        "note": "Claude Desktop 을 완전히 종료 후 재시작하세요(창만 닫는 것 아님).",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
