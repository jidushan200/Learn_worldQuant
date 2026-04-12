import subprocess
import time
from datetime import datetime
from pynput.keyboard import Controller, Key
import os

# Chrome 可执行文件的路径
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # 替换为 Chrome.exe 的实际路径

# 要打开的 blob 链接
blob_url = "blob:https://www.investing.com/703efdc4-d7bd-41c0-a307-bac70e458c05"

# 获取当前日期和时间
now = datetime.now()
formatted_date_time = now.strftime("%Y-%m-%d_%H-%M")  # 格式化为 "YYYY-MM-DD_HH-MM"

# 动态生成文件名
raw_file_name = f"XAU/USD-{formatted_date_time}"  # 原始文件名（带有非法字符）
file_name = raw_file_name.replace("/", "-")  # 替换非法字符“/”为“-”

# 保存路径
save_path = r"F:\Cal_Prince"  # 使用原始字符串，避免路径解析问题

# 确保目标路径存在
if not os.path.exists(save_path):
    os.makedirs(save_path)

# 创建键盘控制器
keyboard = Controller()

try:
    # 打开 Chrome 并加载链接
    print(f"正在使用 Chrome 打开链接: {blob_url}")
    subprocess.Popen([chrome_path, blob_url])  # 启动 Chrome 并打开链接

    # 等待弹窗出现（调整时间以确保弹窗加载完成）
    time.sleep(2)

    # 切换到英文输入法（可根据系统快捷键修改）
    print("切换到英文输入法...")
    keyboard.press(Key.ctrl)  # 按下 Ctrl 键
    keyboard.press(Key.space)  # 按下空格键（切换输入法）
    keyboard.release(Key.space)  # 松开空格键
    keyboard.release(Key.ctrl)  # 松开 Ctrl 键
    time.sleep(0.5)

    # 输入文件名
    print(f"正在输入文件名: {file_name}")
    keyboard.type(file_name)  # 模拟键盘输入文件名
    time.sleep(0.5)

    # 模拟按下 Alt+D 组合键
    print("按下 Alt+D，聚焦到路径输入框...")
    keyboard.press(Key.alt)  # 按下 Alt 键
    keyboard.press('d')  # 按下 D 键
    keyboard.release('d')  # 松开 D 键
    keyboard.release(Key.alt)  # 松开 Alt 键
    time.sleep(0.5)

    # 输入目标路径
    print(f"输入目标路径: {save_path}")
    keyboard.type(save_path)  # 模拟键盘输入路径
    # 按下回车键
    keyboard.press(Key.enter)  # 按下回车键
    keyboard.release(Key.enter)  # 松开回车键
    time.sleep(1)

    # 按下回车键
    print("按下回车键，确认保存...")
    keyboard.press(Key.enter)  # 按下回车键
    keyboard.release(Key.enter)  # 松开回车键
    print("操作完成！文件已保存。")

except FileNotFoundError as e:
    print("未找到 Chrome 可执行文件，请检查路径是否正确。")
    print(f"错误详情: {e}")

except Exception as e:
    print(f"发生错误: {e}")