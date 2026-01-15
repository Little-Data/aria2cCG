import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import threading
import queue
import webbrowser
import pystray
from PIL import Image, ImageDraw
import configparser
import time
import sys
import ctypes
from ctypes import wintypes

# 全局变量区
aria2_process = None
log_window = None
log_text = None
# 队列最大容量 200，防止内存溢出
output_queue = queue.Queue(maxsize=200)
is_log_running = False
tray_icon = None
root = None
# 输入框和勾选框全局变量
entry_exe = None
entry_conf = None
entry_webui = None
entry_params = None
show_cmd_var = None
auto_start_var = None
start_hide_var = None
auto_open_web_var = None
exit_stop_aria2_var = None
# 全局日志内容缓存
log_content_str = ""
# INI配置文件路径
def get_app_dir():
    """获取程序实际运行目录"""
    if getattr(sys, 'frozen', False):
        # 打包后环境：sys.executable指向exe文件路径
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # 开发环境：使用脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))
# INI配置文件路径
INI_FILE_PATH = os.path.join(get_app_dir(), "Aria2cCG.ini")
# 日志最大保留行数
MAX_LOG_LINES = 300

def center_window():
    """让主窗口在屏幕正中央显示，适配所有分辨率"""
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"+{x}+{y}")

def get_tray_icon():
    """托盘图标"""
    # 获取程序当前所在的绝对目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接同目录下的 icon.ico 路径
    ico_path = os.path.join(current_dir, "icon.ico")
    try:
        # 优先尝试加载本地ICO文件
        if os.path.exists(ico_path):
            ico_img = Image.open(ico_path)
            return ico_img
    except Exception as e:
        pass
    
    # 备用方案
    icon_size = (64, 64)
    image = Image.new("RGB", icon_size, color="white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill="#00FF00")
    return image

def set_window_icon():
    """主窗口标题栏左上角图标"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(current_dir, "icon.ico")
    try:
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path) # tkinter原生设置窗口标题栏图标
    except Exception as e:
        pass

# 配置文件读写功能
def init_config():
    config = configparser.ConfigParser()
    if not os.path.exists(INI_FILE_PATH):
        config["MainConfig"] = {
            "aria2_exe_path": "",
            "aria2_conf_path": "",
            "webui_path": "",
            "custom_params": "",
            "auto_open_log": "False",
            "auto_start_aria2": "False",
            "start_hide_window": "False",
            "auto_open_web": "False",
            "exit_stop_aria2": "False"
        }
        with open(INI_FILE_PATH, "w", encoding="utf-8") as f:
            config.write(f)

def load_config():
    init_config()
    config = configparser.ConfigParser()
    config.read(INI_FILE_PATH, encoding="utf-8")
    entry_exe.insert(0, config["MainConfig"].get("aria2_exe_path", ""))
    entry_conf.insert(0, config["MainConfig"].get("aria2_conf_path", ""))
    entry_webui.insert(0, config["MainConfig"].get("webui_path", ""))
    entry_params.insert(0, config["MainConfig"].get("custom_params", ""))
    show_cmd_var.set(config["MainConfig"].getboolean("auto_open_log", False))
    auto_start_var.set(config["MainConfig"].getboolean("auto_start_aria2", False))
    start_hide_var.set(config["MainConfig"].getboolean("start_hide_window", False))
    auto_open_web_var.set(config["MainConfig"].getboolean("auto_open_web", False))
    exit_stop_aria2_var.set(config["MainConfig"].getboolean("exit_stop_aria2", False))

def save_config():
    init_config()
    config = configparser.ConfigParser()
    config["MainConfig"] = {
        "aria2_exe_path": entry_exe.get().strip(),
        "aria2_conf_path": entry_conf.get().strip(),
        "webui_path": entry_webui.get().strip(),
        "custom_params": entry_params.get().strip(),
        "auto_open_log": str(show_cmd_var.get()),
        "auto_start_aria2": str(auto_start_var.get()),
        "start_hide_window": str(start_hide_var.get()),
        "auto_open_web": str(auto_open_web_var.get()),
        "exit_stop_aria2": str(exit_stop_aria2_var.get())
    }
    with open(INI_FILE_PATH, "w", encoding="utf-8") as f:
        config.write(f)

# 路径选择相关函数
def select_aria2_exe():
    file_path = filedialog.askopenfilename(title="选择 aria2c.exe 可执行文件",filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
    if file_path:
        entry_exe.delete(0, tk.END)
        entry_exe.insert(0, file_path)
        if not file_path.lower().endswith("aria2c.exe"):
            messagebox.warning("提示", "请选择正确的 aria2c.exe 文件！")
        save_config()

def select_aria2_conf():
    file_path = filedialog.askopenfilename(title="选择 aria2.conf 配置文件",filetypes=[("配置文件", "*.conf"), ("文本文件", "*.txt"), ("所有文件", "*.*")])
    if file_path:
        entry_conf.delete(0, tk.END)
        entry_conf.insert(0, file_path)
        save_config()

def select_web_ui():
    file_path = filedialog.askopenfilename(title="选择 Aria2 Web管理页面 HTML文件",filetypes=[("HTML网页文件", "*.html"), ("所有文件", "*.*")])
    if file_path:
        entry_webui.delete(0, tk.END)
        entry_webui.insert(0, file_path)
        save_config()

# 日志相关函数
def create_log_window():
    """创建内置独立日志窗口"""
    global log_window, log_text
    if log_window and log_window.winfo_exists():
        log_window.focus()
        return
    log_window = tk.Toplevel()
    log_window.title("Aria2c 实时运行日志窗口")
    log_window.geometry("900x600")
    log_window.resizable(True, True)
    log_text = scrolledtext.ScrolledText(log_window, font=("宋体", 9), bg="#f8f8f8", fg="#000000", state=tk.DISABLED)
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    log_window.protocol("WM_DELETE_WINDOW", lambda: log_window.destroy())
    
    # 创建窗口后，立即写入缓存的历史日志
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, log_content_str)
    log_text.see(tk.END)
    log_text.config(state=tk.DISABLED)
    
    # 启动主线程的日志消费任务，异步更新GUI
    root.after(100, consume_log_queue)

def read_aria2_output(process, pipe_type):
    """子线程只做日志读取+入队，不碰任何GUI组件"""
    global is_log_running
    encoding_list = ["gbk", "utf-8", "gb2312"]
    for encoding in encoding_list:
        try:
            pipe = process.stdout if pipe_type == "stdout" else process.stderr
            while is_log_running and process.poll() is None:
                line = pipe.readline()
                if not line:
                    time.sleep(0.001) # 微小休眠，避免空轮询吃满CPU
                    continue
                try:
                    line_str = line.decode(encoding).strip()
                    if line_str:
                        # 队列满时自动阻塞，不会内存溢出
                        output_queue.put(line_str, block=True, timeout=1)
                except queue.Full:
                    continue
                except Exception:
                    continue
            break
        except Exception:
            continue

def consume_log_queue():
    """异步消费日志队列，日志先追加到全局缓存，再写入文本框"""
    global log_text, is_log_running, log_content_str
    if log_text and log_text.winfo_exists() and is_log_running:
        log_lines = []
        # 批量读取队列中的日志，攒够10行再写入，减少GUI刷新次数
        for _ in range(min(10, output_queue.qsize())):
            try:
                log_lines.append(output_queue.get(block=False))
            except queue.Empty:
                break
        if log_lines:
            # 拼接新日志
            new_log = "\n".join(log_lines) + "\n"
            # 追加到全局日志缓存
            log_content_str += new_log
            
            # 对全局缓存做行数限制，只保留最新MAX_LOG_LINES行，防止内存溢出
            all_lines = log_content_str.splitlines()
            if len(all_lines) > MAX_LOG_LINES:
                log_content_str = "\n".join(all_lines[-MAX_LOG_LINES:]) + "\n"
            
            # 更新到文本框
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, new_log)
            log_text.see(tk.END)
            log_text.config(state=tk.DISABLED)
        # 循环执行，每100ms消费一次，兼顾实时性和流畅度
        root.after(100, consume_log_queue)

def show_log_window():
    """打开日志窗口，服务未运行则提示"""
    global aria2_process, is_log_running
    if not aria2_process or aria2_process.poll() is not None:
        messagebox.showinfo("提示", "当前Aria2c服务未运行，无法打开日志窗口！")
        return
    if not is_log_running:
        is_log_running = True
    create_log_window()

# Web管理页面相关函数
def open_web_ui_page():
    webui_path = entry_webui.get().strip().replace("/", "\\")
    if not webui_path:
        messagebox.showinfo("提示", "请先选择/填写 Aria2 Web管理页面的HTML文件路径！")
        return
    if not os.path.exists(webui_path):
        messagebox.showerror("错误", f"Web管理页面文件不存在！\n路径：{webui_path}")
        return
    if not webui_path.lower().endswith(".html"):
        if not messagebox.askokcancel("提示", "所选文件不是HTML格式，是否继续打开？"): return
    try:
        webbrowser.open_new(f"file:///{webui_path}")
    except Exception as e:
        messagebox.showerror("打开失败", f"打开Web管理页面出错：{str(e)}")

def auto_open_web_check():
    if auto_open_web_var.get():
        webui_path = entry_webui.get().strip().replace("/", "\\")
        if webui_path and os.path.exists(webui_path):
            try:
                webbrowser.open_new(f"file:///{webui_path}")
            except Exception as e:
                messagebox.showerror("自动打开失败", f"启动后打开管理页面出错：{str(e)}")
        elif webui_path and not os.path.exists(webui_path):
            messagebox.showwarning("路径无效", f"Web管理页面路径不存在，无法自动打开！\n路径：{webui_path}")

# 自动启动Aria2检查函数
def auto_start_aria2_check():
    global aria2_process, is_log_running
    if auto_start_var.get() and (not aria2_process or aria2_process.poll() is not None):
        aria2_exe_path = entry_exe.get().strip().replace("/", "\\")
        aria2_conf_path = entry_conf.get().strip().replace("/", "\\")
        custom_params = entry_params.get().strip()
        if aria2_exe_path and aria2_conf_path and os.path.exists(aria2_exe_path) and os.path.exists(aria2_conf_path):
            try:
                cmd = [aria2_exe_path, "--conf-path", aria2_conf_path]
                if custom_params:
                    cmd += custom_params.split()
                popen_kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
                aria2_process = subprocess.Popen(cmd,** popen_kwargs)
                is_log_running = True
                # 启动日志读取线程，只入队不碰GUI
                threading.Thread(target=read_aria2_output, args=(aria2_process, "stdout"), daemon=True).start()
                threading.Thread(target=read_aria2_output, args=(aria2_process, "stderr"), daemon=True).start()
                if show_cmd_var.get():
                    create_log_window()
                auto_open_web_check()
            except Exception as e:
                messagebox.showerror("自动启动失败", f"Aria2c自动启动出错：{str(e)}")

# Aria2核心启停函数
def start_aria2():
    global aria2_process, is_log_running
    aria2_exe_path = entry_exe.get().strip().replace("/", "\\")
    aria2_conf_path = entry_conf.get().strip().replace("/", "\\")
    custom_params = entry_params.get().strip()
    show_builtin_log = show_cmd_var.get()

    if not aria2_exe_path or not aria2_conf_path:
        messagebox.showerror("错误", "请填写完整的Aria2c程序路径和配置文件路径！")
        return
    if not os.path.exists(aria2_exe_path):
        messagebox.showerror("错误", f"Aria2c程序不存在：{aria2_exe_path}")
        return
    if not os.path.exists(aria2_conf_path):
        messagebox.showerror("错误", f"配置文件不存在：{aria2_conf_path}")
        return
    if not aria2_exe_path.lower().endswith("aria2c.exe"):
        messagebox.showerror("错误", "请填写正确的 aria2c.exe 可执行文件！")
        return
    if aria2_process and aria2_process.poll() is None:
        messagebox.showinfo("提示", "Aria2c 服务已经在运行中！")
        return

    try:
        cmd = [aria2_exe_path, "--conf-path", aria2_conf_path]
        if custom_params:
            cmd += custom_params.split()
        
        popen_kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
        aria2_process = subprocess.Popen(cmd,** popen_kwargs)
        is_log_running = True

        # 启动日志读取线程，线程安全
        threading.Thread(target=read_aria2_output, args=(aria2_process, "stdout"), daemon=True).start()
        threading.Thread(target=read_aria2_output, args=(aria2_process, "stderr"), daemon=True).start()

        if not show_builtin_log:
            msg = "Aria2c 启动成功！"
            if custom_params: msg += f"\n已加载自定义启动参数：{custom_params}"
            messagebox.showinfo("成功", msg)
        else:
            create_log_window()
            if custom_params: 
                msg = f"\n已加载自定义启动参数：{custom_params}"
                messagebox.showinfo("成功", msg)
        save_config()
        auto_open_web_check()
    except Exception as e:
        messagebox.showerror("启动失败", f"启动出错：{str(e)}")
        is_log_running = False

def stop_aria2():
    """停止Aria2时，清空全局日志缓存+队列，下次启动重新记录"""
    global aria2_process, is_log_running, log_window, log_content_str, output_queue
    if not aria2_process or aria2_process.poll() is not None:
        messagebox.showinfo("提示", "Aria2c 服务未运行或已停止！")
        return

    try:
        is_log_running = False
        aria2_process.terminate()
        aria2_process.wait(timeout=3)
        # 清空日志缓存+队列，重置状态
        log_content_str = ""
        while not output_queue.empty():
            output_queue.get(block=False)
        # 销毁日志窗口
        if log_window and log_window.winfo_exists():
            log_window.destroy()
        messagebox.showinfo("成功", "Aria2c 服务停止成功！日志已清空")
    except subprocess.TimeoutExpired:
        aria2_process.kill()
        log_content_str = ""
        while not output_queue.empty():
            output_queue.get(block=False)
        if log_window and log_window.winfo_exists():
            log_window.destroy()
        messagebox.showinfo("提示", "Aria2c 服务强制停止成功！日志已清空")
    except Exception as e:
        messagebox.showerror("停止失败", f"停止出错：{str(e)}")
    finally:
        aria2_process = None
        log_window = None

# 系统托盘核心功能
def hide_main_window():
    global root
    save_config()
    root.withdraw()

def show_main_window(icon=None, item=None):
    global root
    root.deiconify()
    root.focus_force()
    root.attributes('-topmost', False)

def exit_program(icon=None, item=None):
    """程序退出函数，保留退出停止Aria2判断逻辑"""
    global tray_icon, aria2_process, log_window, is_log_running, log_content_str, output_queue
    save_config()
    is_log_running = False
    
    # 仅勾选【程序退出时停止服务】才执行停止操作
    if exit_stop_aria2_var.get() and aria2_process and aria2_process.poll() is None:
        try:
            aria2_process.terminate()
            aria2_process.wait(timeout=2)
        except:
            aria2_process.kill()
        # 停止后清空日志缓存
        log_content_str = ""
        while not output_queue.empty():
            output_queue.get(block=False)
    
    # 清理日志窗口和托盘
    if log_window and log_window.winfo_exists():
        log_window.destroy()
    if tray_icon:
        tray_icon.stop()
    
    if 'mutex_handle' in globals():
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle(mutex_handle)

    root.quit()
    root.destroy()

def create_tray_menu():
    menu = pystray.Menu(
        pystray.MenuItem("显示界面", show_main_window),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("启动", start_aria2),
        pystray.MenuItem("停止", stop_aria2),
        pystray.MenuItem("日志", show_log_window),
        pystray.MenuItem("打开管理页", open_web_ui_page),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出程序", exit_program)
    )
    return menu

def start_system_tray():
    global tray_icon
    tray_icon = pystray.Icon("Aria2c 控制器", get_tray_icon(), "Aria2c 控制器", create_tray_menu())
    tray_icon.left_click = lambda icon, item: show_main_window() if root.state() == "withdrawn" else hide_main_window()
    tray_icon.run()

# 单实例运行控制
def check_single_instance():
    # 定义唯一的互斥体名称
    MUTEX_NAME = "Aria2cCG_SingleInstance_9F6B8D2A-8E0E-4F5B-9A1C-8E7D6F8C7B9A"
    # 加载kernel32.dll并调用CreateMutexW
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    h_mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    last_error = ctypes.get_last_error()
    
    # 错误码183表示互斥体已存在（已有实例运行）
    if last_error == 183:
        kernel32.CloseHandle(h_mutex)
        messagebox.showinfo("提示", "Aria2c控制器已在运行中！")
        sys.exit(0)
    # 保留句柄防止被系统回收
    return h_mutex

# 主程序入口
if __name__ == "__main__":
    mutex_handle = check_single_instance()
    root = tk.Tk()
    root.title("Aria2c 控制器")
    root.geometry("780x470")
    root.resizable(False, False)
    center_window()
    set_window_icon()

    # 1. Aria2c程序路径
    tk.Label(root, text="Aria2c程序路径：", font=("宋体", 11)).place(x=10, y=20)
    entry_exe = tk.Entry(root, width=80, font=("宋体", 10))
    entry_exe.place(x=150, y=20)
    tk.Button(root, text="浏览", command=select_aria2_exe, width=6).place(x=720, y=17)

    # 2. 配置文件路径
    tk.Label(root, text="配置文件路径：", font=("宋体", 11)).place(x=10, y=70)
    entry_conf = tk.Entry(root, width=80, font=("宋体", 10))
    entry_conf.place(x=150, y=70)
    tk.Button(root, text="浏览", command=select_aria2_conf, width=6).place(x=720, y=67)

    # 3. Web管理页面路径
    tk.Label(root, text="Web管理页面路径：", font=("宋体", 11)).place(x=10, y=120)
    entry_webui = tk.Entry(root, width=80, font=("宋体", 10))
    entry_webui.place(x=150, y=120)
    tk.Button(root, text="浏览", command=select_web_ui, width=6).place(x=720, y=117)

    # 4. 自定义启动参数
    tk.Label(root, text="自定义启动参数：", font=("宋体", 11)).place(x=10, y=170)
    entry_params = tk.Entry(root, width=80, font=("宋体", 10))
    entry_params.place(x=150, y=170)

    # 5. 勾选框1
    show_cmd_var = tk.BooleanVar(value=False)
    cb_show_cmd = tk.Checkbutton(root,text="启动服务时自动打开日志窗口",variable=show_cmd_var,font=("宋体", 11),fg="#0066CC",selectcolor="#f0f8ff",command=save_config)
    cb_show_cmd.place(x=30, y=210)

    # 6. 勾选框2
    auto_start_var = tk.BooleanVar(value=False)
    cb_auto_start = tk.Checkbutton(root,text="程序启动后自动启动服务",variable=auto_start_var,font=("宋体", 11),fg="#009900",selectcolor="#f0f8ff",command=save_config)
    cb_auto_start.place(x=30, y=240)

    # 7. 勾选框3
    start_hide_var = tk.BooleanVar(value=False)
    cb_start_hide = tk.Checkbutton(root,text="程序启动时隐藏本窗口",variable=start_hide_var,font=("宋体", 11),fg="#000099",selectcolor="#f0f8ff",command=save_config)
    cb_start_hide.place(x=30, y=270)

    # 8. 勾选框4
    auto_open_web_var = tk.BooleanVar(value=False)
    cb_auto_open_web = tk.Checkbutton(root,text="启动服务后自动打开Web管理页面",variable=auto_open_web_var,font=("宋体", 11),fg="#990099",selectcolor="#f0f8ff",command=save_config)
    cb_auto_open_web.place(x=30, y=300)

    # 9. 勾选框5
    exit_stop_aria2_var = tk.BooleanVar(value=False)
    cb_exit_stop_aria2 = tk.Checkbutton(root,text="程序退出时停止服务",variable=exit_stop_aria2_var,font=("宋体", 11),fg="#990000",selectcolor="#f0f8ff",command=save_config)
    cb_exit_stop_aria2.place(x=30, y=330)

    # 核心按钮区
    tk.Button(root, text="启动 Aria2c 服务", command=start_aria2, bg="#009900", fg="white", width=18, height=2, font=("宋体",10)).place(x=30, y=365)
    tk.Button(root, text="停止 Aria2c 服务", command=stop_aria2, bg="#CC0000", fg="white", width=18, height=2, font=("宋体",10)).place(x=230, y=365)
    tk.Button(root, text="显示日志窗口", command=show_log_window, bg="#0066CC", fg="white", width=18, height=2, font=("宋体",10)).place(x=430, y=365)
    tk.Button(root, text="打开管理页面", command=open_web_ui_page, bg="#FF6600", fg="white", width=18, height=2, font=("宋体",10)).place(x=630, y=365)

    # 底部提示
    tk.Label(root, text="Aria2c程序路径和配置文件路径是必要条件！", fg="red", font=("宋体",9)).place(x=20, y=430)
    tk.Label(root, text="程序版本：V1.0 最后更新日期：2026.01.15 HAF半个水果 https://github.com/Little-Data/aria2cCG", fg="gray", font=("宋体", 9)).place(x=20, y=446)

    # 加载配置
    load_config()

    # 启动时隐藏窗口
    if start_hide_var.get():
        root.withdraw()

    # 重写关闭事件
    root.protocol("WM_DELETE_WINDOW", hide_main_window)

    # 启动托盘
    threading.Thread(target=start_system_tray, daemon=True).start()

    # 自动启动检查
    root.after(200, auto_start_aria2_check)

    # 运行主循环
    root.mainloop()
