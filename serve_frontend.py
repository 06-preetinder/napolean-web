#!/usr/bin/env python3
"""
Napoléon AI Launcher
Launches the full-fledged Imperial Web Application Suite.
"""
import sys
import subprocess
import os

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    print("⚜️ Launching Napoléon Imperial Web Intelligence Suite (app.py)...")
    try:
        subprocess.run([sys.executable, app_path])
    except KeyboardInterrupt:
        print("\n⚜️ Imperial Suite terminated.")

