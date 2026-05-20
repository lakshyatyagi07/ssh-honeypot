from flask import Flask, render_template, jsonify, Response
import json, time
from collections import defaultdict, Counter

app = Flask(__name__)

# ---------------- LOAD LOGS ----------------
def load_logs():
    logs = []
    try:
        with open("honeypot_log.json") as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    continue
    except:
        pass
    return logs


# ---------------- BUILD EVENTS (FIXED FOR YOUR FORMAT) ----------------
def build_events():
    logs = load_logs()
    events = []

    for session in logs:
        ip = session.get("ip", "unknown")

        for cmd in session.get("commands", []):
            risk = cmd.get("risk", [])

            if "CRITICAL" in risk:
                level = "CRITICAL"
            elif "HIGH" in risk:
                level = "HIGH"
            elif "MEDIUM" in risk:
                level = "MEDIUM"
            else:
                level = "LOW"

            score = {
                "LOW": 10,
                "MEDIUM": 40,
                "HIGH": 70,
                "CRITICAL": 90
            }[level]

            events.append({
                "timestamp": cmd.get("time"),
                "ip": ip,
                "port": 22,
                "service": "SSH",
                "threat_level": level,
                "threat_score": score,
                "message": cmd.get("command")
            })

    return events


# ---------------- STATS ----------------
def compute_stats(events):
    threat_counts = Counter()
    port_counts = Counter()
    hourly = defaultdict(int)
    ip_score = defaultdict(int)
    ip_conn = Counter()

    for e in events:
        threat_counts[e["threat_level"]] += 1
        port_counts[e["port"]] += 1
        ip_conn[e["ip"]] += 1
        ip_score[e["ip"]] += e["threat_score"]

        if e["timestamp"]:
            hour = e["timestamp"][:13]
            hourly[hour] += 1

    top_threats = [
        {
            "ip": ip,
            "score": ip_score[ip],
            "connections": ip_conn[ip]
        }
        for ip in ip_score
    ]

    top_threats = sorted(top_threats, key=lambda x: x["score"], reverse=True)[:5]

    return {
        "total_attacks": len(events),
        "unique_ips": len(ip_conn),
        "critical_count": threat_counts["CRITICAL"],
        "threat_counts": dict(threat_counts),
        "port_counts": dict(port_counts),
        "hourly_counts": dict(hourly),
        "top_threats": top_threats
    }


# ---------------- AI ANALYSIS ----------------
def compute_ai(events):
    ip_data = defaultdict(lambda: {"cmds": [], "score": [], "count": 0})

    for e in events:
        ip = e["ip"]
        ip_data[ip]["cmds"].append(e["message"])
        ip_data[ip]["score"].append(e["threat_score"])
        ip_data[ip]["count"] += 1

    results = []

    for ip, d in ip_data.items():
        insights = []

        if d["count"] > 5:
            insights.append("High-frequency activity")

        if any("shadow" in c for c in d["cmds"]):
            insights.append("Credential access attempt")

        if any("sudo" in c for c in d["cmds"]):
            insights.append("Privilege escalation")

        if any("wget" in c for c in d["cmds"]):
            insights.append("Malware download")

        if not insights:
            insights.append("Normal behavior")

        results.append({
            "ip": ip,
            "max_score": max(d["score"]),
            "connections": d["count"],
            "insights": insights
        })

    return sorted(results, key=lambda x: x["max_score"], reverse=True)[:8]


# ---------------- TOP COMMANDS ----------------
@app.route("/api/top_commands")
def top_commands():
    logs = load_logs()
    counter = Counter()

    for session in logs:
        for cmd in session.get("commands", []):
            counter[cmd.get("command")] += 1

    return jsonify(counter.most_common(10))


# ---------------- GEO ----------------
@app.route("/api/geo")
def geo_api():
    logs = load_logs()
    geo = []

    for session in logs:
        g = session.get("geo", {})
        geo.append({
            "ip": session.get("ip"),
            "country": g.get("country"),
            "city": g.get("city"),
            "org": g.get("isp"),
            "lat": g.get("lat") or 0,
            "lng": g.get("lon") or 0,
            "threat_level": "HIGH",
            "threat_score": 60,
            "connections": len(session.get("commands", []))
        })

    return jsonify(geo)


# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/logs")
def logs_api():
    return jsonify(build_events())


@app.route("/api/stats")
def stats_api():
    return jsonify(compute_stats(build_events()))


@app.route("/api/ai_analysis")
def ai_api():
    return jsonify(compute_ai(build_events()))


# ---------------- LIVE STREAM ----------------
@app.route("/api/stream")
def stream():
    def generate():
        last = 0
        while True:
            events = build_events()

            if len(events) > last:
                for e in events[last:]:
                    yield f"data: {json.dumps(e)}\n\n"
                last = len(events)

            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)