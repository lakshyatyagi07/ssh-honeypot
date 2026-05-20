import json
import re
from datetime import datetime
import os
import requests

# ---------------- RISK PATTERNS ----------------
RISK_PATTERNS = [
    ("CRITICAL", r"(passwd|shadow|/etc/passwd|/etc/shadow|\.ssh|id_rsa)"),
    ("CRITICAL", r"\b(sudo|su|pkexec)\b"),
    ("HIGH",     r"\b(wget|curl|ftp)\b"),
    ("HIGH",     r"(nc|netcat|/dev/tcp|bash -i)"),
    ("MEDIUM",   r"\b(ps|top|netstat|ifconfig|ip a|uname|id)\b"),
    ("CRITICAL", r"(' OR '1'='1|--|select \* from|union select)"),
    ("HIGH",     r"(<script>|onerror=|alert\()"),
    ("HIGH",     r"(;|&&|\|\|)")
]

# ---------------- GEO LOOKUP ----------------
def get_geo(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        return {
            "country": res.get("country"),
            "city": res.get("city"),
            "isp": res.get("isp"),
            "lat": res.get("lat"),
            "lon": res.get("lon")
        }
    except:
        return {
            "country": None,
            "city": None,
            "isp": None,
            "lat": None,
            "lon": None
        }

# ---------------- SESSION TRACKER ----------------
class SessionTracker:
    def __init__(self, session_id, source_ip):
        self.session_id = session_id
        self.source_ip = source_ip
        self.start_time = datetime.utcnow().isoformat()
        self.geo = get_geo(source_ip)

    # ---------------- LOGIN RECORD ----------------
    def record_login(self, username, password):
        entry = {
            "time": datetime.utcnow().isoformat(),
            "command": f"LOGIN {username}:{password}",
            "risk": ["CRITICAL"],
            "attack_type": "BRUTE_FORCE"
        }

        self.write_event(entry)

    # ---------------- ATTACK TYPE ----------------
    def detect_attack_type(self, command):
        if re.search(r"(select|union|--|' OR)", command, re.IGNORECASE):
            return "SQL_INJECTION"
        elif re.search(r"(<script>|onerror=|alert\()", command, re.IGNORECASE):
            return "XSS"
        elif ";" in command or "&&" in command or "||" in command:
            return "COMMAND_INJECTION"
        elif "sudo" in command or "su" in command:
            return "PRIVILEGE_ESCALATION"
        elif "wget" in command or "curl" in command:
            return "MALWARE_DOWNLOAD"
        else:
            return "NORMAL"

    # ---------------- COMMAND RECORD ----------------
    def record(self, command):
        timestamp = datetime.utcnow().isoformat()

        matches = []
        for level, pattern in RISK_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                matches.append(level)

        entry = {
            "time": timestamp,
            "command": command,
            "risk": matches,
            "attack_type": self.detect_attack_type(command)
        }

        # 🔥 REAL-TIME WRITE
        self.write_event(entry)

    # ---------------- WRITE LOG ----------------
    def write_event(self, entry):
        log_entry = {
            "session_id": self.session_id,
            "ip": self.source_ip,
            "geo": self.geo,
            "start_time": self.start_time,
            "commands": [entry]   # keep same structure for dashboard compatibility
        }

        try:
            if not os.path.exists("honeypot_log.json"):
                open("honeypot_log.json", "w").close()

            with open("honeypot_log.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            print("[LOG ERROR]", e)