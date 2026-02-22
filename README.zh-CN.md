# Dufs 下载客户端

[English](README.md) | 中文

轻量级 Python 客户端，用于从 [dufs](https://github.com/sigoden/dufs) 文件服务器下载文件。可交互式浏览远程目录，下载单个文件，或递归下载整个文件夹。

## 功能

- **交互式浏览** — 列出文件与文件夹，进入子目录，返回上级目录
- **单文件下载** — 下载单个文件，显示进度与速度
- **递归文件夹下载** — 下载整棵目录树，保持目录结构
- **跳过已存在文件** — 下载前检查本地是否已有同大小文件，有则跳过
- **下载速度显示** — 优先使用 wget，其次 curl（若已安装）显示进度与速度

## 环境要求

- Python >= 3.10（仅用标准库，无需额外依赖）
- **推荐：** 已安装 `wget` 或 `curl`（用于下载时显示进度与速度）

## 使用方式

```bash
python dufs_downloader.py [URL] [--dir PATH]
```

**参数说明：**

| 参数 | 说明 |
|------|------|
| `URL` | dufs 服务器完整地址（含端口），如 `http://192.168.1.100:6008`。默认：`http://localhost:6008` |
| `--dir`, `-d` | 保存下载文件的本地目录。默认：脚本所在目录 |

**示例：**

```bash
# 连接本地 dufs 服务（默认端口 6008）
python dufs_downloader.py

# 指定完整 URL
python dufs_downloader.py http://192.168.1.100:6008

# 指定下载目录
python dufs_downloader.py http://example.com:6008 --dir ~/Downloads
```

## 环境变量

- `DUFS_URL` — 未在命令行指定 URL 时使用的默认服务器地址（如 `export DUFS_URL=http://my-server:6008`）

## 交互命令

| 输入 | 操作 |
|------|------|
| `1`, `2`, … | 进入目录（若为目录）或下载文件（若为文件） |
| `d1`, `d2`, … | 强制下载所选项目（文件或文件夹） |
| `dirname` | 按名称进入子目录或下载文件 |
| `..` 或 `cd ..` | 返回上级目录 |
| `q` 或 `quit` | 退出 |

## 兼容性

适用于任意 [dufs](https://github.com/sigoden/dufs) 服务端。启动 dufs 示例：

```bash
dufs -A -p 6008
```

（`-A` 允许所有操作，`-p 6008` 指定端口）
