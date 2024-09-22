import tkinter as tk  # 显示界面
from tkinter import messagebox  # 显示消息框
import ttkbootstrap as ttk  # ttk美化主题
from ttkbootstrap.constants import *  # ttk变量
import winsound  # Windows播放声音
import time  # 处理时间
import re  # 正则表达式
import ctypes  # C语言扩展

from win32api import GetMonitorInfo, MonitorFromPoint

# pyinstaller -n PomodoroTimer -F -w .\PomodoroTimer.py
# pyinstaller PomodoroTimer.spec

font = "微软雅黑"
input_regex = r"^(([0]|[1-9]\d{0,2})((\.\d{0,2})?))?$"


class PomodoroTimer:
    def __init__(self, root: ttk.Window):
        self.root = root  # 源窗口
        self._config_ttk_style()  # 配置ttk样式
        self._config_root_window()  # 配置源窗口参数
        self._create_widgets()  # 配置GUI组件

        self.clock_state = 1  # 番茄时钟状态(1:工作状态;2:休息状态)
        self.is_running = False  # 是否计时中
        self.remaining_time = 0  # 计时剩余时间(秒)
        self.end_time = 0  # 计时结束时间

    def update_work_time_label(self, *args):
        """更新工作时间标签"""
        self._update_time_label(self.work_time, self.work_time_label)

    def update_rest_time_label(self, *args):
        """更新休息时间标签"""
        self._update_time_label(self.rest_time, self.rest_time_label)

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
        winsound.Beep(1000, 1000)
        # winsound.PlaySound("ring.wav", winsound.SND_ASYNC)
        if self.clock_state == 1:
            msg = "工作计时结束"
            self.clock_state = 2
            self.remaining_time = int(float(self.rest_time.get()) * 60)
        elif self.clock_state == 2:
            msg = "休息计时结束"
            self.clock_state = 1
            self.remaining_time = 0
        self._popup_message("够钟", msg)

        if self.clock_state == 1:
            self.reset_button.pack_forget()
            self.start_button.pack(side=tk.LEFT, padx=10)
            self.is_running = False
            self.work_entry.config(state=tk.NORMAL)
            self.rest_entry.config(state=tk.NORMAL)
            self.update_work_time_label()
            self.update_rest_time_label()
        elif self.clock_state == 2:
            self.start_button.pack_forget()
            self.pause_button.pack_forget()
            self.reset_button.pack(side=tk.LEFT, padx=10)
            self.end_time = time.time() + self.remaining_time
            self.is_running = True
            self._update_timer()

    def _popup_message(self, title, message) -> None:
        """弹窗消息"""
        top = tk.Toplevel(self.root)  # 创建一个顶层窗口作为弹窗
        top.title(title)
        top.geometry("250x100")
        top.resizable(False, False)  # 禁止调整弹窗大小
        top.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮
        top.attributes("-topmost", True)  # 设置弹窗总是显示在最前面
        label = tk.Label(top, text=message, font=(font, 12))  # 创建显示消息的标签
        label.pack(expand=True)
        ok_button = tk.Button(top, text="确认", command=top.destroy, font=(font, 10))  # 创建确认按钮
        ok_button.pack(pady=10)
        top.grab_set()  # 设置模态窗口, 弹窗弹出时, 禁止对主窗口进行其他操作
        self._center_window(top)  # 弹窗居中显示
        self._set_dark_title_bar(top)  # 设置弹窗黑色标题栏
        self.root.wait_window(top)  # 等待弹窗关闭后再继续执行

    def start_timer(self):
        try:
            if self.remaining_time == 0:
                if self.clock_state == 1:
                    self.remaining_time = max(1, int(float(self.work_time.get()) * 60))
                elif self.clock_state == 2:
                    self.remaining_time = max(1, int(float(self.rest_time.get()) * 60))
            self.end_time = time.time() + self.remaining_time
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return

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
        self.update_work_time_label()
        self.update_rest_time_label()
        self.work_entry.config(state=tk.NORMAL)
        self.rest_entry.config(state=tk.NORMAL)
        self.pause_button.pack_forget()
        self.reset_button.pack_forget()
        self.start_button.pack(side=tk.LEFT, padx=10)

    def _create_widgets(self) -> None:
        """创建并布局GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH)
        # 配置输入框架
        self._create_input_frame(main_frame)
        # 配置倒计时标签框架
        self._create_timer_frame(main_frame)
        # 配置按钮框架
        self._create_button_frame(main_frame)

    def _create_button_frame(self, main_frame) -> None:
        font_size = 12
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(0, 2))  # pady: 组件垂直间距, 第一个值为上间距, 第二个值为下间距

        self.start_button = ttk.Button(
            button_frame,
            text="开始",
            command=self.start_timer,
            style="success-outline.TButton",
        )
        self.start_button.pack(side=tk.LEFT, padx=10)  # padx: 组件水平间距

        self.pause_button = ttk.Button(
            button_frame,
            text="暂停",
            command=self.pause_timer,
            state=tk.DISABLED,
            style="light-outline.TButton",
        )
        self.pause_button.pack(side=tk.LEFT, padx=10)

        self.reset_button = ttk.Button(
            button_frame,
            text="重置",
            command=self.reset_timer,
            style="light-outline.TButton",
        )

    def _create_timer_frame(self, main_frame) -> None:
        timer_frame = ttk.Frame(main_frame)
        timer_frame.pack(pady=(0, 0))
        font_size = 24
        self.work_time_label = ttk.Label(timer_frame, text="25:00", font=(font, font_size))
        self.work_time_label.pack(side=tk.LEFT, padx=(0, 20))  # padx第一个值为左间距, 第二个值为右间距
        self.rest_time_label = ttk.Label(timer_frame, text="05:00", font=(font, font_size))
        self.rest_time_label.pack(side=tk.LEFT, padx=(20, 0))

    def _create_input_frame(self, main_frame) -> None:
        font_size = 12
        # 输入区域框架
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=(5, 0))
        # 输入内容验证命令
        vcmd = (self.root.register(self.validate_input), "%P")

        # "工作时间"输入框架
        self.work_time = ttk.StringVar(value="25")
        self.work_time.trace_add("write", self.update_work_time_label)
        work_input_frame = ttk.Frame(input_frame)
        work_input_frame.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 0))
        ttk.Label(work_input_frame, text="工作:", font=(font, font_size)).pack(side=tk.LEFT)
        self.work_entry = ttk.Entry(
            work_input_frame,
            textvariable=self.work_time,
            width=6,
            font=(font, font_size),
            validate="key",
            validatecommand=vcmd,
            style="Custom_1.TEntry",
        )
        self.work_entry.pack(side=tk.LEFT)

        # "休息时间"输入框架
        self.rest_time = ttk.StringVar(value="5")  # 休息时间
        self.rest_time.trace_add("write", self.update_rest_time_label)
        rest_input_frame = ttk.Frame(input_frame)
        rest_input_frame.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(rest_input_frame, text="休息:", font=(font, font_size)).pack(side=tk.LEFT)
        self.rest_entry = ttk.Entry(
            rest_input_frame,
            textvariable=self.rest_time,
            width=6,
            font=(font, font_size),
            validate="key",
            validatecommand=vcmd,
            style="Custom_1.TEntry",
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
        self._bottom_right_window(self.root)  # 窗口放置右下角
        self._set_dark_title_bar(self.root)  # 黑色标题栏

    def _config_ttk_style(self) -> None:
        """配置ttk样式"""
        ttk_style = ttk.Style()
        ttk_style.configure("Custom_1.TEntry", padding=(5, 0))

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


if __name__ == "__main__":
    root = ttk.Window(themename="darkly")  # 创建主窗口
    app = PomodoroTimer(root)  # 创建应用实例
    root.mainloop()  # 进入主事件循环
