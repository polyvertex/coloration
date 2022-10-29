#!/usr/bin/env python3

import contextlib
import os
import os.path
import subprocess
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LINTERS = {
    "flake8": (),
    "pylint": (),
}


@contextlib.contextmanager
def scoped_chdir(chdir=None):
    if not chdir:
        oldwd = None
    else:
        oldwd = os.getcwd()
        os.chdir(chdir)

    try:
        yield
    finally:
        if oldwd:
            os.chdir(oldwd)


def safety_checks():
    if not sys.executable:
        raise RuntimeError("no sys.executable")

    if not os.path.isdir(PROJECT_DIR):
        raise RuntimeError(f"project dir not found at: {PROJECT_DIR}")

    for name in ("setup.cfg", "pyproject.toml"):
        if os.path.isfile(os.path.join(PROJECT_DIR, name)):
            break
    else:
        raise RuntimeError(f"not a project dir at: {PROJECT_DIR}")


def list_project_python_packages():
    EXCLUDED = (
        "demo", "demos", "examples", "scripts", "tools", "test", "tests",
        "t", "temp", "tmp")
    packages = []

    with scoped_chdir(PROJECT_DIR):
        with os.scandir() as dirit:
            for direntry in dirit:
                if not direntry.name or direntry.name[0] in (".", "_"):
                    continue

                if direntry.name.lower() in EXCLUDED:
                    continue

                if not direntry.is_dir(follow_symlinks=False):
                    continue

                initpy = os.path.join(direntry.path, "__init__.py")
                if not os.path.isfile(initpy):
                    continue

                packages.append(os.path.normpath(direntry.path))

    return packages


def run_linters(targets):
    discovered_packages = None

    for linter, linterargs in LINTERS.items():
        if not targets and linter == "pylint":
            if discovered_packages is None:
                discovered_packages = list_project_python_packages()
            linter_targets = discovered_packages
        else:
            linter_targets = targets

        targets_msg = "." if not linter_targets else ", ".join(linter_targets)

        cmdargs = [
            sys.executable, "-B", "-m", linter,
            *linterargs, *linter_targets]

        print(f" >> LINTER {linter}: {targets_msg}", flush=True)
        res = subprocess.run(cmdargs, cwd=PROJECT_DIR, check=False)
        print(f" -- LINTER {linter}: exit code {res.returncode}", flush=True)


def main(args=None):
    safety_checks()

    args = sys.argv[1:] if args is None else args[:]
    if args and args[0] in ("-h", "--help"):
        print("usage: codequal <dir_or_file>...")
        sys.exit(1)

    run_linters([] if not args else args[:])


if __name__ == "__main__":
    main()
