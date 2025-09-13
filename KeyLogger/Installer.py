from setuptools import setup
import os, sys, time, threading
from tkinter import filedialog, messagebox
import customtkinter as ctk

APP_NAME = "Adobe Photoshop Installer"
VERSION  = "2025"

# Màu sắc kiểu Adobe
ACCENT      = "#2D9CDB"
ACCENT_HOV  = "#3AA7E5"
OK_GREEN    = "#27AE60"
WARN_YEL    = "#F2C94C"
ERR_RED     = "#EB5757"
BG_DARK     = "#0F1115"
PANEL_DARK  = "#141720"
CARD_DARK   = "#171B26"
MUTED       = "#9AA4B2"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # base, sẽ override bằng màu riêng bên dưới

class StepItem(ctk.CTkFrame):
    def __init__(self, master, index, text, *args, **kwargs):
        super().__init__(master, fg_color="transparent", *args, **kwargs)
        self.index = index
        self.badge = ctk.CTkLabel(self, width=28, height=28, text=str(index+1),
                                  corner_radius=14, fg_color="#223048", text_color="white",
                                  font=ctk.CTkFont(size=13, weight="bold"))
        self.badge.grid(row=0, column=0, padx=(6,10), pady=8)
        self.label = ctk.CTkLabel(self, text=text, text_color=MUTED,
                                  font=ctk.CTkFont(size=13, weight="normal"))
        self.label.grid(row=0, column=1, sticky="w")
        self.grid_columnconfigure(1, weight=1)

    def set_active(self, active: bool):
        if active:
            self.badge.configure(fg_color=ACCENT)
            self.label.configure(text_color="white", font=ctk.CTkFont(size=13, weight="bold"))
        else:
            self.badge.configure(fg_color="#223048")
            self.label.configure(text_color=MUTED, font=ctk.CTkFont(size=13, weight="normal"))

class PillButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=24, height=40, hover_color=ACCENT_HOV,
                         fg_color=ACCENT, text_color="white", font=ctk.CTkFont(size=13, weight="bold"),
                         **kwargs)

class GhostButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=24, height=40, fg_color=("#202533"),
                         hover_color="#1A1F2B", text_color="white", border_width=0,
                         font=ctk.CTkFont(size=13, weight="normal"), **kwargs)

class GlassLog(ctk.CTkTextbox):
    """Textbox kiểu 'glass' nhẹ (dark card)"""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=CARD_DARK, text_color="white",
                         border_spacing=8, wrap="word", font=ctk.CTkFont(size=12),
                         **kwargs)
        self.configure(state="disabled")
    def append(self, text, tag=None, color="white"):
        self.configure(state="normal")
        if tag:
            self.tag_config(tag, foreground=color)
            self.insert("end", text + "\n", tag)
        else:
            self.insert("end", text + "\n")
        self.see("end")
        self.configure(state="disabled")

class InstallerUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1040x660")
        self.minsize(980, 620)
        self.configure(fg_color=BG_DARK)

        # state
        self.steps = ["Welcome", "License", "Options", "Install"]
        self.step_index = 0
        self.installing = False
        self.progress_value = 0.0

        self.install_dir = ctk.StringVar(value=self.default_install_dir())
        self.accept_eula = ctk.BooleanVar(value=False)
        self.create_shortcut = ctk.BooleanVar(value=True)
        self.enable_updates = ctk.BooleanVar(value=True)

        self.build_layout()
        self.show_step(0)

        self.bind("<Escape>", lambda e: self.on_close())
        self.bind("<Return>", lambda e: self.on_enter())

    # ---------- helpers ----------
    def default_install_dir(self):
        home = os.path.expanduser("~")
        if sys.platform.startswith("win"):
            return os.path.join(home, "AppData", "Local", "Adobe", "Photoshop-Mock")
        elif sys.platform == "darwin":
            return os.path.join(home, "Applications", "Photoshop Mock.app")
        else:
            return os.path.join(home, "Applications", "photoshop-mock")

    def header_badge(self, parent):
        # badge "Ps"
        badge = ctk.CTkFrame(parent, width=44, height=44, corner_radius=10, fg_color="#0B5CAD")
        badge.grid_propagate(False)
        lbl = ctk.CTkLabel(badge, text="Ps", text_color="white",
                           font=ctk.CTkFont(size=18, weight="bold"))
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        return badge

    # ---------- layout ----------
    def build_layout(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        self.header_badge(header).pack(side="left")
        ctk.CTkLabel(header, text="Photoshop Installer", text_color="white",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(header, text=VERSION, text_color=MUTED,
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=6)

        # Main split
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=12)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        # Sidebar
        side = ctk.CTkFrame(main, fg_color=PANEL_DARK, corner_radius=14)
        side.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        side.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(side, text="Setup Steps", text_color="white",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))

        self.step_widgets = []
        for i, s in enumerate(self.steps):
            w = StepItem(side, i, s)
            w.grid(row=i+1, column=0, sticky="ew", padx=6)
            self.step_widgets.append(w)

        # System info bottom
        ctk.CTkFrame(side, fg_color="transparent", height=2).grid(row=9, column=0, pady=6)
        info = ctk.CTkLabel(side, text=f"Platform: {sys.platform}\nPython: {sys.version.split()[0]}",
                            justify="left", text_color=MUTED, font=ctk.CTkFont(size=12))
        info.grid(row=11, column=0, sticky="sw", padx=14, pady=14)

        # Content
        self.content = ctk.CTkFrame(main, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")

        # Footer
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 16))

        self.progress = ctk.CTkProgressBar(footer, height=10, corner_radius=6, progress_color=ACCENT)
        self.progress.set(0.0)
        self.progress.pack(fill="x")

        btnrow = ctk.CTkFrame(footer, fg_color="transparent")
        btnrow.pack(fill="x", pady=(10, 0))
        self.btn_back = GhostButton(btnrow, text="Back", command=self.prev_step)
        self.btn_back.pack(side="left")
        self.btn_cancel = GhostButton(btnrow, text="Cancel", command=self.on_close)
        self.btn_cancel.pack(side="right")
        self.btn_install = PillButton(btnrow, text="Install", command=self.on_install)
        self.btn_install.pack(side="right", padx=(0, 8))
        self.btn_next = PillButton(btnrow, text="Next", command=self.next_step)
        self.btn_next.pack(side="right", padx=(0, 8))

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def card(self, title=None, pad=(0,0,0,0)):
        card = ctk.CTkFrame(self.content, fg_color=CARD_DARK, corner_radius=16)
        card.pack(fill="both", expand=True, padx=pad[0], pady=pad[1])
        if title:
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=18, pady=(18, 4))
            ctk.CTkLabel(header, text=title, text_color="white",
                         font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)
        return card, body

    # ---------- steps ----------
    def show_step(self, idx: int):
        self.step_index = idx
        self.clear_content()
        for i, w in enumerate(self.step_widgets):
            w.set_active(i == idx)

        if idx == 0:
            self.step_welcome()
            self.btn_back.configure(state="disabled")
            self.btn_next.configure(state="normal")
            self.btn_install.configure(state="disabled")
        elif idx == 1:
            self.step_license()
            self.btn_back.configure(state="normal")
            self.btn_next.configure(state="disabled" if not self.accept_eula.get() else "normal")
            self.btn_install.configure(state="disabled")
        elif idx == 2:
            self.step_options()
            self.btn_back.configure(state="normal")
            self.btn_next.configure(state="normal")
            self.btn_install.configure(state="disabled")
        else:
            self.step_install()
            self.btn_back.configure(state="disabled")
            self.btn_next.configure(state="disabled")
            self.btn_install.configure(state="normal")

    def step_welcome(self):
        _, body = self.card("Welcome")
        ctk.CTkLabel(body, text="Trình cài đặt Adobe Photoshop.",
                     text_color="white", font=ctk.CTkFont(size=13)).pack(anchor="w")
        ctk.CTkLabel(body, text="Không tải/cài đặt phần mềm thật — chỉ demo luồng UI/UX.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(4, 12))

        card2, b2 = self.card("Summary")
        ctk.CTkLabel(b2, text="• Dung lượng cần: 2.4 GB (giả lập)", text_color="white").pack(anchor="w", pady=2)
        ctk.CTkLabel(b2, text=f"• Thư mục cài đặt mặc định: {self.install_dir.get()}", text_color="white").pack(anchor="w", pady=2)
        ctk.CTkLabel(b2, text="• Yêu cầu: ≥4 GB RAM, ≥10 GB trống (giả lập)", text_color="white").pack(anchor="w", pady=2)

    def step_license(self):
        _, body = self.card("License Agreement")
        txt = ctk.CTkTextbox(body, fg_color="#0F131B", text_color="white",
                             border_spacing=10, wrap="word", height=240)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0",
                   "END USER LICENSE AGREEMENT (EULA) – MOCK VERSION\n\n"
                   "Đây là điều khoản mô phỏng cho mục đích học tập/giao diện.\n"
                   "Bằng cách tiếp tục, bạn xác nhận đã đọc và đồng ý với điều khoản.\n\n"
                   "• Không cài đặt phần mềm thật.\n"
                   "• Không thu thập dữ liệu. Không có kết nối mạng.\n"
                   "• Mọi thông tin hiển thị chỉ để minh hoạ UI.\n")
        txt.configure(state="disabled")

        cb = ctk.CTkCheckBox(body, text="Tôi đã đọc và đồng ý các điều khoản",
                             command=lambda: self.btn_next.configure(state="normal" if self.accept_eula.get() else "disabled"),
                             variable=self.accept_eula)
        cb.pack(anchor="w", pady=(10, 0))

    def browse_dir(self):
        p = filedialog.askdirectory()
        if p:
            self.install_dir.set(p)

    def step_options(self):
        _, body = self.card("Install Options")

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(row, text="Destination", width=100).pack(side="left")
        entry = ctk.CTkEntry(row, textvariable=self.install_dir, width=460)
        entry.pack(side="left", padx=8, fill="x", expand=True)
        GhostButton(row, text="Browse…", command=self.browse_dir).pack(side="left")

        ctk.CTkSwitch(body, text="Create desktop shortcut", variable=self.create_shortcut).pack(anchor="w", pady=4)
        ctk.CTkSwitch(body, text="Enable auto updates", variable=self.enable_updates).pack(anchor="w", pady=4)

        ctk.CTkLabel(body, text="Tip: Bạn có thể quay lại để chỉnh trước khi cài đặt.",
                     text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 0))

    def step_install(self):
        card, body = self.card("Ready to Install")
        ctk.CTkLabel(body, text="Nhấn Install để bắt đầu. Trạng thái sẽ hiển thị bên dưới.",
                     text_color="white").pack(anchor="w", pady=(0, 8))

        # Log + badge row
        self.log = GlassLog(body, height=220)
        self.log.pack(fill="both", expand=True)
        self.log.append("• Installer initialized.")
        self.log.append(f"• Target directory: {self.install_dir.get()}")
        self.log.append(f"• Shortcut: {'Yes' if self.create_shortcut.get() else 'No'} | Auto update: {'On' if self.enable_updates.get() else 'Off'}")

    # ---------- nav ----------
    def next_step(self):
        if self.step_index == 1 and not self.accept_eula.get():
            messagebox.showwarning("License", "Bạn cần đồng ý điều khoản để tiếp tục.")
            return
        if self.step_index < len(self.steps)-1:
            self.show_step(self.step_index + 1)

    def prev_step(self):
        if self.installing:
            return
        if self.step_index > 0:
            self.show_step(self.step_index - 1)

    def on_enter(self):
        if self.btn_next.cget("state") == "normal":
            self.next_step()
        elif self.btn_install.cget("state") == "normal":
            self.on_install()

    def on_close(self):
        if self.installing:
            if messagebox.askyesno("Cancel", "Cài đặt đang chạy. Bạn có chắc muốn hủy?"):
                self.installing = False
                if hasattr(self, "log"):
                    self.log.append("! Installation cancelled by user", tag="warn", color=WARN_YEL)
        else:
            self.destroy()

    # ---------- install simulation ----------
    def on_install(self):
        if self.installing:
            return
        target = self.install_dir.get().strip()
        if not target:
            messagebox.showerror("Destination", "Chưa chọn thư mục cài đặt.")
            return
        self.installing = True
        self.btn_install.configure(state="disabled")
        self.btn_cancel.configure(text="Cancel (Stop)")
        self.progress.start()  # kiểu “indeterminate” nhẹ

        t = threading.Thread(target=self.simulate_install, daemon=True)
        t.start()

    def set_progress(self, v: float):
        self.progress.stop()
        self.progress.set(max(0.0, min(1.0, v)))

    def simulate_install(self):
        steps = [
            ("Chuẩn bị tệp cài đặt…", 0.10),
            ("Giải nén gói tài nguyên…", 0.28),
            ("Cài thành phần lõi…", 0.48),
            ("Cài plug-ins…", 0.66),
            ("Đăng ký thành phần hệ thống…", 0.82),
            ("Dọn dẹp tạm thời…", 0.93),
            ("Hoàn tất cấu hình…", 1.00),
        ]
        # tạo thư mục đích (giả lập)
        try:
            os.makedirs(self.install_dir.get(), exist_ok=True)
        except Exception as e:
            self.append_err(f"Lỗi tạo thư mục: {e}")
            self.finish(False)
            return

        for msg, pct in steps:
            if not self.installing: return
            self.append_info(msg)
            self.smooth_to(pct, duration=0.6)
            time.sleep(0.15)

        # ghi file cấu hình “mock”
        try:
            cfg_path = os.path.join(self.install_dir.get(), "mock.config")
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write("mock_install=true\nproduct=photoshop\nversion=mock-2.0\n")
            self.append_ok(f"Đã tạo file cấu hình: {cfg_path}")
        except Exception as e:
            self.append_err(f"Lỗi ghi file cấu hình: {e}")
            self.finish(False)
            return

        self.append_ok("Installation completed successfully.")
        self.finish(True)

    def smooth_to(self, target, duration=0.5, fps=60):
        start = self.progress._determinate_value if hasattr(self.progress, "_determinate_value") else 0.0
        steps = int(duration * fps)
        if steps <= 0: steps = 1
        for i in range(1, steps+1):
            if not self.installing: return
            v = start + (target - start) * (i/steps)
            self.after(0, lambda val=v: self.set_progress(val))
            time.sleep(1/fps)

    # ---------- log helpers ----------
    def append_info(self, text):
        if hasattr(self, "log"): self.after(0, lambda: self.log.append(f"• {text}"))

    def append_ok(self, text):
        if hasattr(self, "log"): self.after(0, lambda: self.log.append(f"✓ {text}", tag="ok", color=OK_GREEN))

    def append_warn(self, text):
        if hasattr(self, "log"): self.after(0, lambda: self.log.append(f"! {text}", tag="warn", color=WARN_YEL))

    def append_err(self, text):
        if hasattr(self, "log"): self.after(0, lambda: self.log.append(f"× {text}", tag="err", color=ERR_RED))

    def finish(self, success: bool):
        self.installing = False
        self.after(0, lambda: self.btn_cancel.configure(text="Close", command=self.destroy))
        self.after(0, lambda: self.btn_install.configure(state="disabled"))
        if success:
            messagebox.showinfo("Finish", "Cài đặt hoàn tất.")
        else:
            messagebox.showerror("Finish", "Cài đặt thất bại.")

def run():
    app = InstallerUI()
    app.mainloop()

if __name__ == "__main__":
    run()
