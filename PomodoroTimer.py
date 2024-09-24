import tkinter as tk  # 显示界面
from tkinter import messagebox  # 显示消息框
import winsound  # Windows播放声音
import win32gui  # Windows GUI
import time  # 处理时间
import re  # 正则表达式
import ctypes  # C语言扩展

from win32api import GetMonitorInfo, MonitorFromPoint

# pyinstaller -n PomodoroTimer -F -w .\PomodoroTimer.py
# pyinstaller PomodoroTimer.spec

font = "微软雅黑"
bg_color = "#1b1b1b"
fg_color = "#fdf6e3"
button1_color = "#09b286"
button2_color = "#a7afb6"

input_regex = r"^(([0]|[1-9]\d{0,2})((\.\d{0,2})?))?$"


class PomodoroTimer:
    def __init__(self, root: tk.Tk):
        self.root = root  # 源窗口
        self._config_root_window()  # 配置源窗口参数
        self._create_widgets()  # 配置GUI组件

        self.clock_state = 1  # 番茄时钟状态(1:工作状态;2:休息状态)
        self.is_running = False  # 是否计时中
        self.remaining_time = 0  # 计时剩余时间(秒)
        self.end_time = 0  # 计时结束时间

        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

    def _update_time_label(self, time_var, label):
        """更新时间标签"""
        try:
            input_value = time_var.get()
            if input_value == "":
                label.config(text="00:00")
                return
            minutes = float(input_value)
            total_seconds = max(1, int(minutes * 60))
            minutes, seconds = divmod(total_seconds, 60)
            label.config(text=f"{minutes:02d}:{seconds:02d}")
        except ValueError:
            pass

    def _update_timer(self):
        """更新计时器显示"""
        if self.is_running:
            self.remaining_time = max(0, int(self.end_time - time.time()))
            if self.remaining_time > 0:
                minutes, seconds = divmod(self.remaining_time, 60)
                if self.clock_state == 1:
                    self.work_time_label.config(text=f"{minutes:02d}:{seconds:02d}")
                elif self.clock_state == 2:
                    self.rest_time_label.config(text=f"{minutes:02d}:{seconds:02d}")
                self.root.after(200, self._update_timer)
            else:
                if self.clock_state == 1:
                    self.work_time_label.config(text="00:00")
                elif self.clock_state == 2:
                    self.rest_time_label.config(text="00:00")
                self._timer_finished()

    def _timer_finished(self):
        """计时器结束逻辑"""
        if self.clock_state == 1:
            msg = "工作计时结束"
            self.clock_state = 2
            self.remaining_time = int(float(self.rest_time.get()) * 60)
        elif self.clock_state == 2:
            msg = "休息计时结束"
            self.clock_state = 1
            self.remaining_time = 0
        self._popup_message("提示", msg)

        if self.clock_state == 1:
            self.reset_button.pack_forget()
            self.start_button.pack(side=tk.LEFT, padx=10)
            self.is_running = False
            self.work_entry.config(state=tk.NORMAL)
            self.rest_entry.config(state=tk.NORMAL)
            self._update_time_label(self.work_time, self.work_time_label)
            self._update_time_label(self.rest_time, self.rest_time_label)
            self._center_window(self.root)  # 窗口居中
            self._remove_drag()  # 移除拖动功能
        elif self.clock_state == 2:
            self.start_button.pack_forget()
            self.pause_button.pack_forget()
            self.reset_button.pack(side=tk.LEFT, padx=10)
            self.end_time = time.time() + self.remaining_time
            self.is_running = True
            self._update_timer()

    def _popup_message(self, title, message) -> None:
        """弹窗消息"""
        top = tk.Toplevel(self.root, bg=bg_color)  # 创建一个顶层窗口作为弹窗
        top.title(title)
        top.geometry("250x100")
        top.resizable(False, False)  # 禁止调整弹窗大小
        top.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮
        label = tk.Label(top, text=message, font=(font, 12), bg=bg_color, fg=fg_color)  # 创建显示消息的标签
        label.pack(expand=True)
        # 创建确认按钮
        ok_button = tk.Button(top, text="确认", command=top.destroy, font=(font, 10), bg=bg_color, fg=fg_color)
        ok_button.pack(pady=10)
        top.grab_set()  # 设置模态窗口, 弹窗弹出时, 禁止对主窗口进行其他操作
        self._center_window(top)  # 弹窗居中显示
        self._set_dark_title_bar(top)  # 设置弹窗黑色标题栏
        self._popup_schedule_reminder(top)  # 弹窗定时提醒
        self.root.wait_window(top)  # 等待弹窗关闭后再继续执行

    def _popup_schedule_reminder(self, window):
        """弹窗更新提醒"""
        if window.winfo_exists():
            winsound.PlaySound("ring.wav", winsound.SND_ASYNC)
            hwnd = win32gui.GetParent(window.winfo_id())
            win32gui.FlashWindow(hwnd, True)
            window.after(5 * 60 * 1000, lambda: self._popup_schedule_reminder(window))

    def start_timer(self):
        try:
            if self.remaining_time == 0:
                if self.clock_state == 1:
                    self.remaining_time = max(1, int(float(self.work_time.get()) * 60))
                    self._bottom_right_window(self.root)
                elif self.clock_state == 2:
                    self.remaining_time = max(1, int(float(self.rest_time.get()) * 60))
            self.end_time = time.time() + self.remaining_time
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return
        self._setup_drag()  # 设置拖动功能
        self.work_entry.config(state=tk.DISABLED)
        self.rest_entry.config(state=tk.DISABLED)
        self.start_button.pack_forget()
        self.reset_button.pack_forget()
        self.pause_button.pack(side=tk.LEFT, padx=10)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        self.pause_button.config(state=tk.NORMAL)
        self.is_running = True
        self._update_timer()

    def pause_timer(self):
        """暂停计时器"""
        self.is_running = False
        self.remaining_time = max(0, int(self.end_time - time.time()))
        self.pause_button.pack_forget()
        self.reset_button.pack_forget()
        self.start_button.pack(side=tk.LEFT, padx=10)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        self.start_button.config(state=tk.NORMAL)

    def reset_timer(self):
        """重置计时器"""
        self.is_running = False
        self.clock_state = 1
        self.remaining_time = 0
        self._update_time_label(self.work_time, self.work_time_label)
        self._update_time_label(self.rest_time, self.rest_time_label)
        self.work_entry.config(state=tk.NORMAL)
        self.rest_entry.config(state=tk.NORMAL)
        self.pause_button.pack_forget()
        self.reset_button.pack_forget()
        self.start_button.pack(side=tk.LEFT, padx=10)
        self._remove_drag()  # 移除拖动功能

    def _create_widgets(self) -> None:
        """创建并布局GUI组件"""
        # 主框架
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(expand=True, fill=tk.BOTH)
        # 配置输入框架
        self._create_input_frame(main_frame)
        # 配置倒计时标签框架
        self._create_timer_frame(main_frame)
        # 配置按钮框架
        self._create_button_frame(main_frame)

    def _create_button_frame(self, main_frame) -> None:
        font_size = 10
        button_frame = tk.Frame(main_frame, bg=bg_color)
        button_frame.pack(pady=(0, 2))  # pady: 组件垂直间距, 第一个值为上间距, 第二个值为下间距

        self.start_button = tk.Button(
            button_frame,
            text="开始",
            command=self.start_timer,
            font=(font, font_size),
            bg=bg_color,
            fg=button1_color,
            activebackground=button1_color,
            activeforeground=fg_color,
            relief=tk.RIDGE,
        )
        self.start_button.pack(side=tk.LEFT, padx=10)  # padx: 组件水平间距

        self.pause_button = tk.Button(
            button_frame,
            text="暂停",
            command=self.pause_timer,
            state=tk.DISABLED,
            font=(font, font_size),
            bg=bg_color,
            fg=button2_color,
            activebackground=button2_color,
            activeforeground=fg_color,
            relief=tk.RIDGE,
        )
        self.pause_button.pack(side=tk.LEFT, padx=10)

        self.reset_button = tk.Button(
            button_frame,
            text="重置",
            command=self.reset_timer,
            font=(font, font_size),
            bg=bg_color,
            fg=button2_color,
            activebackground=button2_color,
            activeforeground=fg_color,
            relief=tk.RIDGE,
        )

    def _create_timer_frame(self, main_frame) -> None:
        timer_frame = tk.Frame(main_frame, bg=bg_color)
        timer_frame.pack(pady=(0, 0))
        font_size = 24
        self.work_time_label = tk.Label(timer_frame, text="25:00", font=(font, font_size), bg=bg_color, fg=fg_color)
        self.work_time_label.pack(side=tk.LEFT, padx=(0, 20))  # padx第一个值为左间距, 第二个值为右间距
        self.rest_time_label = tk.Label(timer_frame, text="05:00", font=(font, font_size), bg=bg_color, fg=fg_color)
        self.rest_time_label.pack(side=tk.LEFT, padx=(20, 0))

    def _create_input_frame(self, main_frame) -> None:
        font_size = 12
        # 输入区域框架
        input_frame = tk.Frame(main_frame, bg=bg_color)
        input_frame.pack(pady=(5, 0))
        # 输入内容验证命令
        vcmd = (self.root.register(self.validate_input), "%P")

        # "工作时间"输入框架
        self.work_time = tk.StringVar(value="25")
        self.work_time.trace_add("write", lambda a, b, c: self._update_time_label(self.work_time, self.work_time_label))
        work_input_frame = tk.Frame(input_frame, bg=bg_color)
        work_input_frame.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 0))
        tk.Label(work_input_frame, text="工作:", font=(font, font_size), bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
        self.work_entry = tk.Entry(
            work_input_frame,
            textvariable=self.work_time,
            width=6,
            font=(font, font_size),
            validate="key",
            validatecommand=vcmd,
            bg=bg_color,
            fg=fg_color,
            disabledbackground=bg_color,
        )
        self.work_entry.pack(side=tk.LEFT)

        # "休息时间"输入框架
        self.rest_time = tk.StringVar(value="5")  # 休息时间
        self.rest_time.trace_add("write", lambda a, b, c: self._update_time_label(self.rest_time, self.rest_time_label))
        rest_input_frame = tk.Frame(input_frame, bg=bg_color)
        rest_input_frame.pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(rest_input_frame, text="休息:", font=(font, font_size), bg=bg_color, fg=fg_color).pack(side=tk.LEFT)
        self.rest_entry = tk.Entry(
            rest_input_frame,
            textvariable=self.rest_time,
            width=6,
            font=(font, font_size),
            validate="key",
            validatecommand=vcmd,
            bg=bg_color,
            fg=fg_color,
            disabledbackground=bg_color,
        )
        self.rest_entry.pack(side=tk.LEFT)

    def validate_input(self, input_str) -> bool:
        """验证输入是否有效"""
        return True if re.match(input_regex, input_str) else False

    def _config_root_window(self) -> None:
        """配置主窗口"""
        self.root.title("番茄时钟")  # 窗口标题
        self.root.resizable(False, False)  # 禁止窗口最大化
        self.root.geometry("320x140")  # 窗口大小
        self.root.attributes("-topmost", True)  # 窗口最前
        self._center_window(self.root)  # 窗口居中
        self._set_dark_title_bar(self.root)  # 黑色标题栏
        self.root.bind("<FocusIn>", lambda x: self.root.attributes("-alpha", 1.0))  # 获取焦点时不透明
        self.root.bind("<FocusOut>", lambda x: self.root.attributes("-alpha", 0.3))  # 失去焦点时半透明

    def _set_dark_title_bar(self, window) -> None:
        """设置黑色窗口标题栏"""
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.windll.user32.GetParent(window.winfo_id()),  # 窗口句柄
            20,  # 20表示MICA效果(Win11的一种背景效果)
            ctypes.byref(ctypes.c_int(2)),  # 创建一个C整形值2的指针引用, 2表示开启MICA效果
            ctypes.sizeof(ctypes.c_int(2)),  # 指针引用的大小
        )

    def _center_window(self, window) -> None:
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        window.geometry("{}x{}+{}+{}".format(width, height, x, y))

    def _bottom_right_window(self, window) -> None:
        window.update_idletasks()
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        monitor_area = monitor_info.get("Monitor")
        work_area = monitor_info.get("Work")
        taskbar_height = monitor_area[3] - work_area[3]
        title_bar_height = root.winfo_rooty() - root.winfo_y()
        x = self.root.winfo_screenwidth() - window.winfo_width()
        y = self.root.winfo_screenheight() - window.winfo_height() - title_bar_height - taskbar_height
        window.geometry(f"+{x}+{y}")

    def _setup_drag(self):
        """设置拖动功能"""
        self.root.overrideredirect(True)  # 移除窗口边框
        self.root.bind("<ButtonPress-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._drag)
        self.root.bind("<ButtonRelease-1>", lambda event: setattr(self, "dragging", False))

    def _remove_drag(self):
        """移除拖动功能"""
        self.root.overrideredirect(False)  # 恢复窗口边框
        self._set_dark_title_bar(self.root)  # 重新设置黑色标题栏
        self.root.attributes("-alpha", 1.0)  # 设置窗口不透明
        self.root.unbind("<ButtonPress-1>")
        self.root.unbind("<B1-Motion>")
        self.root.unbind("<ButtonRelease-1>")

    def _start_drag(self, event):
        """开始拖动"""
        if not self._is_on_button(event):
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def _drag(self, event):
        """拖动窗口"""
        if self.dragging:
            x = self.root.winfo_x() + (event.x - self.drag_start_x)
            y = self.root.winfo_y() + (event.y - self.drag_start_y)
            self.root.geometry(f"+{x}+{y}")

    def _is_on_button(self, event):
        """检查点击是否在按钮上"""
        for widget in [self.start_button, self.pause_button, self.reset_button]:
            if widget.winfo_ismapped():
                x = self.root.winfo_x() + widget.winfo_x()
                y = self.root.winfo_y() + widget.winfo_y()
                if x <= event.x_root <= x + widget.winfo_width() and y <= event.y_root <= y + widget.winfo_height():
                    return True
        return False


if __name__ == "__main__":
    root = tk.Tk()  # 创建主窗口
    app = PomodoroTimer(root)  # 创建应用实例
    root.mainloop()  # 进入主事件循环
