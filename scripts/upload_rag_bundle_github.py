"""
Upload production RAG bundle zip to a GitHub Release (asset URL for RAG_ARTIFACT_BUNDLE_URL).

Requires GITHUB_TOKEN with permission to create releases and upload assets:
  - Classic PAT: scope ``repo`` (full control of private repositories)
  - Fine-grained PAT: Repository ``Contents`` = Read and write, repo = unutrip_v2

Usage:
  set GITHUB_TOKEN=ghp_...
  python scripts/upload_rag_bundle_github.py --check
  python scripts/upload_rag_bundle_github.py
  python scripts/upload_rag_bundle_github.py --use-gh
"""

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
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = ROOT / "backend" / "rag" / "dist" / "unutrip-rag-artifacts-prod.zip"
API_VERSION = "2022-11-28"

PERM_HELP = """
GitHub returned 403 — token cannot CREATE releases or upload assets.

Fix (pick one):

  A) Classic PAT (recommended for personal repos)
     https://github.com/settings/tokens/new
     - Expiration: as you prefer
     - Scopes: check "repo" (Full control of private repositories)
     - Token starts with ghp_

  B) Fine-grained PAT
     https://github.com/settings/personal-access-tokens?type=beta
     - Repository access: Only "unutrip_v2" (or this repository)
     - Repository permissions -> Contents: Read and write  (NOT read-only)
     - Token starts with github_pat_

Then:
  $env:GITHUB_TOKEN = "ghp_...."
  python scripts/upload_rag_bundle_github.py --check
  python scripts/upload_rag_bundle_github.py

Or upload manually (no token write needed):
  https://github.com/hoanglong13gnol/unutrip_v2/releases/new
  Attach: backend/rag/dist/unutrip-rag-artifacts-prod.zip
"""


def _request(
    method: str,
    url: str,
    token: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[dict, dict[str, str]]:
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
    }
    if headers:
        hdrs.update(headers)
    if data is not None and "Content-Type" not in hdrs:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            parsed = json.loads(body) if body else {}
            return parsed, resp_headers
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} {method} {url}: {detail}") from exc


def _parse_remote(remote: str) -> tuple[str, str]:
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote)
    if not m:
        raise ValueError(f"Cannot parse GitHub owner/repo from: {remote}")
    return m.group(1), m.group(2)


def _git_remote_url(remote: str) -> str:
    return subprocess.check_output(
        ["git", "remote", "get-url", remote],
        cwd=ROOT,
        text=True,
    ).strip()


def _token_hint(token: str) -> str:
    if token.startswith("github_pat_"):
        return "fine-grained (github_pat_*)"
    if token.startswith("ghp_"):
        return "classic (ghp_*)"
    return "unknown type"


def check_token_permissions(token: str, owner: str, repo: str) -> bool:
    print(f"Token type: {_token_hint(token)}")

    _, headers = _request("GET", "https://api.github.com/user", token)
    scopes = headers.get("x-oauth-scopes", "")
    if scopes:
        print(f"OAuth scopes (classic): {scopes}")
        if "repo" not in scopes and "public_repo" not in scopes:
            print("WARN: classic token missing 'repo' scope")

    _request("GET", f"https://api.github.com/repos/{owner}/{repo}/releases", token)
    print("OK  list releases (read)")

    test_tag = f"rag-perm-check-{uuid.uuid4().hex[:8]}"
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    payload = json.dumps(
        {
            "tag_name": test_tag,
            "name": "permission check (delete me)",
            "body": "Automated token check from upload_rag_bundle_github.py",
            "draft": True,
            "prerelease": True,
            "target_commitish": "master",
        }
    ).encode("utf-8")
    try:
        release, _ = _request("POST", url, token, data=payload)
    except RuntimeError as exc:
        if "403" in str(exc):
            print("FAIL create release (write) — this is why upload fails.")
            print(PERM_HELP)
            return False
        raise

    release_id = release.get("id")
    print(f"OK  create draft release (write) id={release_id}")

    if release_id:
        del_url = f"https://api.github.com/repos/{owner}/{repo}/releases/{release_id}"
        try:
            _request("DELETE", del_url, token)
            print("OK  deleted permission-check release")
        except RuntimeError:
            print(f"WARN: delete test release manually: tag {test_tag}")

    return True


def _get_release_by_tag(token: str, owner: str, repo: str, tag: str) -> dict | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    try:
        release, _ = _request("GET", url, token)
        return release
    except RuntimeError as exc:
        if "404" in str(exc):
            return None
        raise


