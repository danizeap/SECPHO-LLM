#!/usr/bin/env python3
"""PreToolUse hook: require an active SDD+ change before editing product source.

Enforces the 'everything is drydocked' rule at the tool level: a Write/Edit/
MultiEdit to a product-source directory is blocked when there is NO active
change packet under sdd-plus/changes/. Open one first (`/drydock:new <name>`
or `python scripts/sdd.py new <name>`).

Contract mirrors the Drydock plugin hooks: read the tool-call JSON from stdin;
exit code 2 blocks the tool call and feeds stderr back to the agent as the
reason; exit code 0 allows it. Fails OPEN on any error so a hook bug can never
brick the session.

Scope note: this enforces that *an* active change exists, not that the edit is
bound to a specific change. That's the backstop against the real failure mode
(editing source with zero open packets). Per-file change binding is a possible
future enhancement.
"""
import json
import os
import sys

# Product-source dirs that must not be edited outside an active drydock change.
# (Docs, specs, sdd-plus/, .claude/, tests, config are intentionally NOT guarded.)
GUARDED = ("backend_api", "recommendation_engine", "report_engine", "scripts")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # never break the session on malformed input

    try:
        tool_input = payload.get("tool_input") or {}
        path = tool_input.get("file_path") or tool_input.get("path") or ""
        if not path:
            return 0

        root = payload.get("cwd") or os.getcwd()
        abs_path = os.path.normpath(os.path.abspath(path))
        abs_root = os.path.normpath(os.path.abspath(root))

        try:
            rel = os.path.relpath(abs_path, abs_root).replace("\\", "/")
        except Exception:
            return 0  # different drive / unrelatable path -> not ours to guard
        if rel == ".." or rel.startswith("../"):
            return 0  # outside the repo

        first = rel.split("/", 1)[0]
        if first not in GUARDED:
            return 0  # not product source -> always allowed

        # Confirm we resolved a real drydock root. If sdd-plus/ isn't here, the
        # root was misdetected (or this isn't a drydock repo) -> fail OPEN, never
        # block on a path we can't assess.
        sddplus = os.path.join(abs_root, "sdd-plus")
        if not os.path.isdir(sddplus):
            return 0

        # Is there at least one active (non-archived) change packet?
        changes_dir = os.path.join(sddplus, "changes")
        has_active = False
        if os.path.isdir(changes_dir):
            for name in os.listdir(changes_dir):
                packet = os.path.join(changes_dir, name)
                if os.path.isdir(packet) and os.path.isfile(os.path.join(packet, "brief.md")):
                    has_active = True
                    break
        if has_active:
            return 0

        print(
            f"Blocked by SDD+ drydock guardrail: editing product source ('{rel}') with NO "
            "active change packet. Open one first: `python scripts/sdd.py new <kebab-name>` "
            "(or /drydock:new <name>). Product source is never edited outside a drydock change.",
            file=sys.stderr,
        )
        return 2
    except Exception:
        return 0  # fail open: a guardrail bug must never block legitimate work


if __name__ == "__main__":
    sys.exit(main())
