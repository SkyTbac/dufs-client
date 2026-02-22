# Dufs Download Client

[English](README.md) | [中文](README.zh-CN.md)

A lightweight Python client for downloading files from a [dufs](https://github.com/sigoden/dufs) file server. Browse the remote directory interactively, download single files, or recursively download entire folders.

## Features

- **Interactive browsing** — List files and folders, navigate into subdirectories, go back to parent
- **Single file download** — Download individual files with progress and speed display
- **Recursive folder download** — Download a whole directory tree, preserving structure
- **Skip existing files** — Before downloading, checks if the file already exists locally with the same size; skips if so
- **Download speed display** — Uses wget (preferred) or curl when available to show progress and speed

## Requirements

- Python >= 3.10 (standard library only, no extra packages)
- **Recommended:** `wget` or `curl` installed (for progress and speed display during download)

## Usage

```bash
python dufs_downloader.py [URL] [--dir PATH]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `URL` | Full dufs server URL including port (e.g. `http://192.168.1.100:6008`). Default: `http://localhost:6008` |
| `--dir`, `-d` | Local directory to save downloads. Default: script directory |

**Examples:**

```bash
# Connect to local dufs server (default port 6008)
python dufs_downloader.py

# Connect with full URL
python dufs_downloader.py http://192.168.1.100:6008

# Specify download directory
python dufs_downloader.py http://example.com:6008 --dir ~/Downloads
```

## Environment Variable

- `DUFS_URL` — Default server URL when not specified as argument (e.g. `export DUFS_URL=http://my-server:6008`)

## Interactive Commands

| Input | Action |
|-------|--------|
| `1`, `2`, … | Enter directory (if dir) or download file (if file) |
| `d1`, `d2`, … | Force download selected item (file or folder) |
| `dirname` | Enter subdirectory or download file by name |
| `..` or `cd ..` | Go to parent directory |
| `q` or `quit` | Exit |

## Compatibility

Works with any [dufs](https://github.com/sigoden/dufs) server. Start dufs with:

```bash
dufs -A -p 6008
```

(`-A` allows all operations, `-p 6008` sets the port)
