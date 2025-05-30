#!/usr/bin/env python3
"""
Auto-fix code errors using OpenAI Codex and create a GitHub PR with tests and migrations.

Usage:
    python auto_fix_error.py "<error message>"

Prerequisites:
    - openai CLI installed and configured (OPENAI_API_KEY set).
    - Git repository initialized with remote "origin".
    - GitHub CLI (`gh`) installed and authenticated.
    - Tests available (e.g., pytest or unittest).
    - Django project if migrations are needed (`manage.py migrate`).
"""
import argparse
import subprocess
import tempfile
import os
import sys
import json
import uuid


def generate_patch(error_message: str) -> str:
    prompt = f"""
# Provide a unified diff patch to fix the following error in the codebase.
# Also include a new automated test to catch this error in the future.
# After applying the patch, migrations should run if needed.
# Error message:
{error_message}
"""
    result = subprocess.run(
        [
            "openai", "api", "completions.create",
            "-m", "code-davinci-002",
            "--prompt", prompt,
            "--max-tokens", "1024",
            "--temperature", "0"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )
    data = json.loads(result.stdout)
    return data["choices"][0]["text"].strip()


def apply_patch(patch_text: str):
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write(patch_text)
        tmp_path = tmp.name
    try:
        subprocess.run(["git", "apply", tmp_path], check=True)
    except subprocess.CalledProcessError as e:
        print("Failed to apply patch:\n", e.stderr.decode(), file=sys.stderr)
        sys.exit(1)
    finally:
        os.remove(tmp_path)


def run_migrations():
    # Run Django migrations if a manage.py is present
    if os.path.exists("manage.py"):
        print("Running migrations...")
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)


def run_tests():
    print("Running tests...")
    # Prefer pytest if available, fallback to unittest
    try:
        subprocess.run(["pytest"], check=True)
    except FileNotFoundError:
        subprocess.run([sys.executable, "-m", "unittest", "discover"], check=True)


def create_branch() -> str:
    branch_name = f"fix/error-correction-{uuid.uuid4().hex[:8]}"
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    return branch_name


def commit_changes(error_message: str) -> str:
    subprocess.run(["git", "add", "-A"], check=True)
    summary = error_message.splitlines()[0][:50]
    commit_msg = f"Fix error: {summary}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    return commit_msg


def push_branch(branch_name: str):
    subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)


def create_pr(commit_msg: str, error_message: str):
    pr_title = commit_msg
    pr_body = f"""## Summary
This PR fixes the following error:

```
{error_message}
```

- Inline comments explain the fix.
- Includes a new automated test to prevent regression.
- Migrations have been applied if necessary.
"""
    subprocess.run([
        "gh", "pr", "create",
        "--title", pr_title,
        "--body", pr_body
    ], check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Auto-fix code errors using OpenAI Codex and create a GitHub PR with tests and migrations."
    )
    parser.add_argument(
        "error_message",
        help="Error message from the system log"
    )
    args = parser.parse_args()

    # Ensure we're at repo root
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True,
                       stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Not inside a git repository. Run this at the project root.", file=sys.stderr)
        sys.exit(1)

    error_msg = args.error_message

    print("Generating patch with OpenAI Codex...")
    patch = generate_patch(error_msg)

    print("Creating new branch...")
    branch = create_branch()

    print("Applying patch...")
    apply_patch(patch)

    run_migrations()
    run_tests()

    print("Committing changes...")
    commit_msg = commit_changes(error_msg)

    print("Pushing branch...")
    push_branch(branch)

    print("Creating pull request...")
    create_pr(commit_msg, error_msg)

    print("Pull request created successfully.")

if __name__ == '__main__':
    main()
