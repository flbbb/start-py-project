from __future__ import annotations

import argparse
import re
import stat
import subprocess
from importlib import resources
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def valid_project_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name))


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def read_template(filename: str) -> str:
    # templates/ is inside the package
    return (
        resources.files("start_py_project")
        .joinpath("templates", filename)
        .read_text(encoding="utf-8")
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="start-py-project")
    parser.add_argument("name", help="Project name (directory to create)")
    args = parser.parse_args()

    project_name = args.name.strip()
    if not valid_project_name(project_name):
        raise SystemExit(
            "Invalid project name. Use letters/numbers and optionally '.', '_', '-'."
        )

    project_dir = Path.cwd() / project_name
    if project_dir.exists():
        raise SystemExit(f"Target directory already exists: {project_dir}")

    # 1) Create project using uv (packaged project => src layout)
    run(["uv", "init", "--package", project_name])
    run(["git", "branch", "-M", "main"], cwd=project_dir)
    # 2) Init git
    run(["git", "init"], cwd=project_dir)
    # Stage all files

    # 3) Load ignore templates
    base_ignore = read_template("base_ignore.tmpl").rstrip() + "\n"
    git_extra = read_template("gitignore_extra.tmpl").rstrip() + "\n"
    rsync_extra = read_template("rsyncignore_extra.tmpl").rstrip() + "\n"

    # 4) Write ignore files + helper base file
    write_file(project_dir / "base_ignore", base_ignore)
    write_file(project_dir / ".gitignore", base_ignore + "\n" + git_extra)
    write_file(
        project_dir / ".rsyncignore",
        base_ignore + ("\n" + rsync_extra if rsync_extra.strip() else ""),
    )

    # 5) Write scripts
    write_file(project_dir / "sync_to.sh", read_template("sync_to.sh.tmpl"))
    write_file(
        project_dir / "install_remote.sh", read_template("install_remote.sh.tmpl")
    )

    make_executable(project_dir / "sync_to.sh")
    make_executable(project_dir / "install_remote.sh")
    run(["git", "add", "."], cwd=project_dir)

    # Initial commit
    run(["git", "commit", "-m", "Initial commit"], cwd=project_dir)

    print(f"Created project: {project_dir}")
    print("Next:")
    print(f"  cd {project_name}")
    print("  uv sync")


if __name__ == "__main__":
    main()
