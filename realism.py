import random
from datetime import datetime, timedelta

# ── Metadata store ─────────────────────────────────────────

def _fake_mtime():
    days_ago = random.randint(0, 300)
    return datetime.now() - timedelta(days=days_ago)

def _ensure_meta(fs_obj, path, is_dir):
    if not hasattr(fs_obj, "meta"):
        fs_obj.meta = {}

    if path not in fs_obj.meta:
        fs_obj.meta[path] = {
            "mode": "drwxr-xr-x" if is_dir else "-rw-r--r--",
            "owner": "root" if path.startswith("/etc") else "ubuntu",
            "group": "root" if path.startswith("/etc") else "ubuntu",
            "size": random.randint(100, 5000) if not is_dir else 4096,
            "mtime": _fake_mtime()
        }
    return fs_obj.meta[path]

# ── Path helpers ─────────────────────────────────────────

def _abs(cwd, path):
    if not path.startswith("/"):
        path = cwd.rstrip("/") + "/" + path

    parts, stack = path.split("/"), []
    for p in parts:
        if p in ("", "."):
            continue
        elif p == "..":
            if stack:
                stack.pop()
        else:
            stack.append(p)

    return "/" + "/".join(stack)

def _get_node(fs, path):
    if path == "/":
        return fs

    node = fs
    for part in [p for p in path.split("/") if p]:
        if part not in node:
            return None
        node = node[part]
    return node

# ── ls ─────────────────────────────────────────

def cmd_ls(fs_obj, args):
    long_format = "-l" in args
    show_all = "-a" in args

    target = None
    for a in args:
        if not a.startswith("-"):
            target = a

    path = _abs(fs_obj.cwd, target) if target else fs_obj.cwd
    node = _get_node(fs_obj.fs, path)

    if node is None:
        return f"ls: cannot access '{target}': No such file or directory"

    if not isinstance(node, dict):
        return target

    entries = list(node.items())

    if long_format:
        lines = []
        for name, val in entries:
            full_path = path.rstrip("/") + "/" + name
            meta = _ensure_meta(fs_obj, full_path, isinstance(val, dict))

            time_str = meta["mtime"].strftime("%b %d %H:%M")
            lines.append(
                f"{meta['mode']} 1 {meta['owner']} {meta['group']} "
                f"{meta['size']} {time_str} {name}"
            )
        return "\n".join(lines)

    else:
        return "  ".join(name for name, _ in entries)

# ── cd ─────────────────────────────────────────

def cmd_cd(fs_obj, args):
    target = args[0] if args else fs_obj.home_dir

    new_path = _abs(fs_obj.cwd, target)
    node = _get_node(fs_obj.fs, new_path)

    if node is None:
        return f"cd: {target}: No such file or directory"
    if not isinstance(node, dict):
        return f"cd: {target}: Not a directory"

    fs_obj.cwd = new_path
    return ""

# ── pwd ─────────────────────────────────────────

def cmd_pwd(fs_obj, args):
    return fs_obj.cwd

# ── chmod (basic) ─────────────────────────────────────────

def cmd_chmod(fs_obj, args):
    if len(args) < 2:
        return "chmod: missing operand"

    mode, path = args[0], args[1]
    abs_path = _abs(fs_obj.cwd, path)

    node = _get_node(fs_obj.fs, abs_path)
    if node is None:
        return f"chmod: cannot access '{path}'"

    meta = _ensure_meta(fs_obj, abs_path, isinstance(node, dict))

    if mode.isdigit():
        perms = int(mode)
        mapping = {
            7: "rwx", 6: "rw-", 5: "r-x",
            4: "r--", 3: "-wx", 2: "-w-", 1: "--x", 0: "---"
        }
        u = mapping[int(mode[0])]
        g = mapping[int(mode[1])]
        o = mapping[int(mode[2])]

        prefix = "d" if isinstance(node, dict) else "-"
        meta["mode"] = prefix + u + g + o

    return ""