from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
import requests, re, os, json

app = Flask(__name__, static_folder="static")
KEY = os.environ.get("KEY") or open("key.txt").read().strip()
URL = "https://app.ai-grid.io/v1/chat/completions"
MODEL = "google/gemma-4-31B"
BAD = {"fuck","shit","bitch","merde","putain","connard"}
H = lambda: {"Content-Type": "application/json", "Authorization": "Bearer " + KEY}

def is_bad(t):
    return bool(BAD & set(re.findall(r"\w+", t.lower())))

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/sw.js")
def sw():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")

def clean(m):
    c = m.get("content", "")
    if isinstance(c, list):
        parts = []
        for p in c:
            if p.get("type") == "text":
                parts.append({"type": "text", "text": str(p.get("text", ""))})
            elif p.get("type") == "image_url":
                u = (p.get("image_url") or {}).get("url", "")
                if u.startswith("data:image/") and len(u) < 3_000_000:
                    parts.append({"type": "image_url", "image_url": {"url": u}})
        c = parts
    return {"role": m.get("role", "user"), "content": c}

def text_of(c):
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if p.get("type") == "text")
    return c or ""

def get_msgs():
    msgs = [clean(m) for m in (request.json or {}).get("messages", [])][-10:]
    return msgs, (text_of(msgs[-1]["content"]) if msgs else "")

@app.route("/api/chat", methods=["POST"])
def chat():
    msgs, last = get_msgs()
    if is_bad(last):
        return jsonify({"blocked": True})
    try:
        r = requests.post(URL, timeout=60, headers=H(),
            json={"model": MODEL, "messages": msgs, "max_tokens": 400, "temperature": 0.4})
        return jsonify({"reply": r.json()["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stream", methods=["POST"])
def stream():
    msgs, last = get_msgs()
    if is_bad(last):
        return jsonify({"blocked": True})
    def gen():
        try:
            with requests.post(URL, stream=True, timeout=60, headers=H(),
                json={"model": MODEL, "messages": msgs, "max_tokens": 400,
                      "temperature": 0.4, "stream": True}) as r:
                if r.status_code != 200:
                    yield "\x00ERR"; return
                r.encoding = "utf-8"
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    d = line[5:].strip()
                    if d == "[DONE]":
                        break
                    try:
                        c = json.loads(d)["choices"][0]["delta"].get("content")
                    except Exception:
                        continue
                    if c:
                        yield c
        except Exception:
            yield "\x00ERR"
    return Response(stream_with_context(gen()), mimetype="text/plain",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
