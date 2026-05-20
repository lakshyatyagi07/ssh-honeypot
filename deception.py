import random
import time

# ── 1. Fake system files ─────────────────────────

def install_fake_sensitive_files(fs_obj):
    fs = fs_obj.fs

    def set_file(path, content):
        parts = [p for p in path.split("/") if p]
        node = fs
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = content

    # passwd
    set_file("/etc/passwd",
        "root:x:0:0:root:/root:/bin/bash\n"
        "ubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash\n"
        "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
    )

    # shadow (fake hashes)
    set_file("/etc/shadow",
        "root:$6$randomhashroot:19000:0:99999:7:::\n"
        "ubuntu:$6$randomhashuser:19000:0:99999:7:::\n"
    )

    # hostname
    set_file("/etc/hostname", "ubuntu-server\n")

# ── 2. Command delay ─────────────────────────

def apply_command_delay(cmd):
    delays = {
        "ls": (0.05, 0.2),
        "cat": (0.05, 0.2),
        "ps": (0.1, 0.3),
        "ifconfig": (0.1, 0.3),
        "ip": (0.1, 0.3),
        "sudo": (0.5, 1.0),
        "wget": (0.5, 1.5),
        "default": (0.05, 0.2)
    }

    lo, hi = delays.get(cmd, delays["default"])
    time.sleep(random.uniform(lo, hi))

# ── 3. Fake sudo ─────────────────────────

def cmd_sudo(fs_obj, args):
    if not args:
        return "usage: sudo command\n"

    # fake password prompt (non-interactive)
    if random.random() < 0.2:
        return ""

    return "Sorry, try again.\n"

# ── 4. Fake ps ─────────────────────────

def cmd_ps(fs_obj, args):
    return """USER       PID %CPU %MEM VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 168164 12048 ?        Ss   10:00   0:01 /sbin/init
root       500  0.0  0.1  72296  5428 ?        Ss   10:01   0:00 sshd
ubuntu    1200  0.0  0.1  10284  5544 pts/0    Ss   10:05   0:00 bash
ubuntu    1250  0.0  0.1  12680  3276 pts/0    R+   10:06   0:00 ps
"""

# ── 5. Fake network ─────────────────────────

def cmd_ifconfig(fs_obj, args):
    return """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.2.15  netmask 255.255.255.0  broadcast 10.0.2.255
        RX packets 123456  bytes 12345678 (12.3 MB)
        TX packets 654321  bytes 87654321 (87.6 MB)
"""

def cmd_ip(fs_obj, args):
    return """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 10.0.2.15/24 brd 10.0.2.255 scope global eth0
"""