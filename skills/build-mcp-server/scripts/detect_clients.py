#!/usr/bin/env python
"""Detect which Claude clients + toolchain are present. Prints JSON to stdout.

Used by the wizard at start-up to shape the registration choices.
Stdlib only.
"""
import glob
import json
import os
import shutil
import sys


def find_desktop_config():
    """Return (present: bool, config_path: str) for Claude Desktop on this OS."""
    appdata = os.environ.get("APPDATA")  # Windows
    if appdata:
        std = os.path.join(appdata, "Claude", "claude_desktop_config.json")
        if os.path.isdir(os.path.dirname(std)):
            return True, std
        # MSIX-packaged install fallback
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            hits = glob.glob(
                os.path.join(local, "Packages", "Claude_*", "LocalCache",
                             "Roaming", "Claude", "claude_desktop_config.json")
            )
            if hits:
                return True, hits[0]
        return False, std  # not installed; std is where it *would* live

    # macOS
    home = os.path.expanduser("~")
    mac = os.path.join(home, "Library", "Application Support", "Claude",
                       "claude_desktop_config.json")
    if os.path.isdir(os.path.dirname(mac)):
        return True, mac
    # Linux (unofficial)
    lin = os.path.join(home, ".config", "Claude", "claude_desktop_config.json")
    return (os.path.isdir(os.path.dirname(lin)), lin if os.path.isdir(os.path.dirname(lin)) else mac)


def claude_code_present():
    if shutil.which("claude"):
        return True
    return os.path.isfile(os.path.join(os.path.expanduser("~"), ".claude.json"))


def main():
    desktop_present, desktop_path = find_desktop_config()
    info = {
        "code": claude_code_present(),
        "desktop": desktop_present,
        "desktopConfigPath": desktop_path,
        "uvPath": shutil.which("uv") or "",
        "npxPath": shutil.which("npx") or "",
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
