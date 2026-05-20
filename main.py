import datetime
import json
import os
import re
import time
import random

# ---------------- RISK DETECTION ----------------
RISK_PATTERNS = [
    ("CRITICAL", r"(passwd|shadow|/etc/passwd|/etc/shadow|\.ssh)"),
    ("CRITICAL", r"\b(sudo|su)\b"),
    ("HIGH",     r"\b(wget|curl)\b"),
    ("MEDIUM",   r"\b(ps|ifconfig|ip a)\b"),
]

def detect_risk(command):
    matches = []
    for level, pattern in RISK_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            matches.append(level)
    return matches


# ---------------- REALISTIC FILESYSTEM ----------------
fs = {
    "/": {
        "bin": {},
        "boot": {"vmlinuz": "", "initrd.img": ""},
        "dev": {"null": "", "tty": "", "random": ""},
        "etc": {
            "passwd": "root:x:0:0:root:/root:/bin/bash\nubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash",
            "shadow": "root:$6$hash\nubuntu:$6$hash",
            "hostname": "ubuntu-server\n",
            "hosts": "127.0.0.1 localhost\n192.168.1.10 server",
            "ssh": {
                "sshd_config": "PermitRootLogin yes\nPasswordAuthentication yes"
            }
        },
        "home": {
            "ubuntu": {
                "notes.txt": "TODO:\n- change password\n- backup server",
                "passwords.txt": "admin:admin123\nroot:toor",
                ".bash_history": "ls\ncat /etc/passwd\nsudo su",
                "project": {
                    "app.py": "print('Running app')"
                }
            }
        },
        "var": {
            "log": {
                "auth.log": "Failed password for root from 192.168.1.5",
                "syslog": "System boot complete"
            },
            "www": {
                "html": {
                    "index.html": "<h1>Company Portal</h1>",
                    "config.php": "$db_user='admin'; $db_pass='admin123';"
                }
            }
        },
        "tmp": {"temp.txt": ""},
        "usr": {"bin": {"python3": "", "bash": ""}},
        "root": {"secret.txt": "root password is toor"},
        "opt": {"scripts": {"backup.sh": "tar -czf backup.tar.gz"}},
    }
}

current_path = ["/", "home", "ubuntu"]
current_user = "ubuntu"

# ---------------- HELPERS ----------------
def get_current_dir():
    node = fs["/"]
    for p in current_path[1:]:
        node = node.get(p, {})
    return node

def get_path():
    if len(current_path) == 1:
        return "/"
    return "/" + "/".join(current_path[1:])


# ---------------- REAL-TIME LOGGING ----------------
def log_command(cmd):
    entry = {
        "session_id": "main-session",
        "ip": "127.0.0.1",
        "start_time": datetime.datetime.utcnow().isoformat(),
        "commands": [{
            "time": datetime.datetime.utcnow().isoformat(),
            "command": cmd,
            "risk": detect_risk(cmd)
        }]
    }

    with open("honeypot_log.json", "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------- COMMANDS ----------------
def cmd_ls():
    node = get_current_dir()
    print("  ".join(node.keys()))

def cmd_pwd():
    print(get_path())

def cmd_whoami():
    print(current_user)

def cmd_cd(arg):
    global current_path

    if arg == "/":
        current_path = ["/"]
        return

    if arg.startswith("/"):
        parts = [p for p in arg.split("/") if p]
        node = fs["/"]

        for p in parts:
            if p in node and isinstance(node[p], dict):
                node = node[p]
            else:
                print("cd: no such directory")
                return

        current_path = ["/"] + parts
        return

    if arg == "..":
        if len(current_path) > 1:
            current_path.pop()
        return

    node = get_current_dir()
    if arg in node and isinstance(node[arg], dict):
        current_path.append(arg)
    else:
        print("cd: no such directory")


# 🔥 FIXED CAT (ONLY CHANGE)
def cmd_cat(arg):
    if arg.startswith("/"):
        parts = [p for p in arg.split("/") if p]
        node = fs["/"]

        for p in parts[:-1]:
            if p in node and isinstance(node[p], dict):
                node = node[p]
            else:
                print("cat: no such file")
                return

        file_name = parts[-1]

        if file_name in node and isinstance(node[file_name], str):
            content = node[file_name]

            if ".bash_history" in file_name:
                content += "\nls\nwhoami\npwd\nsudo su"

            print(content)
        else:
            print("cat: no such file")

    else:
        node = get_current_dir()

        if arg in node and isinstance(node[arg], str):
            content = node[arg]

            if ".bash_history" in arg:
                content += "\nls\nwhoami\npwd\nsudo su"

            print(content)
        else:
            print("cat: no such file")


def cmd_ps():
    print("""USER       PID %CPU %MEM VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 168164 12048 ?        Ss   10:00   0:01 /sbin/init
root       500  0.0  0.1  72296  5428 ?        Ss   10:01   0:00 sshd
ubuntu    1200  0.0  0.1  10284  5544 pts/0    Ss   10:05   0:00 bash
""")

def cmd_ifconfig():
    print("""eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
inet 192.168.1.10  netmask 255.255.255.0
RX packets 123456  bytes 12345678
TX packets 654321  bytes 87654321
""")

def cmd_wget(url):
    print(f"--2026--  Connecting to {url}...")
    time.sleep(0.3)
    print("HTTP request sent, awaiting response... 200 OK")
    print("Length: 1024 (1.0K) [application/octet-stream]")
    print("Saving to: ‘payload.sh’\n")
    time.sleep(0.3)
    print("payload.sh        100%[===================>]   1.00K")
    print("Download completed.")


# ---------------- LOGIN ----------------
def login():
    print("Ubuntu 20.04.6 LTS\n")

    while True:
        username = input("username: ")
        password = input("password: ")

        log_command(f"LOGIN {username}:{password}")
        print("Login successful\n")
        return


# ---------------- MAIN LOOP ----------------
login()

while True:
    try:
        cmd = input(f"{current_user}@honeypot:{get_path()}$ ")

        if not cmd.strip():
            continue

        time.sleep(random.uniform(0.1, 0.3))
        log_command(cmd)

        parts = cmd.split()
        base = parts[0]

        if base == "ls":
            cmd_ls()
        elif base == "pwd":
            cmd_pwd()
        elif base == "whoami":
            cmd_whoami()
        elif base == "cd":
            if len(parts) > 1:
                cmd_cd(parts[1])
            else:
                print("cd: missing argument")
        elif base == "cat":
            if len(parts) > 1:
                cmd_cat(parts[1])
            else:
                print("cat: missing file")
        elif base == "ps":
            cmd_ps()
        elif base == "ifconfig":
            cmd_ifconfig()
        elif base == "wget":
            if len(parts) > 1:
                cmd_wget(parts[1])
            else:
                print("wget: missing URL")
        elif base == "sudo":
            print("[+] Privilege escalation successful (simulated)")
            current_user = "root"
        elif base == "exit":
            print("logout")
            break
        else:
            print(f"{base}: command not found")

    except KeyboardInterrupt:
        print("\nlogout")
        break