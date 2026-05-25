#!/usr/bin/env python3
"""AI-assisted governance checks for EEE pull requests."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


RISK_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("K8S_ROOT_USER", re.compile(r"runAsUser\s*:\s*0\b"), "Kubernetes workload runs as UID 0."),
    ("K8S_PRIVILEGED", re.compile(r"privileged\s*:\s*true\b"), "Kubernetes workload enables privileged mode."),
    ("K8S_PRIV_ESC", re.compile(r"allowPrivilegeEscalation\s*:\s*true\b"), "Kubernetes workload allows privilege escalation."),
    ("K8S_HOST_PATH", re.compile(r"\bhostPath\s*:"), "Kubernetes workload mounts a hostPath volume."),
    ("K8S_HOST_NETWORK", re.compile(r"hostNetwork\s*:\s*true\b"), "Kubernetes workload joins the host network."),
    ("K8S_ALL_CAPS", re.compile(r"add\s*:\s*(?:\n\s*)?-\s*ALL\b"), "Kubernetes workload adds all Linux capabilities."),
    ("IAM_WILDCARD_ACTION", re.compile(r'(?i)(?:"Action"|actions?)\s*[=:]\s*(?:\[\s*)?"\*"'), "IAM policy allows all actions."),
    ("IAM_WILDCARD_RESOURCE", re.compile(r'(?i)(?:"Resource"|resources?)\s*[=:]\s*(?:\[\s*)?"\*"'), "IAM policy allows all resources."),
    ("OPEN_SECURITY_GROUP", re.compile(r"0\.0\.0\.0/0"), "Terraform allows traffic from the public internet."),
]

REVIEWABLE_EXTENSIONS = {".tf", ".hcl", ".yaml", ".yml", ".tpl"}


@dataclass
class Finding:
    code: str
    path: Path
    line: int
    message: str
    evidence: str


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git_executable() -> str:
    configured = os.environ.get("GIT_EXE")
    if configured:
        return configured
    discovered = shutil.which("git")
    if discovered:
        return discovered
    windows_git = Path("C:/Program Files/Git/cmd/git.exe")
    if windows_git.exists():
        return str(windows_git)
    return "git"


def changed_files(base: str, head: str) -> list[Path]:
    result = run([git_executable(), "diff", "--name-only", f"{base}...{head}"])
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def is_reviewable(path: Path) -> bool:
    parts = set(path.parts)
    return path.suffix in REVIEWABLE_EXTENSIONS and ("terraform" in parts or "kubernetes" in parts)


def static_findings(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if not path.exists() or not is_reviewable(path):
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for code, pattern, message in RISK_PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(code, path, line_number, message, line.strip()))
    return findings


def ollama_review(prompt: str) -> str | None:
    endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434/api/chat")
    model = os.environ.get("OLLAMA_MODEL", "llama3.1")
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise security reviewer for Kubernetes, Helm, and Terraform changes.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError):
        return None
    return body.get("message", {}).get("content")


def openai_review(prompt: str) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    payload = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": "You are a concise security reviewer for Kubernetes, Helm, and Terraform changes.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    return body.get("choices", [{}])[0].get("message", {}).get("content")


def ai_review(paths: list[Path], provider: str) -> str | None:
    snippets: list[str] = []
    for path in paths:
        if not path.exists() or not is_reviewable(path):
            continue
        content = path.read_text(encoding="utf-8")
        snippets.append(f"--- {path}\n{content[:6000]}")

    if not snippets or provider == "static":
        return None

    prompt = (
        "Review these changed files for high-risk Kubernetes and Terraform changes. "
        "Call out only concrete blockers: root containers, privileged pods, host mounts, broad IAM, "
        "or open security groups. Return a short bullet list or 'No additional blockers'.\n\n"
        + "\n\n".join(snippets)
    )

    if provider == "ollama":
        return ollama_review(prompt)
    if provider == "openai":
        return openai_review(prompt)
    return None


def format_report(findings: list[Finding], ai_notes: str | None) -> str:
    lines = ["EEE governance review"]
    if not findings and not ai_notes:
        lines.append("")
        lines.append("No blocking Kubernetes or Terraform risks were detected.")
        return "\n".join(lines)

    if findings:
        lines.append("")
        lines.append("Blocking static findings:")
        for finding in findings:
            lines.append(
                f"- {finding.code}: {finding.path}:{finding.line} - {finding.message} `{finding.evidence}`"
            )

    if ai_notes:
        lines.append("")
        lines.append("AI review notes:")
        lines.append(ai_notes.strip())

    return "\n".join(lines)


def ai_notes_are_blocking(ai_notes: str | None) -> bool:
    if not ai_notes:
        return False
    normalized = ai_notes.lower()
    return "no additional blockers" not in normalized and "no blockers" not in normalized


def comment_on_pr(body: str) -> None:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_REF_NAME", "").split("/")[0]
    if not token or not repo or not pr_number:
        return

    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "eee-ai-reviewer",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15):
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Review changed Helm and Terraform files for risky changes.")
    parser.add_argument("--base", default=os.environ.get("BASE_REF", "origin/main"))
    parser.add_argument("--head", default=os.environ.get("HEAD_REF", "HEAD"))
    parser.add_argument("--provider", default=os.environ.get("AI_REVIEW_PROVIDER", "static"), choices=["static", "ollama", "openai"])
    parser.add_argument("--comment", action="store_true", help="Comment on the PR when GitHub env vars are available.")
    args = parser.parse_args()

    paths = changed_files(args.base, args.head)
    findings = static_findings(paths)
    ai_notes = ai_review(paths, args.provider)
    report = format_report(findings, ai_notes)
    print(report)

    if args.comment and (findings or ai_notes):
        comment_on_pr(report)

    return 1 if findings or ai_notes_are_blocking(ai_notes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
