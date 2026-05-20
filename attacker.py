import time
import random
import json
import datetime

# --- CRITICAL COMMAND SET ---
CRITICAL_COMMANDS = [
    "cat /etc/passwd",
    "cat /etc/shadow",
    "sudo su",
    "su",
    "cd /root",
    "cat /root/secret.txt",
    "ls /root",
    "cat ~/.ssh/id_rsa",
    "cat /home/ubuntu/.bash_history"
]

# keep same risk logic as main.py
def detect_risk(cmd):
    if any(x in cmd for x in ["passwd", "shadow", "sudo", "su", ".ssh"]):
        return ["CRITICAL"]
    return ["LOW"]


print("🔥 Starting CRITICAL Attack Simulation...\n")

for i in range(8):  # number of attacker sessions
    print(f"[ATTACKER {i+1}] Starting session...")

    username = random.choice(["root", "admin", "ubuntu"])
    password = random.choice(["1234", "admin", "toor", "password"])

    print(f"[ATTACKER {i+1}] Login → {username}:{password}")

    entry = {
        "session_id": f"attacker-{i}",
        "ip": "127.0.0.1",
        "start_time": datetime.datetime.utcnow().isoformat(),
        "commands": []
    }

    # run multiple CRITICAL commands per session
    for _ in range(random.randint(4, 7)):
        cmd = random.choice(CRITICAL_COMMANDS)

        print(f"[ATTACKER {i+1}] Running → {cmd}")

        entry["commands"].append({
            "time": datetime.datetime.utcnow().isoformat(),
            "command": cmd,
            "risk": detect_risk(cmd)
        })

        time.sleep(0.4)

    # write to log (dashboard will pick this up)
    with open("honeypot_log.json", "a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"[ATTACKER {i+1}] Session complete\n")
    time.sleep(0.8)

print("✅ CRITICAL attack simulation completed")