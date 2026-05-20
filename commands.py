# ── Path Helpers ─────────────────────────

def _abs(cwd, path):
    if not path.startswith("/"):
        path = cwd.rstrip("/") + "/" + path

    parts = path.split("/")
    stack = []

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


def _get_parent(fs, path):
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None, None

    parent_path = "/" + "/".join(parts[:-1])
    parent = _get_node(fs, parent_path or "/")
    return parent, parts[-1]


# ── Commands ─────────────────────────

def cmd_mkdir(fs_obj, args):
    for path in args:
        abs_path = _abs(fs_obj.cwd, path)
        parent, name = _get_parent(fs_obj.fs, abs_path)
        if parent is not None:
            parent[name] = {}
    return ""


def cmd_touch(fs_obj, args):
    for path in args:
        abs_path = _abs(fs_obj.cwd, path)
        parent, name = _get_parent(fs_obj.fs, abs_path)
        if parent is not None:
            parent[name] = ""
    return ""


def cmd_rm(fs_obj, args):
    for path in args:
        abs_path = _abs(fs_obj.cwd, path)
        parent, name = _get_parent(fs_obj.fs, abs_path)
        if parent and name in parent:
            del parent[name]
    return ""


def cmd_cp(fs_obj, args):
    if len(args) < 2:
        return "cp: missing file operand"

    src = _abs(fs_obj.cwd, args[0])
    dst = _abs(fs_obj.cwd, args[1])

    node = _get_node(fs_obj.fs, src)
    if node is None:
        return f"cp: cannot stat '{args[0]}'"

    parent, name = _get_parent(fs_obj.fs, dst)
    if parent is None:
        return f"cp: cannot create '{args[1]}'"

    # FIX: copy properly
    if isinstance(node, dict):
        parent[name] = node.copy()
    else:
        parent[name] = str(node)

    return ""


def cmd_mv(fs_obj, args):
    if len(args) < 2:
        return "mv: missing file operand"

    src = _abs(fs_obj.cwd, args[0])
    dst = _abs(fs_obj.cwd, args[1])

    node = _get_node(fs_obj.fs, src)
    if node is None:
        return f"mv: cannot stat '{args[0]}'"

    parent_src, name_src = _get_parent(fs_obj.fs, src)
    parent_dst, name_dst = _get_parent(fs_obj.fs, dst)

    if parent_dst is None:
        return f"mv: cannot move to '{args[1]}'"

    parent_dst[name_dst] = node

    if parent_src and name_src in parent_src:
        del parent_src[name_src]

    return ""


def cmd_cat(fs_obj, args):
    if not args:
        return "cat: missing file operand"

    path = args[0]
    abs_path = _abs(fs_obj.cwd, path)

    node = _get_node(fs_obj.fs, abs_path)

    if node is None:
        return f"cat: {path}: No such file or directory"

    if isinstance(node, dict):
        return f"cat: {path}: Is a directory"

    return node