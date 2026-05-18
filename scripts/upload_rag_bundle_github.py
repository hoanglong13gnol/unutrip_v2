"""
Upload production RAG bundle zip to a GitHub Release (asset URL for RAG_ARTIFACT_BUNDLE_URL).

Requires: GITHUB_TOKEN (classic PAT or fine-grained with Contents: Read and write)
Scope: repo releases.

Usage:
  set GITHUB_TOKEN=ghp_...
  python scripts/upload_rag_bundle_github.py
  python scripts/upload_rag_bundle_github.py --zip backend/rag/dist/unutrip-rag-artifacts-prod.zip --tag rag-artifacts-2026-05-19
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = ROOT / "backend" / "rag" / "dist" / "unutrip-rag-artifacts-prod.zip"
API_VERSION = "2022-11-28"


def _request(
    method: str,
    url: str,
    token: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> dict:
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
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} {method} {url}: {detail}") from exc


def _parse_remote(remote: str) -> tuple[str, str]:
    # https://github.com/owner/repo.git
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote)
    if not m:
        raise ValueError(f"Cannot parse GitHub owner/repo from: {remote}")
    return m.group(1), m.group(2)


def _get_release_by_tag(token: str, owner: str, repo: str, tag: str) -> dict | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    try:
        return _request("GET", url, token)
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
        }
    ).encode("utf-8")
    return _request("POST", url, token, data=payload)


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    ap.add_argument("--tag", default="", help="Release tag (default: rag-artifacts-YYYY-MM-DD)")
    ap.add_argument("--remote", default="origin", help="Git remote name")
    args = ap.parse_args()

    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("ERROR: set GITHUB_TOKEN (repo scope, Contents read/write)", file=sys.stderr)
        sys.exit(1)

    zip_path = args.zip.resolve()
    if not zip_path.is_file():
        print(f"ERROR: zip not found: {zip_path}", file=sys.stderr)
        print("Run: .\\scripts\\publish_rag_bundle.ps1", file=sys.stderr)
        sys.exit(1)

    import subprocess

    remote_url = subprocess.check_output(
        ["git", "remote", "get-url", args.remote],
        cwd=ROOT,
        text=True,
    ).strip()
    owner, repo = _parse_remote(remote_url)

    meta_path = zip_path.with_name(zip_path.name + ".RELEASE.json")
    doc_count = "?"
    zip_sha = "?"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        doc_count = meta.get("document_count", "?")
        zip_sha = meta.get("zip_sha256", "?")[:16]

    from datetime import UTC, date

    tag = args.tag.strip() or f"rag-artifacts-{date.today().isoformat()}"
    title = f"RAG artifacts ({doc_count} docs)"
    body = (
        f"Production BM25 bundle for UnuTrip RAG.\n\n"
        f"- Documents: {doc_count}\n"
        f"- SHA256: `{zip_sha}...`\n\n"
        f"Deploy:\n"
        f"```env\nRAG_ARTIFACT_BUNDLE_URL=<browser_download_url below>\n```\n"
    )

    release = _get_release_by_tag(token, owner, repo, tag)
    if release is None:
        release = _create_release(token, owner, repo, tag, title, body)
        print(f"Created release {tag}")
    else:
        print(f"Using existing release {tag} (id={release['id']})")

    upload_url = release["upload_url"]
    asset = _upload_asset(token, upload_url, zip_path)
    browser_url = asset.get("browser_download_url", "")
    print(f"Uploaded: {asset.get('name')} ({asset.get('size')} bytes)")
    print(f"browser_download_url={browser_url}")
    print("\nSet in deploy .env:")
    print(f"RAG_ARTIFACT_BUNDLE_URL={browser_url}")


if __name__ == "__main__":
    main()
