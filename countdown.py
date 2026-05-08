import tkinter as tk
from tkinter import ttk
import threading
import winsound
from datetime import datetime, timedelta, timezone

STATES = {"IDLE": "idle", "RUNNING": "running", "PAUSED": "paused"}


class CountdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面倒计时")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.remaining = 0
        self.total_remaining = 0
        self.state = STATES["IDLE"]
        self._after_id = None

        self._build_ui()
        self._center_window(420, 560)

    def _center_window(self, width, height):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        # 标题
        self.title_label = ttk.Label(self.root, text="桌面倒计时", font=("Microsoft YaHei", 14))
        self.title_label.pack(pady=(20, 10))

        # 时间显示
        self.time_label = ttk.Label(
            self.root, text="00:00:00", font=("Consolas", 48)
        )
        self.time_label.pack(pady=(10, 5))

        # 进度条
        self.progress = ttk.Progressbar(
            self.root, mode="determinate", length=300
        )
        self.progress.pack(pady=(0, 10))

        self.end_time_label = ttk.Label(
            self.root, text="", font=("Microsoft YaHei", 10)
        )
        self.end_time_label.pack(pady=(0, 15))

        # 时间输入
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=5)

        self.hour_var = tk.IntVar(value=0)
        self.hour_spin = ttk.Spinbox(
            input_frame,
            from_=0,
            to=99,
            textvariable=self.hour_var,
            width=4,
            font=("Microsoft YaHei", 10),
        )
        self.hour_spin.pack(side=tk.LEFT)
        ttk.Label(input_frame, text="时", font=("Microsoft YaHei", 10)).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        self.min_var = tk.IntVar(value=0)
        self.min_spin = ttk.Spinbox(
            input_frame,
            from_=0,
            to=59,
            textvariable=self.min_var,
            width=4,
            font=("Microsoft YaHei", 10),
        )
        self.min_spin.pack(side=tk.LEFT)
        ttk.Label(input_frame, text="分", font=("Microsoft YaHei", 10)).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        self.sec_var = tk.IntVar(value=0)
        self.sec_spin = ttk.Spinbox(
            input_frame,
            from_=0,
            to=59,
            textvariable=self.sec_var,
            width=4,
            font=("Microsoft YaHei", 10),
        )
        self.sec_spin.pack(side=tk.LEFT)
        ttk.Label(input_frame, text="秒", font=("Microsoft YaHei", 10)).pack(
            side=tk.LEFT,
        )

        # 预设快捷时长
        preset_frame = ttk.LabelFrame(self.root, text="快捷预设", padding=8)
        preset_frame.pack(pady=(5, 0))

        presets = [
            ("5 分", 0, 5, 0),
            ("10 分", 0, 10, 0),
            ("15 分", 0, 15, 0),
            ("25 分", 0, 25, 0),
            ("30 分", 0, 30, 0),
            ("45 分", 0, 45, 0),
            ("1 时", 1, 0, 0),
            ("2 时", 2, 0, 0),
        ]
        for i, (label, h, m, s) in enumerate(presets):
            btn = ttk.Button(
                preset_frame,
                text=label,
                width=6,
                command=lambda h=h, m=m, s=s: self._set_preset(h, m, s),
            )
            btn.grid(row=i // 4, column=i % 4, padx=3, pady=2)

        # 按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=(10, 10))

        self.start_btn = ttk.Button(btn_frame, text="开始", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = ttk.Button(btn_frame, text="暂停", command=self.pause)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.pause_btn.state(["disabled"])

        self.reset_btn = ttk.Button(btn_frame, text="重置", command=self.reset)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        self.inputs = [self.hour_spin, self.min_spin, self.sec_spin]

        # 设置区（透明度）
        settings_frame = ttk.LabelFrame(self.root, text="设置", padding=8)
        settings_frame.pack(pady=(5, 10), fill="x", padx=20)

        # 透明度滑块
        opacity_frame = ttk.Frame(settings_frame)
        opacity_frame.pack(fill="x", pady=2)
        ttk.Label(opacity_frame, text="透明度：", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        self.opacity_scale = ttk.Scale(
            opacity_frame,
            from_=0.2,
            to=1.0,
            value=1.0,
            command=self._set_opacity,
        )
        self.opacity_scale.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

    def _format_time(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _update_display(self):
        self.time_label.config(text=self._format_time(self.remaining))

    def _update_progress(self):
        if self.total_remaining > 0:
            pct = (self.total_remaining - self.remaining) / self.total_remaining * 100
            self.progress["value"] = pct

    def _toggle_inputs(self, enabled):
        state = "!disabled" if enabled else "disabled"
        for w in self.inputs:
            w.state([state])

    def _show_end_time(self):
        bj_tz = timezone(timedelta(hours=8))
        end = datetime.now(bj_tz) + timedelta(seconds=self.remaining)
        self.end_time_label.config(text=f"预计结束：{end.strftime('%Y-%m-%d %H:%M:%S')}")

    def _set_buttons(self, start, pause, reset):
        self.start_btn.state(["!disabled"] if start else ["disabled"])
        self.pause_btn.state(["!disabled"] if pause else ["disabled"])
        self.reset_btn.state(["!disabled"] if reset else ["disabled"])

    def _set_preset(self, h, m, s):
        if self.state != STATES["IDLE"]:
            return
        self.hour_var.set(h)
        self.min_var.set(m)
        self.sec_var.set(s)

    def _set_opacity(self, val):
        self.root.attributes("-alpha", float(val))

    def _is_time_zero(self):
        return self.hour_var.get() == 0 and self.min_var.get() == 0 and self.sec_var.get() == 0

    def start(self):
        if self.state == STATES["IDLE"]:
            if self._is_time_zero():
                return
            self.remaining = (
                self.hour_var.get() * 3600
                + self.min_var.get() * 60
                + self.sec_var.get()
            )
            self.total_remaining = self.remaining
            self._toggle_inputs(False)
            self._show_end_time()
            self.progress["value"] = 0

        self.state = STATES["RUNNING"]
        self._set_buttons(False, True, True)
        self._tick()

    def pause(self):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.state = STATES["PAUSED"]
        self._set_buttons(True, False, True)

    def reset(self):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.state = STATES["IDLE"]
        self.remaining = 0
        self.total_remaining = 0
        self.hour_var.set(0)
        self.min_var.set(0)
        self.sec_var.set(0)
        self._update_display()
        self.progress["value"] = 0
        self.end_time_label.config(text="")
        self.time_label.config(foreground="black")
        self._toggle_inputs(True)
        self._set_buttons(True, False, True)

    def _tick(self):
        if self.remaining > 0:
            self.remaining -= 1
            self._update_display()
            self._update_progress()

            # 最后 10 秒红色闪烁
            if 0 < self.remaining <= 10:
                if self.remaining % 2 == 0:
                    self.time_label.config(foreground="red")
                else:
                    self.time_label.config(foreground="black")

            self._after_id = self.root.after(1000, self._tick)
        else:
            self._after_id = None
            self.state = STATES["IDLE"]
            self._update_display()
            self.progress["value"] = 100
            self.time_label.config(foreground="black")
            self._toggle_inputs(True)
            self._set_buttons(True, False, True)
            self._play_alarm()

    def _play_alarm(self):
        def beep():
            for _ in range(3):
                winsound.Beep(1000, 300)
                winsound.Beep(800, 300)

        threading.Thread(target=beep, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownApp(root)
    root.mainloop()
