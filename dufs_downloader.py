#!/usr/bin/env python3
"""
Dufs file download client.
Connects to a dufs server, lists files/folders, supports single file and recursive folder download.
"""

import os
import shutil
import sys
import subprocess
import json
import argparse
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def normalize_base_url(url: str) -> str:
    """Normalize base URL for direct use."""
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url


def fetch_json(base_url: str, path: str = "") -> dict:
    """Fetch directory listing in JSON format."""
    url = urljoin(base_url + "/", (path or ".").lstrip("/") + "/")
    if not url.endswith("/"):
        url += "/"
    url += "?json"
    req = Request(url)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_simple(base_url: str, path: str = "") -> list[tuple[str, bool]]:
    """Fetch directory listing in simple format (fallback), returns [(name, is_dir), ...]"""
    url = urljoin(base_url + "/", (path or ".").lstrip("/") + "/")
    if not url.endswith("/"):
        url += "/"
    url += "?simple"
    req = Request(url)
    with urlopen(req, timeout=30) as resp:
        lines = resp.read().decode().strip().split("\n")
    result = []
    for line in lines:
        if not line:
            continue
        is_dir = line.endswith("/")
        name = line.rstrip("/")
        result.append((name, is_dir))
    return result


def list_directory(base_url: str, path: str = "") -> list[tuple[str, bool]]:
    """List directory contents, returns [(name, is_dir), ...].
    Dufs JSON uses path_type: "Dir"|"SymlinkDir"|"File"|"SymlinkFile"
    """
    try:
        data = fetch_json(base_url, path)
        paths = data.get("paths", [])
        result = []
        for p in paths:
            name = p.get("name", "")
            if not name and "href" in p:
                href = p["href"].rstrip("/")
                name = href.split("/")[-1] if href else ""
            path_type = p.get("path_type", "")
            is_dir = str(path_type).endswith("Dir")  # Dir, SymlinkDir
            result.append((name, is_dir))
        return result
    except (KeyError, TypeError):
        return fetch_simple(base_url, path)


def get_remote_size(base_url: str, remote_path: str) -> int | None:
    """Get remote file size, returns None on failure."""
    url = urljoin(base_url + "/", remote_path.lstrip("/"))
    req = Request(url, method="HEAD")
    try:
        with urlopen(req, timeout=10) as resp:
            cl = resp.headers.get("Content-Length")
            return int(cl) if cl is not None else None
    except Exception:
        return None


def download_file(base_url: str, remote_path: str, local_path: Path) -> tuple[bool, bool]:
    """Download a single file. Skip if local file exists with same size.
    Returns (success, skipped). success=True means file is available (including skip case)."""
    url = urljoin(base_url + "/", remote_path.lstrip("/"))
    local_path = local_path.resolve()
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if local_path.exists() and local_path.is_file():
        remote_size = get_remote_size(base_url, remote_path)
        if remote_size is not None and remote_size >= 0 and local_path.stat().st_size == remote_size:
            return (True, True)

    if shutil.which("wget"):
        ret = subprocess.run(
            ["wget", "--show-progress", "-O", str(local_path), url],
            check=False,
        )
    elif shutil.which("curl"):
        ret = subprocess.run(
            ["curl", "-#", "-f", "-L", "-o", str(local_path), url],
            check=False,
        )
    else:
        req = Request(url)
        with urlopen(req, timeout=60) as resp:
            with open(local_path, "wb") as f:
                while chunk := resp.read(8192):
                    f.write(chunk)
        ret = subprocess.CompletedProcess([], 0)
    return (ret.returncode == 0, False)


def collect_files_recursive(base_url: str, remote_path: str) -> list[str]:
    """Recursively collect all file paths under a folder."""
    files = []
    items = list_directory(base_url, remote_path)
    for name, is_dir in items:
        if name in (".", ".."):
            continue
        child_path = f"{remote_path.rstrip('/')}/{name}" if remote_path else name
        if is_dir:
            files.extend(collect_files_recursive(base_url, child_path))
        else:
            files.append(child_path)
    return files