def _create_release(token: str, owner: str, repo: str, tag: str, title: str, body: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    payload = json.dumps(
        {
            "tag_name": tag,
            "name": title,
            "body": body,
            "draft": False,
            "prerelease": True,
            "target_commitish": "master",
        }
    ).encode("utf-8")
    release, _ = _request("POST", url, token, data=payload)
    return release


def _upload_asset(token: str, upload_url: str, zip_path: Path) -> dict:
    name = zip_path.name
    url = upload_url.replace("{?name,label}", f"?name={name}")
    data = zip_path.read_bytes()
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/zip",
            "Content-Length": str(len(data)),
            "X-GitHub-Api-Version": API_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Upload failed {exc.code}: {detail}") from exc


def _find_gh() -> str | None:
    for name in ("gh", "gh.exe"):
        path = shutil.which(name)
        if path:
            return path
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidate = Path(program_files) / "GitHub CLI" / "gh.exe"
    if candidate.is_file():
        return str(candidate)
    return None


def upload_via_gh(
    token: str,
    owner: str,
    repo: str,
    tag: str,
    zip_path: Path,
    title: str,
    body: str,
) -> str:
    gh = _find_gh()
    if not gh:
        raise RuntimeError("gh CLI not found; install GitHub CLI or use API upload")

    full_repo = f"{owner}/{repo}"
    env = {**os.environ, "GH_TOKEN": token, "GITHUB_TOKEN": token}

    subprocess.run(
        [
            gh,
            "release",
            "create",
            tag,
            str(zip_path),
            "--repo",
            full_repo,
            "--prerelease",
            "--title",
            title,
            "--notes",
            body,
        ],
        check=True,
        env=env,
        cwd=ROOT,
    )

    out = subprocess.check_output(
        [gh, "release", "view", tag, "--repo", full_repo, "--json", "assets"],
        text=True,
        env=env,
    )
    assets = json.loads(out).get("assets", [])
    for asset in assets:
        if asset.get("name") == zip_path.name:
            return asset.get("browser_download_url", "")
    raise RuntimeError("Release created but asset URL not found")


def upload_via_api(
    token: str,
    owner: str,
    repo: str,
    tag: str,
    zip_path: Path,
    title: str,
    body: str,
) -> str:
    release = _get_release_by_tag(token, owner, repo, tag)
    if release is None:
        try:
            release = _create_release(token, owner, repo, tag, title, body)
            print(f"Created release {tag}")
        except RuntimeError as exc:
            if "403" in str(exc):
                print(str(exc), file=sys.stderr)
                print(PERM_HELP, file=sys.stderr)
                sys.exit(1)
            raise
    else:
        print(f"Using existing release {tag} (id={release['id']})")

    asset = _upload_asset(token, release["upload_url"], zip_path)
    return str(asset.get("browser_download_url", ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    ap.add_argument("--tag", default="", help="Release tag (default: rag-artifacts-YYYY-MM-DD)")
    ap.add_argument("--remote", default="origin", help="Git remote name")
    ap.add_argument("--check", action="store_true", help="Only verify token can create releases")
    ap.add_argument("--use-gh", action="store_true", help="Use gh CLI instead of REST API")
    args = ap.parse_args()

    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("ERROR: set GITHUB_TOKEN", file=sys.stderr)
        print(PERM_HELP, file=sys.stderr)
        sys.exit(1)

    owner, repo = _parse_remote(_git_remote_url(args.remote))

    if args.check:
        ok = check_token_permissions(token, owner, repo)
        sys.exit(0 if ok else 1)

    zip_path = args.zip.resolve()
    if not zip_path.is_file():
        print(f"ERROR: zip not found: {zip_path}", file=sys.stderr)
        print("Run: .\\scripts\\publish_rag_bundle.ps1", file=sys.stderr)
        sys.exit(1)

    meta_path = zip_path.with_name(zip_path.name + ".RELEASE.json")
    doc_count = "?"
    zip_sha = "?"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        doc_count = meta.get("document_count", "?")
        zip_sha = str(meta.get("zip_sha256", "?"))[:16]
        if isinstance(doc_count, int) and doc_count < 100:
            print(
                f"WARN: zip has only {doc_count} documents — run publish_rag_bundle.ps1 without -SkipBuild",
                file=sys.stderr,
            )

    from datetime import date

    tag = args.tag.strip() or f"rag-artifacts-{date.today().isoformat()}"
    title = f"RAG artifacts ({doc_count} docs)"
    body = (
        f"Production BM25 bundle for UnuTrip RAG.\n\n"
        f"- Documents: {doc_count}\n"
        f"- SHA256: `{zip_sha}...`\n\n"
        f"Set `RAG_ARTIFACT_BUNDLE_URL` to the release asset URL."
    )

    if not check_token_permissions(token, owner, repo):
        sys.exit(1)

    if args.use_gh:
        browser_url = upload_via_gh(token, owner, repo, tag, zip_path, title, body)
    else:
        browser_url = upload_via_api(token, owner, repo, tag, zip_path, title, body)

    print(f"Uploaded: {zip_path.name}")
    print(f"browser_download_url={browser_url}")
    print("\nSet in deploy .env:")
    print(f"RAG_ARTIFACT_BUNDLE_URL={browser_url}")


if __name__ == "__main__":
    main()
