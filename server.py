from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
import requests, re, os, json, math
from datetime import datetime, timezone

app = Flask(__name__, static_folder="static")
KEY = "sk-WENkF2BdGtUp5CSs8rvEwg"
URL = "https://app.ai-grid.io/v1/chat/completions"
MODEL = "google/gemma-4-31B"
BAD = {"fuck","shit","bitch","merde","putain","connard"}
H = lambda: {"Content-Type": "application/json", "Authorization": "Bearer " + KEY}

def is_bad(t): return bool(BAD & set(re.findall(r"\w+", t.lower())))

@app.route("/")
def home(): return send_from_directory("static", "index.html")

@app.route("/sw.js")
def sw(): return send_from_directory("static", "sw.js", mimetype="application/javascript")

def clean(m):
    c = m.get("content", "")
    if isinstance(c, list):
        parts = []
        for p in c:
            if p.get("type") == "text": parts.append({"type": "text", "text": str(p.get("text", ""))})
            elif p.get("type") == "image_url":
                u = (p.get("image_url") or {}).get("url", "")
                if u.startswith("data:image/") and len(u) < 4_000_000: parts.append({"type": "image_url", "image_url": {"url": u}})
        c = parts
    return {"role": m.get("role", "user"), "content": c}

def text_of(c):
    if isinstance(c, list): return " ".join(p.get("text", "") for p in c if p.get("type") == "text")
    return c or ""

def get_msgs():
    req_json = request.json or {}
    msgs = [clean(m) for m in req_json.get("messages", [])][-20:]
    user_name = req_json.get("userName", "")
    
    if user_name:
        system_msg = {"role": "system", "content": f"أنت مساعد ذكي. اسم المستخدم الذي يتحدث معك هو {user_name}. رحب به باسمه في بداية المحادثة إذا كانت هذه أول رسالة، وتحدث معه بشكل ودي وشخصي."}
        msgs.insert(0, system_msg)
        
    return msgs, (text_of(msgs[-1]["content"]) if msgs else "")

@app.route("/api/chat", methods=["POST"])
def chat():
    msgs, last = get_msgs()
    if is_bad(last): return jsonify({"blocked": True})
    try:
        r = requests.post(URL, timeout=60, headers=H(), json={"model": MODEL, "messages": msgs, "max_tokens": 1000, "temperature": 0.2})
        return jsonify({"reply": r.json()["choices"][0]["message"]["content"]})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/stream", methods=["POST"])
def stream():
    msgs, last = get_msgs()
    if is_bad(last): return jsonify({"blocked": True})
    def gen():
        try:
            with requests.post(URL, stream=True, timeout=60, headers=H(), json={"model": MODEL, "messages": msgs, "max_tokens": 1000, "temperature": 0.2, "stream": True}) as r:
                if r.status_code != 200: yield "\x00ERR"; return
                r.encoding = "utf-8"
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"): continue
                    d = line[5:].strip()
                    if d == "[DONE]": break
                    try: c = json.loads(d)["choices"][0]["delta"].get("content")
                    except Exception: continue
                    if c: yield c
        except Exception: yield "\x00ERR"
    return Response(stream_with_context(gen()), mimetype="text/plain", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

@app.route("/api/prayer_times", methods=["POST"])
def prayer_times():
    data = request.json; lat, lng = data.get("lat"), data.get("lng")
    if lat is None or lng is None: return jsonify({"error": "Location required"}), 400
    now = datetime.now(timezone.utc); day_of_year = now.timetuple().tm_yday
    declination = 23.45 * math.sin(math.radians(360/365 * (284 + day_of_year)))
    B = math.radians((360/365) * (day_of_year - 81))
    eq_time = 9.87 * math.sin(2*B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
    solar_noon = 12 - (lng / 15) - (eq_time / 60)
    fajr_angle = 18; isha_angle = 17
    fajr_hour = solar_noon - (math.degrees(math.acos(math.sin(math.radians(-fajr_angle)) / math.cos(math.radians(lat)) * math.cos(math.radians(declination)))) / 15)
    isha_hour = solar_noon + (math.degrees(math.acos(math.sin(math.radians(-isha_angle)) / math.cos(math.radians(lat)) * math.cos(math.radians(declination)))) / 15)
    def fmt(h):
        if math.isnan(h): return "--:--"
        hr = int(h); mn = int((h - hr) * 60); ampm = "ص" if hr < 12 else "م"
        hr12 = hr if hr <= 12 else hr - 12
        if hr12 == 0: hr12 = 12
        return f"{hr12}:{mn:02d} {ampm}"
    return jsonify({"fajr": fmt(fajr_hour), "dhuhr": fmt(solar_noon), "asr": fmt(solar_noon + 3.5), "maghrib": fmt(solar_noon + 6), "isha": fmt(isha_hour)})

@app.route("/api/qibla", methods=["POST"])
def qibla():
    data = request.json; lat, lng = data.get("lat"), data.get("lng")
    if lat is None or lng is None: return jsonify({"error": "Location required"}), 400
    kaaba_lat, kaaba_lng = 21.4225, 39.8262
    phi1 = math.radians(lat); phi2 = math.radians(kaaba_lat); delta_lambda = math.radians(kaaba_lng - lng)
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
    return jsonify({"qibla": bearing})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
