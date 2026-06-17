#!/usr/bin/env python3
"""SDD+ change packet helper. Cross-platform replacement for scripts/sdd.ps1.

Commands:
  init                       Create the sdd-plus directory structure.
  new <kebab-change-name>    Create a change packet from templates.
  status                     List active changes and task counts.
  verify <kebab-change-name> Check required artifacts exist and are filled in.
  archive <kebab-change-name> [--force]  Move a completed change to the archive.
"""

import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

REQUIRED_FILES = ["brief.md", "plan.md", "tasks.md", "decision-log.md", "verification.md"]
SDD_DIRS = ["sdd-plus", "sdd-plus/standards", "sdd-plus/specs",
            "sdd-plus/changes", "sdd-plus/archive", "sdd-plus/templates"]
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLACEHOLDER = re.compile(r"^\s*-?\s*TBD\s*$", re.MULTILINE)


def find_root(require: bool = True) -> Path:
    """Walk up from cwd looking for an sdd-plus directory. Never falls back silently."""
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "sdd-plus").is_dir():
            return candidate
    if require:
        sys.exit("error: no sdd-plus directory found in this or any parent directory. "
                 "Run 'python scripts/sdd.py init' from the project root first.")
    return current


def assert_kebab(name: str) -> None:
    if not name:
        sys.exit("error: change name is required.")
    if not KEBAB.match(name):
        sys.exit("error: change name must be kebab-case, e.g. improve-search-flow.")


def cmd_init() -> None:
    root = find_root(require=False)
    for d in SDD_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    print(f"Initialized SDD+ directories under {root}")


def render_template(template: Path, target: Path, change_name: str) -> None:
    content = template.read_text(encoding="utf-8-sig")  # tolerate legacy BOMs on read
    content = content.replace("{{CHANGE_NAME}}", change_name)
    content = content.replace("{{DATE}}", datetime.date.today().isoformat())
    target.write_text(content, encoding="utf-8")  # never write a BOM


def cmd_new(name: str) -> None:
    assert_kebab(name)
    root = find_root()
    change_dir = root / "sdd-plus" / "changes" / name
    if change_dir.exists():
        sys.exit(f"error: change already exists: {change_dir.relative_to(root)}")
    change_dir.mkdir(parents=True)
    template_dir = root / "sdd-plus" / "templates"
    for fname in REQUIRED_FILES:
        template = template_dir / fname
        target = change_dir / fname
        if template.is_file():
            render_template(template, target, name)
        else:
            target.write_text(f"# {fname}\n\nChange: {name}\n", encoding="utf-8")
    specs_dir = change_dir / "specs"
    specs_dir.mkdir()
    delta_template = template_dir / "spec-delta.md"
    if delta_template.is_file():
        render_template(delta_template, specs_dir / "EXAMPLE-capability.md.template", name)
    print(f"Created change: {change_dir.relative_to(root)}")
    print("If this change modifies system behavior, add delta specs under "
          f"{specs_dir.relative_to(root)}/<capability>.md")


def task_counts(tasks_path: Path) -> tuple[int, int]:
    if not tasks_path.is_file():
        return 0, 0
    lines = tasks_path.read_text(encoding="utf-8-sig").splitlines()
    complete = sum(1 for l in lines if re.match(r"^\s*-\s*\[[xX]\]\s+", l))
    pending = sum(1 for l in lines if re.match(r"^\s*-\s*\[\s\]\s+", l))
    return complete, pending


def delta_spec_files(change_dir: Path) -> list[Path]:
    specs_dir = change_dir / "specs"
    if not specs_dir.is_dir():
        return []
    return sorted(p for p in specs_dir.glob("*.md") if not p.name.endswith(".template"))


def delta_capabilities(change_dir: Path) -> list[str]:
    caps = []
    for f in delta_spec_files(change_dir):
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            if line.lower().startswith("capability:"):
                cap = line.split(":", 1)[1].strip().strip("`<>")
                if cap and not cap.startswith("kebab-capability"):
                    caps.append(cap)
                break
    return caps


def cmd_status() -> None:
    root = find_root()
    changes_root = root / "sdd-plus" / "changes"
    changes = sorted(p for p in changes_root.iterdir() if p.is_dir()) if changes_root.is_dir() else []
    if not changes:
        print("No active SDD+ changes.")
        return
    for change in changes:
        complete, pending = task_counts(change / "tasks.md")
        deltas = delta_spec_files(change)
        suffix = f", {len(deltas)} delta spec(s)" if deltas else ""
        print(f"{change.name}: {complete} complete, {pending} pending{suffix}")


def cmd_verify(name: str) -> int:
    assert_kebab(name)
    root = find_root()
    change_dir = root / "sdd-plus" / "changes" / name
    if not change_dir.is_dir():
        sys.exit(f"error: change not found: sdd-plus/changes/{name}")

    standards_dir = root / "sdd-plus" / "standards"
    if not standards_dir.is_dir() or not any(standards_dir.iterdir()):
        sys.exit("error: no standards found under sdd-plus/standards.")

    missing = [f for f in REQUIRED_FILES if not (change_dir / f).is_file()]
    if missing:
        sys.exit(f"error: missing required artifacts: {', '.join(missing)}")

    unfilled = []
    for fname in REQUIRED_FILES:
        text = (change_dir / fname).read_text(encoding="utf-8-sig")
        if PLACEHOLDER.search(text) or "{{CHANGE_NAME}}" in text:
            unfilled.append(fname)

    complete, pending = task_counts(change_dir / "tasks.md")
    print(f"Verified artifacts for {name}.")
    print(f"Tasks: {complete} complete, {pending} pending.")
    if unfilled:
        print(f"warning: unfilled placeholder content (TBD) remains in: {', '.join(unfilled)}")
    if pending > 0:
        print("Pending tasks remain. Archive will require --force.")
    return 1 if unfilled else 0


def cmd_archive(name: str, force: bool) -> None:
    rc = cmd_verify(name)
    root = find_root()
    change_dir = root / "sdd-plus" / "changes" / name
    unsynced = [
        cap for cap in delta_capabilities(change_dir)
        if not (root / "sdd-plus" / "specs" / "capabilities" / f"{cap}.md").is_file()
    ]
    if unsynced and not force:
        sys.exit(
            "error: delta specs reference capabilities with no living spec yet: "
            + ", ".join(unsynced)
            + ". Run the spec-sync skill (/sdd:sync) first, or rerun with --force."
        )
    _, pending = task_counts(change_dir / "tasks.md")
    if (pending > 0 or rc != 0) and not force:
        sys.exit("error: cannot archive with pending tasks or unfilled placeholders. "
                 "Complete the packet or rerun with --force.")
    archive_root = root / "sdd-plus" / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    target = archive_root / f"{datetime.date.today().isoformat()}-{name}"
    if target.exists():
        sys.exit(f"error: archive already exists: {target.relative_to(root)}")
    shutil.move(str(change_dir), str(target))
    print(f"Archived change: {target.relative_to(root)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SDD+ change packet helper.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    p_new = sub.add_parser("new")
    p_new.add_argument("name")
    sub.add_parser("status")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("name")
    p_archive = sub.add_parser("archive")
    p_archive.add_argument("name")
    p_archive.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "new":
        cmd_new(args.name)
    elif args.command == "status":
        cmd_status()
    elif args.command == "verify":
        sys.exit(cmd_verify(args.name))
    elif args.command == "archive":
        cmd_archive(args.name, args.force)


if __name__ == "__main__":
    main()
