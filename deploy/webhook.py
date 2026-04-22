#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hmac
import hashlib
import subprocess
import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Путь к .env файлу
ENV_FILE = "/root/crm_project/.env"

def load_env():
    """Загружает переменные из .env файла"""
    env_vars = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    return env_vars

env = load_env()
WEBHOOK_SECRET = env.get("WEBHOOK_SECRET", "")

DEPLOY_SCRIPT = "/root/crm_project/deploy/deploy.sh"
LOG_FILE = "/root/crm_project/logs/webhook.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

@app.route("/webhook", methods=["POST"])
def webhook():
    # Проверяем подпись
    signature = request.headers.get("X-Hub-Signature-256")
    if signature:
        secret = WEBHOOK_SECRET.encode()
        digest = hmac.new(secret, request.data, hashlib.sha256).hexdigest()
        expected = f"sha256={digest}"
        if not hmac.compare_digest(signature, expected):
            log("❌ Неверная подпись вебхука")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403

    # Проверяем, что пуш был в ветку main
    payload = request.json
    if payload and "ref" in payload:
        if payload["ref"] != "refs/heads/main":
            log(f"ℹ️ Пропускаем пуш в ветку {payload['ref']}")
            return jsonify({"status": "skipped", "message": "Not main branch"}), 200

    log("🚀 Запускаю деплой...")
    
    # Запускаем скрипт деплоя в фоне
    subprocess.Popen([DEPLOY_SCRIPT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return jsonify({"status": "ok", "message": "Deploy started"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000)
