#!/usr/bin/env bash
# Run locally after inspecting this script and authenticating with gh auth login.
set -euo pipefail

repo_name="${1:-fundforge}"
if [[ ! "$repo_name" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo 'Repository name must use letters, numbers, dots, underscores or hyphens.' >&2
  exit 1
fi
command -v git >/dev/null || { echo 'Install Git first.' >&2; exit 1; }
command -v gh >/dev/null || { echo 'Install GitHub CLI first, then run gh auth login.' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'Run gh auth login first. Do not paste tokens into chat.' >&2; exit 1; }

package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$package_root"
owner="$(gh api user --jq '.login')"
owner_id="$(gh api user --jq '.id')"
if [[ -z "$owner" || ! "$owner_id" =~ ^[0-9]+$ ]]; then
  echo 'Unable to resolve authenticated GitHub identity.' >&2
  exit 1
fi
if gh repo view "$owner/$repo_name" >/dev/null 2>&1; then
  echo "Repository $owner/$repo_name already exists. Choose another name; nothing was overwritten." >&2
  exit 1
fi

existing_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$existing_root" && "$(cd "$existing_root" && pwd)" != "$package_root" ]]; then
  echo 'Package is inside another Git repository. Move it to a separate folder first.' >&2
  exit 1
fi
if [[ -z "$existing_root" ]]; then
  git init --initial-branch=main
fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'An origin remote already exists. Inspect it manually; this script does not replace remotes.' >&2
  exit 1
fi
if ! git diff --cached --quiet; then
  echo 'Existing staged changes detected. Resolve them before running this setup script.' >&2
  exit 1
fi
if [[ -z "$(git config user.name 2>/dev/null || true)" ]]; then
  git config --local user.name "$owner"
fi
if [[ -z "$(git config user.email 2>/dev/null || true)" ]]; then
  git config --local user.email "$owner_id+$owner@users.noreply.github.com"
fi

# Explicit package paths; do not git add arbitrary files such as a personal resume.
git add -- README.md CLAUDE.md .gitignore docs fixtures scripts .claude/agents
if ! git diff --cached --quiet; then
  git commit -m 'docs: add FundForge specification and Claude handoff'
fi
gh repo create "$owner/$repo_name" --private --source=. --remote=origin --push
privacy="$(gh repo view "$owner/$repo_name" --json isPrivate --jq '.isPrivate')"
if [[ "$privacy" != 'true' ]]; then
  echo 'Privacy verification failed. Inspect the remote manually; no visibility changes were attempted.' >&2
  exit 1
fi
gh repo view "$owner/$repo_name" --json nameWithOwner,isPrivate,url
