from flask import Flask, request, jsonify, send_from_directory
import requests, re, os

app = Flask(__name__, static_folder="static")
KEY = os.environ.get("KEY") or open("key.txt").read().strip()
URL = "https://app.ai-grid.io/v1/chat/completions"
BAD = {"fuck","shit","bitch","merde","putain","connard"}

def is_bad(t):
    return bool(BAD & set(re.findall(r"\w+", t.lower())))

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/sw.js")
def sw():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")

@app.route("/api/chat", methods=["POST"])
def chat():
    msgs = request.json.get("messages", [])
    last = msgs[-1]["content"] if msgs else ""
    if is_bad(last):
        return jsonify({"blocked": True})
    try:
        r = requests.post(URL, timeout=60,
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + KEY},
            json={"model": "google/gemma-4-31B",
                  "messages": msgs[-12:], "max_tokens": 500})
        return jsonify({"reply": r.json()["choices"][0]["message"]["content"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
