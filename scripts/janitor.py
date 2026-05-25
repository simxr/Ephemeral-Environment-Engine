#!/usr/bin/env python3
"""Clean stale EEE preview environments."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


NAMESPACE_PATTERN = re.compile(r"^env-pr-(?P<number>[0-9]+)$")


def run(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_kubernetes_timestamp(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_namespaces() -> list[dict[str, Any]]:
    result = run(["kubectl", "get", "namespaces", "-o", "json"])
    payload = json.loads(result.stdout)
    return payload.get("items", [])


def github_pr_state(repo: str, pr_number: str, token: str | None) -> str | None:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "eee-janitor",
        },
    )

    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "missing"
        raise
    except urllib.error.URLError:
        return None

    if payload.get("merged_at"):
        return "merged"

    return payload.get("state")


def should_delete(namespace: dict[str, Any], repo: str, max_age_hours: float, token: str | None) -> tuple[bool, str]:
    metadata = namespace.get("metadata", {})
    name = metadata.get("name", "")
    match = NAMESPACE_PATTERN.match(name)
    if not match:
        return False, "namespace is not an EEE preview"

    created_at = parse_kubernetes_timestamp(metadata["creationTimestamp"])
    age_hours = (utc_now() - created_at).total_seconds() / 3600
    pr_number = match.group("number")
    state = github_pr_state(repo, pr_number, token)

    if state in {"closed", "merged", "missing"}:
        return True, f"github-pr-{state}"

    if age_hours >= max_age_hours:
        return True, f"age-{age_hours:.1f}h"

    if state is None:
        return False, f"active-or-unknown-github-state age-{age_hours:.1f}h"

    return False, f"github-pr-{state} age-{age_hours:.1f}h"


def delete_namespace(name: str, apply: bool) -> None:
    command = ["kubectl", "delete", "namespace", name, "--ignore-not-found=true"]
    if apply:
        run(command)
    else:
        print("DRY RUN:", " ".join(command))


def destroy_terraform(repo_root: Path, pr_number: str, apply: bool) -> None:
    live_dir = repo_root / "terraform" / "live" / "pr" / pr_number
    if not live_dir.exists():
        print(f"Skipping Terragrunt destroy; no live directory at {live_dir}")
        return

    command = ["terragrunt", "destroy", "-auto-approve"]
    if apply:
        run(command, cwd=live_dir)
    else:
        print("DRY RUN:", " ".join(command), f"(cwd={live_dir})")


def scale_preview_deployments(action: str, apply: bool) -> None:
    namespaces = get_namespaces()
    for namespace in namespaces:
        name = namespace.get("metadata", {}).get("name", "")
        if not NAMESPACE_PATTERN.match(name):
            continue

        result = run(["kubectl", "get", "deployments", "-n", name, "-o", "json"], check=False)
        if result.returncode != 0:
            continue

        deployments = json.loads(result.stdout).get("items", [])
        for deployment in deployments:
            deployment_name = deployment["metadata"]["name"]
            annotations = deployment["metadata"].get("annotations", {})
            current_replicas = deployment.get("spec", {}).get("replicas", 1)

            if action == "scale-down":
                commands = [
                    [
                        "kubectl",
                        "annotate",
                        "deployment",
                        deployment_name,
                        f"eee.io/original-replicas={current_replicas}",
                        "--overwrite",
                        "-n",
                        name,
                    ],
                    ["kubectl", "scale", "deployment", deployment_name, "--replicas=0", "-n", name],
                ]
            else:
                replicas = annotations.get("eee.io/original-replicas", "1")
                commands = [
                    ["kubectl", "scale", "deployment", deployment_name, f"--replicas={replicas}", "-n", name],
                    ["kubectl", "annotate", "deployment", deployment_name, "eee.io/original-replicas-", "-n", name],
                ]

            for command in commands:
                if apply:
                    run(command, check=False)
                else:
                    print("DRY RUN:", " ".join(command))


def smart_scale_action(timezone: str) -> str:
    now = utc_now().astimezone(ZoneInfo(timezone))
    if now.weekday() == 4 and now.hour >= 19:
        return "scale-down"
    if now.weekday() in {5, 6}:
        return "scale-down"
    if now.weekday() == 0 and 8 <= now.hour < 12:
        return "scale-up"
    return "none"


def ollama_scale_action(timezone: str, usage_file: Path | None) -> str | None:
    endpoint = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434/api/chat")
    model = os.environ.get("OLLAMA_MODEL", "llama3.1")
    usage = {}
    if usage_file and usage_file.exists():
        usage = json.loads(usage_file.read_text(encoding="utf-8"))

    prompt = {
        "instruction": "Return exactly one token: scale-down, scale-up, or none.",
        "policy": "Scale down after 7 PM Friday and through weekends. Scale back up Monday morning. Prefer none during active working hours.",
        "timezone": timezone,
        "current_time": utc_now().astimezone(ZoneInfo(timezone)).isoformat(),
        "usage": usage,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(
            {
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": "You decide preview environment scaling actions."},
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError):
        return None

    action = body.get("message", {}).get("content", "").strip().lower()
    if action in {"scale-down", "scale-up", "none"}:
        return action
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean stale EEE preview environments.")
    parser.add_argument("--repo", default="simxr/Ephemeral-Environment-Engine", help="GitHub repo in owner/name form.")
    parser.add_argument("--max-age-hours", type=float, default=24, help="Delete previews older than this age.")
    parser.add_argument("--apply", action="store_true", help="Perform deletes and destroys. Default is dry-run.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--smart-scale", action="store_true", help="Scale preview deployments based on local work-week policy.")
    parser.add_argument("--timezone", default=os.environ.get("EEE_TIMEZONE", "Asia/Kolkata"))
    parser.add_argument("--scaler-provider", default=os.environ.get("EEE_SCALER_PROVIDER", "policy"), choices=["policy", "ollama"])
    parser.add_argument("--usage-file", type=Path, default=None)
    args = parser.parse_args()

    if args.smart_scale:
        action = None
        if args.scaler_provider == "ollama":
            action = ollama_scale_action(args.timezone, args.usage_file)
        if action is None:
            action = smart_scale_action(args.timezone)
        print(f"smart-scale action: {action}")
        if action in {"scale-down", "scale-up"}:
            scale_preview_deployments(action, args.apply)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    namespaces = get_namespaces()

    for namespace in namespaces:
        name = namespace.get("metadata", {}).get("name", "")
        match = NAMESPACE_PATTERN.match(name)
        if not match:
            continue

        delete, reason = should_delete(namespace, args.repo, args.max_age_hours, token)
        print(f"{name}: {reason}")
        if not delete:
            continue

        pr_number = match.group("number")
        delete_namespace(name, args.apply)
        destroy_terraform(args.repo_root, pr_number, args.apply)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr, file=sys.stderr)
        raise SystemExit(exc.returncode)