def download_folder(base_url: str, remote_path: str, local_base: Path) -> None:
    """Recursively download a folder."""
    files = collect_files_recursive(base_url, remote_path)
    folder_name = remote_path.rstrip("/").split("/")[-1] or "download"
    target_dir = local_base / folder_name
    prefix = remote_path.rstrip("/") + "/"
    print(f"Downloading {len(files)} file(s) to {target_dir}")
    for file_path in files:
        if file_path.startswith(prefix):
            rel = file_path[len(prefix) :]
        else:
            rel = file_path
        local_file = target_dir / rel
        try:
            ok, skipped = download_file(base_url, file_path, local_file)
            if ok:
                print(f"  {'⊙ skipped (exists)' if skipped else '✓'}: {local_file.name}")
            else:
                print(f"  ✗ failed: {file_path}")
        except Exception as e:
            print(f"  ✗ failed: {file_path}: {e}")


def is_directory(base_url: str, path: str) -> bool:
    """Check if path is a directory."""
    items = list_directory(base_url, path if "/" in path else "")
    if not path or path == "/":
        return True
    parent = "/".join(path.rstrip("/").split("/")[:-1])
    name = path.rstrip("/").split("/")[-1]
    parent_items = list_directory(base_url, parent) if parent else list_directory(base_url, "")
    for n, is_dir in parent_items:
        if n == name:
            return is_dir
    return False


def interactive_download(base_url: str, save_dir: Path) -> None:
    """Interactive download main loop."""
    current_path = ""
    while True:
        print("\n" + "=" * 50)
        print(f"Current path: /{current_path}" if current_path else "Current path: / (root)")
        print("=" * 50)

        try:
            items = list_directory(base_url, current_path)
        except Exception as e:
            print(f"Failed to list: {e}")
            return

        if not items:
            print("(empty directory)")
        else:
            for i, (name, is_dir) in enumerate(items, 1):
                icon = "[dir]" if is_dir else "[file]"
                print(f"  {i:3}. {icon} {name}")

        print("\nCommands:")
        print("  - number (e.g. 1): enter dir or download file")
        print("  - d+number (e.g. d1): download selected file or folder")
        print("  - .. or cd ..: go to parent directory")
        print("  - q or quit: exit")
        print()

        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return

        if not user_input:
            continue
        if user_input.lower() in ("q", "quit", "exit"):
            print("Bye!")
            return

        if user_input in ("..", "cd .."):
            if current_path:
                parts = current_path.rstrip("/").split("/")
                current_path = "/".join(parts[:-1]) if len(parts) > 1 else ""
            continue

        force_download = user_input.lower().startswith("d") and user_input[1:].strip().isdigit()
        if force_download:
            user_input = user_input[1:].strip()

        if user_input.isdigit():
            idx = int(user_input)
            if 1 <= idx <= len(items):
                name, is_dir = items[idx - 1]
                target_path = f"{current_path}/{name}".strip("/") if current_path else name
                if is_dir and not force_download:
                    current_path = target_path
                else:
                    try:
                        if is_dir:
                            download_folder(base_url, target_path, save_dir)
                        else:
                            local_file = save_dir / name
                            ok, skipped = download_file(base_url, target_path, local_file)
                            if ok:
                                print(f"{'Skipped (exists)' if skipped else 'Downloaded'}: {local_file}")
                            else:
                                print(f"Download failed: {target_path}")
                    except Exception as e:
                        print(f"Download failed: {e}")
            else:
                print("Invalid number")
            continue

        name = user_input
        target_path = f"{current_path}/{name}".strip("/") if current_path else name
        matched = [(n, d) for n, d in items if n == name]
        if not matched:
            print("Not found")
            continue
        _, is_dir = matched[0]
        if is_dir:
            current_path = target_path
        else:
            try:
                local_file = save_dir / name
                ok, skipped = download_file(base_url, target_path, local_file)
                if ok:
                    print(f"{'Skipped (exists)' if skipped else 'Downloaded'}: {local_file}")
                else:
                    print(f"Download failed: {target_path}")
            except Exception as e:
                print(f"Download failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Dufs file download client")
    parser.add_argument(
        "url",
        nargs="?",
        default=os.environ.get("DUFS_URL", "http://localhost:6008"),
        help="Dufs server URL (e.g. http://192.168.1.100:6008)",
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Download save directory (default: script directory)",
    )
    args = parser.parse_args()

    base_url = normalize_base_url(args.url)
    save_dir = args.dir.resolve()
    save_dir.mkdir(parents=True, exist_ok=True)

    print("Dufs download client")
    print(f"Server: {base_url}")
    print(f"Save dir: {save_dir}")
    print()

    try:
        list_directory(base_url, "")
    except Exception as e:
        print(f"Cannot connect to server {base_url}: {e}")
        print("Check server address, port and network connection")
        sys.exit(1)

    interactive_download(base_url, save_dir)


if __name__ == "__main__":
    main()
