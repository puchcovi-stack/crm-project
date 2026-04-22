#!/usr/bin/env python3
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    print("WEBHOOK CALLED!")  # это попадёт в journalctl
    payload = request.json
    print(f"Payload: {payload}")
    
    # Запускаем деплой
    subprocess.Popen(["/root/crm_project/deploy/deploy.sh"])
    
    return jsonify({"status": "ok"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000)
