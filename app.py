#!/usr/bin/env python3
"""
Napoléon Imperial Web Reconnaissance & Intelligence Suite
Main Web Application Server
"""

import os
import sys
import json
import time
import queue
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from napoleon_service import NapoleonService

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

PORT = 5000
HOST = "127.0.0.1"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/campaign/start", methods=["POST"])
def start_campaign():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Target URL is required"}), 400

    service = NapoleonService.get_instance()
    res = service.start_campaign(data)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)


@app.route("/api/campaign/stop", methods=["POST"])
def stop_campaign():
    service = NapoleonService.get_instance()
    res = service.stop_campaign()
    return jsonify(res)


@app.route("/api/campaign/status", methods=["GET"])
def campaign_status():
    service = NapoleonService.get_instance()
    return jsonify(service.get_status())


@app.route("/api/campaign/data", methods=["GET"])
def campaign_data():
    service = NapoleonService.get_instance()
    return jsonify(service.get_campaign_data())


@app.route("/api/campaign/archives", methods=["GET"])
def campaign_archives():
    service = NapoleonService.get_instance()
    return jsonify(service.get_archives())


@app.route("/api/campaign/stream")
def campaign_stream():
    service = NapoleonService.get_instance()
    client_queue = service.subscribe()

    def event_stream():
        # First send recent log backlog so client connects with full context
        status = service.get_status()
        init_payload = {
            "event": "init",
            "status": status,
            "logs": status.get("recent_logs", [])
        }
        yield f"data: {json.dumps(init_payload)}\n\n"

        try:
            while True:
                try:
                    msg = client_queue.get(timeout=25.0)
                    yield f"data: {json.dumps(msg)}\n\n"
                except queue.Empty:
                    # Keepalive heartbeat
                    yield f": heartbeat\n\n"
        except GeneratorExit:
            service.unsubscribe(client_queue)

    return Response(event_stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    })


@app.route("/output/<path:filename>")
def download_output(filename):
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    return send_from_directory(output_dir, filename)


def open_browser():
    time.sleep(1.2)
    url = f"http://{HOST}:{PORT}"
    print(f"\n⚜️  Napoléon Imperial Suite launched at {url}")
    print("Opening browser automatically...\n")
    try:
        webbrowser.open_new_tab(url)
    except Exception:
        pass


if __name__ == "__main__":
    print("""
███╗   ██╗ █████╗ ██████╗  ██████╗ ██╗     ███████╗ ██████╗ ███╗   ██╗
████╗  ██║██╔══██╗██╔══██╗██╔═══██╗██║     ██╔════╝██╔═══██╗████╗  ██║
██╔██╗ ██║███████║██████╔╝██║   ██║██║     █████╗  ██║   ██║██╔██╗ ██║
██║╚██╗██║██╔══██║██╔═══╝ ██║   ██║██║     ██╔══╝  ██║   ██║██║╚██╗██║
██║ ╚████║██║  ██║██║     ╚██████╔╝███████╗███████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
    """)
    print("⚜️  Napoléon Imperial Web Reconnaissance & Intelligence Suite v2.0")
    print("⚜️  Server running at http://127.0.0.1:5000")
    print("⚜️  Press Ctrl+C to stop the imperial server.\n")

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
