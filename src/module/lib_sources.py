automation_library = r'''import time
import pyautogui
import pyperclip


# 关闭故障保护
pyautogui.FAILSAFE = False

# 设置操作间隔时间
pyautogui.PAUSE = 0.1


def mouse_click(clicks=1, interval=0, x=None, y=None, button="左"):
    """
    鼠标单击操作

    参数:
        clicks: 点击次数
        interval: 多次点击间隔时间, 单位秒
        x: x 坐标, 为 None 时点击当前位置
        y: y 坐标, 为 None 时点击当前位置
        button: 鼠标按钮, 可选 '左'/'右'/'中'
    """
    btn_map = { "左": "left", "右": "right", "中": "middle" }
    btn = btn_map.get(button)

    if btn is None:
        print(f"错误: 不支持的鼠标按钮 '{button}'，可选值: '左'/'右'/'中'")
        return

    try:
        if x is None and y is None:
            pyautogui.click(clicks=clicks, interval=interval, button=btn)
        else:
            pyautogui.click(x, y, clicks=clicks, interval=interval, button=btn)
    except Exception as e:
        print(f"鼠标单击时发生错误: {e}")


def mouse_move(x, y, move_type="屏幕"):
    """
    鼠标移动操作

    参数:
        x: 目标 x 坐标
        y: 目标 y 坐标
        move_type: 移动类型, 可选 '屏幕'/'相对'
    """
    try:
        if move_type == "屏幕":
            pyautogui.moveTo(x, y)
        elif move_type == "相对":
            pyautogui.move(x, y, duration=0.3, tween=pyautogui.easeInOutQuad)  # type: ignore
        else:
            print(f"错误: 不支持的移动类型 '{move_type}'，可选值: '屏幕'/'相对'")
    except Exception as e:
        print(f"鼠标移动时发生错误: {e}")


def mouse_scroll(clicks=1):
    """
    鼠标滚轮滚动操作

    参数:
        clicks: 滚动次数, 正数向上滚动, 负数向下滚动
    """
    try:
        pyautogui.scroll(clicks)
    except Exception as e:
        print(f"鼠标滚轮滚动时发生错误: {e}")


def mouse_button(action="按下", button="左"):
    """
    鼠标按下/松开操作

    参数:
        action: 操作类型, 可选 '按下'/'松开'
        button: 鼠标按钮, 可选 '左'/'右'/'中'
    """
    btn_map = { "左": "left", "右": "right", "中": "middle" }
    btn = btn_map.get(button)

    if btn is None:
        print(f"错误: 不支持的鼠标按钮 '{button}'，可选值: '左'/'右'/'中'")
        return

    try:
        if action == "按下":
            pyautogui.mouseDown(button=btn)
        elif action == "松开":
            pyautogui.mouseUp(button=btn)
        else:
            print(f"错误: 不支持的操作 '{action}'，可选值: '按下'/'松开'")
    except Exception as e:
        print(f"鼠标按键操作时发生错误: {e}")


def mouse_drag(x, y, duration=0.5, button="左"):
    """
    鼠标拖拽操作

    参数:
        x: 目标 x 坐标
        y: 目标 y 坐标
        duration: 拖拽持续时间, 单位秒
        button: 鼠标按钮, 可选 '左'/'右'/'中'
    """
    btn_map = { "左": "left", "右": "right", "中": "middle" }
    btn = btn_map.get(button)

    if btn is None:
        print(f"错误: 不支持的鼠标按钮 '{button}'，可选值: '左'/'右'/'中'")
        return

    try:
        pyautogui.dragTo(x, y, duration=duration, button=btn)
    except Exception as e:
        print(f"鼠标拖拽时发生错误: {e}")


def get_mouse_position():
    """
    获取当前鼠标位置

    返回:
        x, y: 当前鼠标坐标
    """
    try:
        return pyautogui.position()
    except Exception as e:
        print(f"获取鼠标位置时发生错误: {e}")
        return None


def keyboard_hotkey(*keys):
    """
    键盘快捷键操作

    参数:
        keys: 按键组合, 支持多个按键
    """
    try:
        pyautogui.hotkey(*keys)
    except Exception as e:
        print(f"键盘快捷键操作时发生错误: {e}")


def keyboard_input(text="", index=1, interval=0):
    """
    键盘输入操作

    参数:
        text: 要输入的文本内容
        index: 每次粘贴的字符数
        interval: 每次粘贴间隔时间, 单位秒
    """
    if not text:
        print("警告: 输入文本为空")
        return
    if not isinstance(index, int) or index < 1:
        print(f"错误: 每次字符数必须是大于 0 的整数, 当前为 {index}")
        return

    try:
        old_clip = pyperclip.paste()
    except Exception as e:
        print(f"获取剪贴板内容失败: {e}")
        old_clip = None

    try:
        for i in range(0, len(text), index):
            pyperclip.copy(text[i:i + index])
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(interval)
    except Exception as e:
        print(f"键盘输入时发生错误: {e}")
    finally:
        if old_clip is not None:
            try:
                pyperclip.copy(old_clip)
            except Exception as e:
                print(f"恢复剪贴板内容失败: {e}")


def type_text(text, interval=0):
    """
    模拟键盘逐字输入

    参数:
        text: 要输入的文本
        interval: 每个字符间隔时间, 单位秒
    """
    if not text:
        print("警告: 输入文本为空")
        return

    try:
        pyautogui.typewrite(text, interval=interval)
    except Exception as e:
        print(f"逐字输入时发生错误: {e}")


def press_key(key, presses=1, interval=0):
    """
    按下指定按键

    参数:
        key: 按键名称, 如 'enter', 'tab', 'esc', 'f1' 等
        presses: 按键次数
        interval: 多次按键间隔时间, 单位秒
    """
    try:
        pyautogui.press(key, presses=presses, interval=interval)
    except Exception as e:
        print(f"按键操作时发生错误: {e}")


def take_screenshot(filename="screenshot.png", region=None):
    """
    屏幕截图

    参数:
        filename: 保存文件名
        region: 截图区域, x, y, width, height, 为 None 时截取全屏
    """
    try:
        if region:
            img = pyautogui.screenshot(region=region)
        else:
            img = pyautogui.screenshot()
        img.save(filename)
        print(f"截图已保存: {filename}")
    except Exception as e:
        print(f"截图时发生错误: {e}")


def _locate(image, confidence=0.9):
    """
    屏幕找图

    参数:
        image: 图片路径
        confidence: 匹配置信度, 0 到 1

    返回:
        locateOnScreen 找到的位置, 失败时回退到默认置信度再找一次
    """
    try:
        return pyautogui.locateOnScreen(image, confidence=confidence)
    except Exception as e:
        print(f"找图时发生错误: {e}")
        return pyautogui.locateOnScreen(image)


def locate_on_screen(image, confidence=0.9):
    """
    在屏幕上查找图片位置

    参数:
        image: 图片路径
        confidence: 匹配置信度, 0-1 之间

    返回:
        x, y, width, height: 图片左上角坐标与宽高, 未找到返回 None
    """
    try:
        box = _locate(image, confidence)
        return tuple(box) if box else None
    except Exception as e:
        print(f"查找图片时发生错误: {e}")
        return None


def click_on_screen(image, clicks=1, confidence=0.9):
    """
    查找并点击图片

    参数:
        image: 图片路径
        clicks: 点击次数
        confidence: 匹配置信度, 0-1 之间
    """
    try:
        box = _locate(image, confidence)
        if box:
            left, top, width, height = box
            pyautogui.click(left + width // 2, top + height // 2, clicks=clicks)
            return
        print(f"未找到图片: {image}")
    except Exception as e:
        print(f"点击图片时发生错误: {e}")


def wait_for_image(image, timeout=10, interval=0.5, confidence=0.9):
    """
    等待图片出现在屏幕上

    参数:
        image: 图片路径
        timeout: 最长等待秒数
        interval: 每次重试的间隔秒数
        confidence: 匹配置信度, 0-1 之间

    返回:
        x, y, width, height: 找到时返回位置, 超时返回 None
    """
    start = time.time()
    while True:
        try:
            box = _locate(image, confidence)
        except Exception as e:
            print(f"等待图片时发生错误: {e}")
            return None
        if box:
            return tuple(box)
        if time.time() - start >= timeout:
            print(f"等待 {timeout} 秒仍未找到图片: {image}")
            return None
        time.sleep(interval)


def automation_library(operation, *args):
    """
    自动化操作统一入口

    参数:
        operation: 操作名称
        args: 操作参数

    返回:
        操作结果, 未知操作或出错时返回 False
    """
    operations = {
        # 鼠标操作
        "鼠标单击": mouse_click,
        "鼠标移动": mouse_move,
        "鼠标滚轮": mouse_scroll,
        "鼠标按键": mouse_button,
        "鼠标拖拽": mouse_drag,
        "获取鼠标位置": get_mouse_position,

        # 键盘操作
        "键盘快捷键": keyboard_hotkey,
        "键盘输入": keyboard_input,
        "逐字输入": type_text,
        "按键": press_key,

        # 屏幕操作
        "截图": take_screenshot,
        "查找图片": locate_on_screen,
        "点击图片": click_on_screen,
        "等待图片": wait_for_image,
    }

    try:
        operation_func = operations.get(operation)
        if operation_func:
            return operation_func(*args)
        else:
            print(f"错误: 未知的自动化操作 '{operation}'")
            return False
    except Exception as e:
        print(f"执行自动化操作 '{operation}' 时发生错误: {e}")
        return False
'''

concurrent_libraries = r'''import asyncio
import threading
import time


def create_thread(fun, args=()):
    """
    创建并启动单个线程

    参数:
        fun: 要执行的函数
        args: 函数参数元组, 默认空元组

    返回:
        Thread: 创建的线程对象
    """
    try:
        t = threading.Thread(target=fun, args=args, daemon=True)
        t.start()
        return t
    except Exception as e:
        print(f"创建线程时发生错误: {e}")
        return None


def run_threads(funcs, args_list=None):
    """
    运行多个线程

    参数:
        funcs: 函数列表
        args_list: 参数列表, 每个函数对应一组参数, 可选

    返回:
        list: 线程对象列表
    """
    try:
        threads = []

        # 如果没有提供参数列表使用空元组
        if args_list is None:
            args_list = [() for _ in funcs]

        # 确保参数列表长度与函数列表一致
        while len(args_list) < len(funcs):
            args_list.append(())

        for fun, args in zip(funcs, args_list):
            t = threading.Thread(target=fun, args=args if isinstance(args, tuple) else tuple(args), daemon=True)
            t.start()
            threads.append(t)

        return threads
    except Exception as e:
        print(f"运行多线程时发生错误: {e}")
        return []


def run_thread_with_result(fun, args=()):
    """
    运行线程并获取返回值

    参数:
        fun: 要执行的函数
        args: 函数参数元组

    返回:
        任意类型: 函数返回值
    """
    result = [None]
    error = [None]

    def wrapper():
        """执行原函数并把返回值或异常存入外部列表"""
        try:
            result[0] = fun(*args)
        except Exception as e:
            error[0] = e  # type: ignore

    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    t.join()  # 等待线程完成

    if error[0]:
        print(f"线程执行发生错误: {error[0]}")
        return None
    return result[0]


async def run_async_internal(funcs):
    """
    内部异步运行函数

    参数:
        funcs: 异步函数列表
    """
    tasks = [asyncio.create_task(func()) for func in funcs]
    await asyncio.gather(*tasks)


def run_async(funcs):
    """
    运行多个异步函数

    参数:
        funcs: 异步函数列表
    """
    try:
        asyncio.run(run_async_internal(funcs))
    except Exception as e:
        print(f"运行异步任务时发生错误: {e}")


def run_async_with_result(funcs):
    """
    运行异步函数并获取返回值

    参数:
        funcs: 异步函数列表

    返回:
        list: 所有异步函数的返回值列表
    """

    async def gather_results():
        """
        汇集全部异步任务的返回值

        返回:
            所有异步函数返回值组成的列表
        """
        tasks = [asyncio.create_task(func()) for func in funcs]
        return await asyncio.gather(*tasks)

    try:
        return asyncio.run(gather_results())
    except Exception as e:
        print(f"运行异步任务并获取结果时发生错误: {e}")
        return []


def sleep_thread(seconds):
    """
    线程休眠

    参数:
        seconds: 休眠时间, 单位秒
    """
    try:
        time.sleep(seconds)
    except Exception as e:
        print(f"线程休眠时发生错误: {e}")


def sleep_async(seconds):
    """
    异步休眠

    参数:
        seconds: 休眠时间, 单位秒
    """
    try:
        time.sleep(seconds)
    except Exception as e:
        print(f"异步休眠时发生错误: {e}")


def create_timer(interval, fun, args=(), repeat=False) -> threading.Timer | None:
    """
    创建定时器

    参数:
        interval: 间隔时间, 单位秒
        fun: 要执行的函数
        args: 函数参数元组
        repeat: 是否重复执行, 默认 False 只执行一次

    返回:
        Timer: 定时器对象, 可交给取消定时器停止
    """
    stop_event = threading.Event()
    state = { "current": None }

    def tick():
        """执行一次定时任务, 按需安排下一次"""
        if stop_event.is_set():
            return
        try:
            fun(*args)
        except Exception as err:
            print(f"定时器执行时发生错误: {err}")
        if repeat and not stop_event.is_set():
            schedule()

    def schedule():
        """安排下一次定时器触发"""
        t = threading.Timer(interval, tick)
        t.daemon = True
        t._cn_stop = stop_event  # type: ignore
        t._cn_state = state  # type: ignore
        state["current"] = t  # type: ignore
        t.start()

    try:
        schedule()
        return state["current"]
    except Exception as e:
        print(f"创建定时器时发生错误: {e}")
        return None


def create_repeat_timer(interval, fun, args=(), repeat=True):
    """
    创建重复定时器

    参数:
        interval: 间隔时间, 单位秒
        fun: 要执行的函数
        args: 函数参数元组
        repeat: 是否重复执行, 默认 True

    返回:
        Timer: 定时器对象
    """
    return create_timer(interval, fun, args, repeat)


def cancel_timer(timer):
    """
    取消定时器

    参数:
        timer: 定时器或重复定时器返回的定时器对象
    """
    if timer is None:
        print("错误: 没有可取消的定时器, 请先用「定时器」或「重复定时器」的返回值")
        return
    try:
        stop_event = getattr(timer, "_cn_stop", None)
        if stop_event is not None:
            stop_event.set()  # type: ignore
        state = getattr(timer, "_cn_state", None)
        pending = state.get("current") if state else None  # type: ignore
        if pending is not None:
            pending.cancel()  # type: ignore
        timer.cancel()
    except Exception as e:
        print(f"取消定时器时发生错误: {e}")


def concurrent_libraries(operation, *args):
    """
    并发操作统一入口

    参数:
        operation: 操作名称
        args: 操作参数

    返回:
        操作结果, 未知操作或出错时返回 False
    """
    operations = {
        # 线程操作
        "创建线程": create_thread,
        "线程": run_threads,
        "线程返回": run_thread_with_result,
        "线程休眠": sleep_thread,
        "定时器": create_timer,
        "重复定时器": create_repeat_timer,
        "取消定时器": cancel_timer,

        # 异步操作
        "异步": run_async,
        "异步返回": run_async_with_result,
        "异步休眠": sleep_async,
    }

    try:
        operation_func = operations.get(operation)
        if operation_func:
            return operation_func(*args)
        else:
            print(f"错误: 未知的并发操作 '{operation}'")
            return False
    except Exception as e:
        print(f"执行并发操作 '{operation}' 时发生错误: {e}")
        return False
'''

document_library = r'''import os
import shutil
import sys
import time


def append_file(filename, content):
    """
    追加文件内容

    参数:
        filename: 文件路径, 支持相对路径和绝对路径
        content: 要追加的内容
    """
    try:
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)  # type: ignore
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"追加文件 {filename} 时发生错误: {e}")


def delete_file(filename):
    """
    删除文件

    参数:
        filename: 文件路径
    """
    try:
        if not os.path.exists(filename):
            print(f"警告: 文件 {filename} 不存在")
            return
        os.remove(filename)
    except FileNotFoundError:
        print(f"错误: 文件 {filename} 不存在")
    except PermissionError:
        print(f"错误: 文件 {filename} 正在使用中，无法删除")
    except Exception as e:
        print(f"删除文件 {filename} 时发生错误: {e}")


def overwrite_file(filename, content):
    """
    覆盖文件内容

    参数:
        filename: 文件路径
        content: 新内容
    """
    try:
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)  # type: ignore
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"覆盖文件 {filename} 时发生错误: {e}")


def read_file(filename):
    """
    读取文件内容

    参数:
        filename: 文件路径

    返回:
        str: 文件内容, 失败返回 None
    """
    try:
        if not os.path.exists(filename):
            print(f"警告: 文件 {filename} 不存在")
            return None
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        print(f"错误: 文件 {filename} 不是文本文件，无法读取")
        return None
    except Exception as e:
        print(f"读取文件 {filename} 时发生错误: {e}")
        return None


def copy_file(src, dst):
    """
    复制文件

    参数:
        src: 源文件路径
        dst: 目标文件路径
    """
    try:
        if not os.path.exists(src):
            print(f"错误: 源文件 {src} 不存在")
            return
        dst_dir = os.path.dirname(dst)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)  # type: ignore
        shutil.copy2(src, dst)
    except Exception as e:
        print(f"复制文件 {src} 到 {dst} 时发生错误: {e}")


def move_file(src, dst):
    """
    移动文件

    参数:
        src: 源文件路径
        dst: 目标文件路径
    """
    try:
        if not os.path.exists(src):
            print(f"错误: 源文件 {src} 不存在")
            return
        dst_dir = os.path.dirname(dst)
        if dst_dir:
            os.makedirs(dst_dir, exist_ok=True)  # type: ignore
        shutil.move(src, dst)
    except Exception as e:
        print(f"移动文件 {src} 到 {dst} 时发生错误: {e}")


def rename_file(src, dst):
    """
    重命名文件

    参数:
        src: 原文件路径
        dst: 新文件路径
    """
    try:
        if not os.path.exists(src):
            print(f"错误: 文件 {src} 不存在")
            return
        os.rename(src, dst)
    except Exception as e:
        print(f"重命名文件 {src} 到 {dst} 时发生错误: {e}")


def file_exists(filename):
    """
    检查文件是否存在

    参数:
        filename: 文件路径

    返回:
        bool: 文件是否存在
    """
    return os.path.isfile(filename)


def get_file_size(filename):
    """
    获取文件大小

    参数:
        filename: 文件路径

    返回:
        int: 文件大小, 单位字节, 失败返回 None
    """
    try:
        if not os.path.exists(filename):
            print(f"错误: 文件 {filename} 不存在")
            return None
        return os.path.getsize(filename)
    except Exception as e:
        print(f"获取文件大小 {filename} 时发生错误: {e}")
        return None


def get_file_name(filename):
    """
    获取文件名

    参数:
        filename: 文件完整路径

    返回:
        str: 文件名, 含扩展名
    """
    return os.path.basename(filename)


def get_file_ext(filename):
    """
    获取文件扩展名

    参数:
        filename: 文件路径

    返回:
        str: 文件扩展名, 含点号
    """
    return os.path.splitext(filename)[1]


def delete_dir(path):
    """
    删除目录, 递归删除

    参数:
        path: 目录路径
    """
    try:
        if not os.path.exists(path):
            print(f"警告: 目录 {path} 不存在")
            return
        shutil.rmtree(path)
    except FileNotFoundError:
        print(f"错误: 目录 {path} 不存在")
    except PermissionError:
        print(f"错误: 目录 {path} 中的文件正在使用中，无法删除")
    except Exception as e:
        print(f"删除目录 {path} 时发生错误: {e}")


def create_dir(path):
    """
    创建目录, 支持递归创建

    参数:
        path: 目录路径
    """
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"创建目录 {path} 时发生错误: {e}")


def copy_dir(src, dst):
    """
    复制目录

    参数:
        src: 源目录路径
        dst: 目标目录路径
    """
    try:
        if not os.path.exists(src):
            print(f"错误: 源目录 {src} 不存在")
            return
        shutil.copytree(src, dst, dirs_exist_ok=True)
    except Exception as e:
        print(f"复制目录 {src} 到 {dst} 时发生错误: {e}")


def move_dir(src, dst):
    """
    移动目录

    参数:
        src: 源目录路径
        dst: 目标目录路径
    """
    try:
        if not os.path.exists(src):
            print(f"错误: 源目录 {src} 不存在")
            return
        shutil.move(src, dst)
    except Exception as e:
        print(f"移动目录 {src} 到 {dst} 时发生错误: {e}")


def rename_dir(src, dst):
    """
    重命名目录

    参数:
        src: 原目录路径
        dst: 新目录路径
    """
    try:
        if not os.path.exists(src):
            print(f"错误: 目录 {src} 不存在")
            return
        os.rename(src, dst)
    except Exception as e:
        print(f"重命名目录 {src} 到 {dst} 时发生错误: {e}")


def list_dir(path):
    """
    列出目录下的文件和子目录

    参数:
        path: 目录路径

    返回:
        list: 文件和目录名称列表, 失败返回 None
    """
    try:
        if not os.path.exists(path):
            print(f"错误: 目录 {path} 不存在")
            return None
        return os.listdir(path)
    except Exception as e:
        print(f"列出目录 {path} 时发生错误: {e}")
        return None


def dir_exists(path):
    """
    检查目录是否存在

    参数:
        path: 目录路径

    返回:
        bool: 目录是否存在
    """
    return os.path.isdir(path)


def get_current_dir():
    """
    获取当前工作目录

    返回:
        str: 当前工作目录路径
    """
    return os.getcwd()


def change_dir(path):
    """
    切换当前工作目录

    参数:
        path: 目标目录路径
    """
    try:
        if not os.path.exists(path):
            print(f"错误: 目录 {path} 不存在")
            return
        os.chdir(path)
    except Exception as e:
        print(f"切换目录 {path} 时发生错误: {e}")


def list_files(path, extension=None):
    """
    列出目录下的文件

    参数:
        path: 目录路径
        extension: 文件扩展名过滤, 如 '.txt', 为 None 时列出所有文件

    返回:
        list: 文件路径列表
    """
    try:
        if not os.path.exists(path):
            print(f"错误: 目录 {path} 不存在")
            return []
        files = []
        want = None
        if extension:
            want = extension.lower()
            if not want.startswith("."):
                want = "." + want
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                if want is None or item.lower().endswith(want):
                    files.append(full_path)
        return files
    except Exception as e:
        print(f"列出文件 {path} 时发生错误: {e}")
        return []


def read_lines(filename):
    """
    按行读取文件

    参数:
        filename: 文件路径

    返回:
        list: 每一行文本组成的列表, 不含行尾换行符, 失败返回 None
    """
    try:
        if not os.path.exists(filename):
            print(f"警告: 文件 {filename} 不存在")
            return None
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.rstrip("\r\n") for line in f]
    except UnicodeDecodeError:
        print(f"错误: 文件 {filename} 不是文本文件，无法读取")
        return None
    except Exception as e:
        print(f"按行读取文件 {filename} 时发生错误: {e}")
        return None


def join_path(*parts):
    """
    拼接路径

    参数:
        *parts: 任意段路径, 如 './data', '2024', 'log.txt'

    返回:
        str: 拼接后的路径, 自动使用当前系统的分隔符
    """
    try:
        valid = [str(item) for item in parts if item is not None and str(item) != ""]
        if not valid:
            return ""
        return os.path.join(*valid)
    except Exception as e:
        print(f"拼接路径 {parts} 时发生错误: {e}")
        return ""


def absolute_path(filename):
    """
    获取绝对路径

    参数:
        filename: 相对路径或绝对路径

    返回:
        str: 转换后的绝对路径, 同时去掉 . 和 ..
    """
    try:
        return os.path.abspath(filename)
    except Exception as e:
        print(f"获取绝对路径 {filename} 时发生错误: {e}")
        return ""


def get_modified_time(filename):
    """
    获取文件修改时间

    参数:
        filename: 文件路径

    返回:
        str: 格式为 年-月-日 时:分:秒 的文本, 失败返回 None
    """
    try:
        if not os.path.exists(filename):
            print(f"警告: 文件 {filename} 不存在")
            return None
        stamp = os.path.getmtime(filename)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stamp))
    except Exception as e:
        print(f"获取文件修改时间 {filename} 时发生错误: {e}")
        return None


def format_size(size_bytes):
    """
    格式化文件大小

    参数:
        size_bytes: 字节数, 通常来自「文件大小」操作

    返回:
        str: 带单位的文本, 如 1.20 MB
    """
    try:
        size = float(size_bytes)
    except (TypeError, ValueError):
        print(f"错误: 格式化大小需要数字, 收到 {size_bytes!r}")
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    step = 0
    while size >= 1024 and step < len(units) - 1:
        size /= 1024
        step += 1
    return f"{size:.0f} {units[step]}" if step == 0 else f"{size:.2f} {units[step]}"


def walk_files(path, extension=None):
    """
    递归列出目录下的所有文件

    参数:
        path: 目录路径
        extension: 扩展名过滤, 如 '.py', 为 None 时列出所有文件

    返回:
        list: 所有层级文件的完整路径列表
    """
    want = None
    if extension:
        want = extension.lower()
        if not want.startswith("."):
            want = "." + want
    try:
        if not os.path.exists(path):
            print(f"错误: 目录 {path} 不存在")
            return []
        found = []
        for root, _, names in os.walk(path):
            for item in names:
                if want is None or item.lower().endswith(want):
                    found.append(os.path.join(root, item))  # type: ignore
        return found
    except Exception as e:
        print(f"递归列出文件 {path} 时发生错误: {e}")
        return []


def get_resource_path(relative_path):
    """
    获取资源文件真实路径, 兼容打包前后

    参数:
        relative_path: 相对路径, 如 'data/config.json'

    返回:
        str: 完整路径, 包含文件名
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def document_library(operation, *args):
    """
    文件操作统一入口

    参数:
        operation: 操作名称
        args: 操作参数

    返回:
        操作结果, 未知操作或出错时返回 False
    """
    operations = {
        # 文件操作
        "追加文件": append_file,
        "删除文件": delete_file,
        "覆盖文件": overwrite_file,
        "读取文件": read_file,
        "复制文件": copy_file,
        "移动文件": move_file,
        "重命名文件": rename_file,
        "文件存在": file_exists,
        "文件大小": get_file_size,
        "文件名": get_file_name,
        "文件扩展名": get_file_ext,
        "真实路径": get_resource_path,
        "读取文件行": read_lines,
        "拼接路径": join_path,
        "绝对路径": absolute_path,
        "修改时间": get_modified_time,
        "格式化大小": format_size,

        # 目录操作
        "创建目录": create_dir,
        "删除目录": delete_dir,
        "复制目录": copy_dir,
        "移动目录": move_dir,
        "重命名目录": rename_dir,
        "列出目录": list_dir,
        "目录存在": dir_exists,
        "当前目录": get_current_dir,
        "切换目录": change_dir,
        "列出文件": list_files,
        "递归列出文件": walk_files,
    }

    try:
        operation_func = operations.get(operation)
        if operation_func:
            return operation_func(*args)
        else:
            print(f"错误: 未知的文件操作 '{operation}'")
            return False
    except Exception as e:
        print(f"执行文件操作 '{operation}' 时发生错误: {e}")
        return False
'''

interface_library = r'''import sys
from PySide6 import QtGui
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton, QRadioButton, QSlider, QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget


def create_window(title, x, y, width, height, icon="", size=None, style_sheet=""):
    """
    创建主窗口

    参数:
        title: 窗口标题
        x: 窗口 x 坐标
        y: 窗口 y 坐标
        width: 窗口宽度
        height: 窗口高度
        icon: 图标路径, 默认空
        size: 是否固定大小, 为 True 时窗口大小不可调整, 默认 None
        style_sheet: 样式表, 默认空

    返回:
        tuple: 应用对象, 窗口对象
    """
    app = QApplication.instance() or QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle(title)
    window.setGeometry(x, y, width, height)
    if icon:
        window.setWindowIcon(QtGui.QIcon(icon))
    if style_sheet:
        window.setStyleSheet(style_sheet)
    if size:
        window.setFixedSize(width, height)
    return app, window


def create_div(window, x, y, width, height, style_sheet=""):
    """
    创建容器

    参数:
        window: 窗口对象或应用窗口元组
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        style_sheet: 样式表

    返回:
        QWidget: 容器对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    div = QWidget(parent=parent)
    div.setGeometry(x, y, width, height)
    if style_sheet:
        div.setStyleSheet(style_sheet)
    return div


def create_label(window, title, x, y, width, height, font_size=10, style_sheet=""):
    """
    创建标签

    参数:
        window: 窗口对象或应用窗口元组
        title: 标签文本
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QLabel: 标签对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    label = QLabel(title, parent=parent)
    label.move(x, y)
    label.resize(width, height)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
    font = label.font()
    font.setPointSize(font_size)
    label.setFont(font)
    if style_sheet:
        label.setStyleSheet(style_sheet)
    return label


def create_input_box(window, placeholder, x, y, width, height, font_size=10, style_sheet=""):
    """
    创建单行输入框

    参数:
        window: 窗口对象或应用窗口元组
        placeholder: 占位符文本
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QLineEdit: 输入框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    input_box = QLineEdit(parent=parent)
    input_box.setPlaceholderText(placeholder)
    input_box.move(x, y)
    input_box.resize(width, height)
    font = input_box.font()
    font.setPointSize(font_size)
    input_box.setFont(font)
    if style_sheet:
        input_box.setStyleSheet(style_sheet)
    return input_box


def create_text_box(window, x, y, width, height, font_size=10, style_sheet=""):
    """
    创建多行文本框

    参数:
        window: 窗口对象或应用窗口元组
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QTextEdit: 文本框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    text_box = QTextEdit(parent=parent)
    text_box.move(x, y)
    text_box.resize(width, height)
    font = text_box.font()
    font.setPointSize(font_size)
    text_box.setFont(font)
    if style_sheet:
        text_box.setStyleSheet(style_sheet)
    return text_box


def create_combo_box(window, items, x, y, width, height, font_size=10, style_sheet=""):
    """
    创建下拉框

    参数:
        window: 窗口对象或应用窗口元组
        items: 选项列表
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QComboBox: 下拉框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    combo_box = QComboBox(parent=parent)
    combo_box.addItems(items)
    combo_box.move(x, y)
    combo_box.resize(width, height)
    font = combo_box.font()
    font.setPointSize(font_size)
    combo_box.setFont(font)
    if style_sheet:
        combo_box.setStyleSheet(style_sheet)
    return combo_box


def create_button(window, title, x, y, width, height, click_func=None, font_size=10, style_sheet=""):
    """
    创建按钮

    参数:
        window: 窗口对象或应用窗口元组
        title: 按钮文本
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        click_func: 点击事件函数, 可选
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QPushButton: 按钮对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    button = QPushButton(title, parent=parent)
    button.move(x, y)
    button.resize(width, height)
    font = button.font()
    font.setPointSize(font_size)
    button.setFont(font)
    if style_sheet:
        button.setStyleSheet(style_sheet)
    if click_func:
        button.clicked.connect(click_func)
    return button


def create_check_box(window, title, x, y, width, height, checked=False, font_size=10, style_sheet=""):
    """
    创建复选框

    参数:
        window: 窗口对象或应用窗口元组
        title: 复选框文本
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        checked: 是否默认选中, 默认 False
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QCheckBox: 复选框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    check_box = QCheckBox(title, parent=parent)
    check_box.move(x, y)
    check_box.resize(width, height)
    check_box.setChecked(checked)
    font = check_box.font()
    font.setPointSize(font_size)
    check_box.setFont(font)
    if style_sheet:
        check_box.setStyleSheet(style_sheet)
    return check_box


def create_radio_button(window, title, x, y, width, height, checked=False, font_size=10, style_sheet=""):
    """
    创建单选框

    参数:
        window: 窗口对象或应用窗口元组
        title: 单选框文本
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        checked: 是否默认选中, 默认 False
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QRadioButton: 单选框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    radio_button = QRadioButton(title, parent=parent)
    radio_button.move(x, y)
    radio_button.resize(width, height)
    radio_button.setChecked(checked)
    font = radio_button.font()
    font.setPointSize(font_size)
    radio_button.setFont(font)
    if style_sheet:
        radio_button.setStyleSheet(style_sheet)
    return radio_button


def create_progress_bar(window, x, y, width, height, value=0, style_sheet=""):
    """
    创建进度条

    参数:
        window: 窗口对象或应用窗口元组
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        value: 初始值, 0 到 100, 默认 0
        style_sheet: 样式表

    返回:
        QProgressBar: 进度条对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    progress_bar = QProgressBar(parent=parent)
    progress_bar.move(x, y)
    progress_bar.resize(width, height)
    progress_bar.setValue(value)
    if style_sheet:
        progress_bar.setStyleSheet(style_sheet)
    return progress_bar


def create_slider(window, x, y, width, height, min_value=0, max_value=100, value=50, style_sheet=""):
    """
    创建滑块

    参数:
        window: 窗口对象或应用窗口元组
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        min_value: 最小值, 默认 0
        max_value: 最大值, 默认 100
        value: 初始值, 默认 50
        style_sheet: 样式表

    返回:
        QSlider: 滑块对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    slider = QSlider(Qt.Orientation.Horizontal, parent=parent)
    slider.move(x, y)
    slider.resize(width, height)
    slider.setRange(min_value, max_value)
    slider.setValue(value)
    if style_sheet:
        slider.setStyleSheet(style_sheet)
    return slider


def create_spin_box(window, x, y, width, height, min_value=0, max_value=100, value=50, font_size=10, style_sheet=""):
    """
    创建数字输入框

    参数:
        window: 窗口对象或应用窗口元组
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        min_value: 最小值, 默认 0
        max_value: 最大值, 默认 100
        value: 初始值, 默认 50
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QSpinBox: 数字输入框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    spin_box = QSpinBox(parent=parent)
    spin_box.move(x, y)
    spin_box.resize(width, height)
    spin_box.setRange(min_value, max_value)
    spin_box.setValue(value)
    font = spin_box.font()
    font.setPointSize(font_size)
    spin_box.setFont(font)
    if style_sheet:
        spin_box.setStyleSheet(style_sheet)
    return spin_box


def create_group_box(window, title, x, y, width, height, style_sheet=""):
    """
    创建分组框

    参数:
        window: 窗口对象或应用窗口元组
        title: 分组框标题
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        style_sheet: 样式表

    返回:
        QGroupBox: 分组框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    group_box = QGroupBox(title, parent=parent)
    group_box.setGeometry(x, y, width, height)
    if style_sheet:
        group_box.setStyleSheet(style_sheet)
    return group_box


def show_alert(title, message, btn="确定", icon=""):
    """
    创建信息弹窗

    参数:
        title: 弹窗标题
        message: 弹窗内容
        btn: 按钮文本, 默认确定
        icon: 图标路径, 默认空
    """
    msg_box = QMessageBox()
    if icon:
        msg_box.setWindowIcon(QtGui.QIcon(icon))
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Information)
    ok_button = msg_box.addButton(btn, QMessageBox.ButtonRole.AcceptRole)
    msg_box.exec()
    if msg_box.clickedButton() == ok_button:
        return


def show_confirm(title, message, btn1="确定", btn2="取消", icon=""):
    """
    创建确认弹窗

    参数:
        title: 弹窗标题
        message: 弹窗内容
        btn1: 确认按钮文本, 默认确定
        btn2: 取消按钮文本, 默认取消
        icon: 图标路径, 默认空

    返回:
        bool: 点击确认返回 True, 点击取消返回 False
    """
    msg_box = QMessageBox()
    if icon:
        msg_box.setWindowIcon(QtGui.QIcon(icon))
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Question)
    ok_button = msg_box.addButton(btn1, QMessageBox.ButtonRole.AcceptRole)
    cancel_button = msg_box.addButton(btn2, QMessageBox.ButtonRole.RejectRole)
    msg_box.exec()
    if msg_box.clickedButton() == ok_button:
        return True
    if msg_box.clickedButton() == cancel_button:
        return False
    return None


def show_warning(title, message, btn="确定", icon=""):
    """
    创建警告弹窗

    参数:
        title: 弹窗标题
        message: 弹窗内容
        btn: 按钮文本, 默认确定
        icon: 图标路径, 默认空
    """
    msg_box = QMessageBox()
    if icon:
        msg_box.setWindowIcon(QtGui.QIcon(icon))
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    ok_button = msg_box.addButton(btn, QMessageBox.ButtonRole.AcceptRole)
    msg_box.exec()
    if msg_box.clickedButton() == ok_button:
        return


def show_error(title, message, btn="确定", icon=""):
    """
    创建错误弹窗

    参数:
        title: 弹窗标题
        message: 弹窗内容
        btn: 按钮文本, 默认确定
        icon: 图标路径, 默认空
    """
    msg_box = QMessageBox()
    if icon:
        msg_box.setWindowIcon(QtGui.QIcon(icon))
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    ok_button = msg_box.addButton(btn, QMessageBox.ButtonRole.AcceptRole)
    msg_box.exec()
    if msg_box.clickedButton() == ok_button:
        return


def get_text(input_box):
    """
    获取输入框, 下拉框, 数字框, 滑块或文本框的内容

    参数:
        input_box: 输入类组件对象

    返回:
        文本内容, 数字框和滑块返回数字, 类型为 str 或 int
    """
    if isinstance(input_box, QComboBox):
        return input_box.currentText()
    if isinstance(input_box, (QSpinBox, QSlider)):
        return input_box.value()
    if isinstance(input_box, QTextEdit):
        return input_box.toPlainText()
    return input_box.text()


def set_text(input_box, text):
    """
    设置输入框的内容

    参数:
        input_box: 输入框, 下拉框或数字框对象
        text: 要设置的文本, 数字框会自动转成整数
    """
    if isinstance(input_box, QLineEdit):
        input_box.setText(str(text))
        return
    if isinstance(input_box, QComboBox):
        # 下拉框只能切到已有的选项
        index = input_box.findText(str(text))
        if index >= 0:
            input_box.setCurrentIndex(index)
            return
        print(f"错误: 下拉框里没有选项 {text}")
        return
    if isinstance(input_box, QSpinBox):
        input_box.setValue(int(text))
        return


def set_text_box_text(text_box, text):
    """
    设置多行文本框的内容

    参数:
        text_box: 文本框对象
        text: 要设置的文本
    """
    if isinstance(text_box, QTextEdit):
        text_box.setPlainText(text)
        return


def get_text_box_text(text_box):
    """
    获取多行文本框的内容

    参数:
        text_box: 文本框对象

    返回:
        str: 文本内容
    """
    if isinstance(text_box, QTextEdit):
        return text_box.toPlainText()
    return ""


def set_progress_value(progress_bar, value):
    """
    设置进度条的值

    参数:
        progress_bar: 进度条对象
        value: 进度值, 0 到 100
    """
    if isinstance(progress_bar, QProgressBar):
        progress_bar.setValue(value)
        return


def is_checked(check_box):
    """
    获取复选框或单选框的选中状态

    参数:
        check_box: 复选框或单选框对象

    返回:
        bool: 是否选中
    """
    if isinstance(check_box, (QCheckBox, QRadioButton)):
        return check_box.isChecked()
    return False


def set_checked(check_box, checked):
    """
    设置复选框或单选框的选中状态

    参数:
        check_box: 复选框或单选框对象
        checked: 是否选中
    """
    if isinstance(check_box, (QCheckBox, QRadioButton)):
        check_box.setChecked(checked)
        return


def set_enabled(widget, enabled):
    """
    设置组件的启用或禁用状态

    参数:
        widget: 任意界面组件对象
        enabled: 是否启用
    """
    try:
        widget.setEnabled(enabled)
    except Exception as e:
        print(f"设置组件状态时发生错误: {e}")


def set_visible(widget, visible):
    """
    设置组件的显示或隐藏状态

    参数:
        widget: 任意界面组件对象
        visible: 是否显示
    """
    try:
        widget.setVisible(visible)
    except Exception as e:
        print(f"设置组件可见性时发生错误: {e}")


def select_file(title="选择文件", files_filter="所有文件 (*)"):
    """
    打开选择文件对话框

    参数:
        title: 对话框标题
        files_filter: 文件类型过滤, 如 文本文件 *.txt;;图片 *.png *.jpg

    返回:
        str: 选中的文件完整路径, 取消返回空字符串
    """
    try:
        path, _ = QFileDialog.getOpenFileName(None, title, "", files_filter)
        return path
    except Exception as e:
        print(f"打开文件对话框时发生错误: {e}")
        return ""


def select_dir(title="选择目录"):
    """
    打开选择目录对话框

    参数:
        title: 对话框标题

    返回:
        str: 选中的目录完整路径, 取消返回空字符串
    """
    try:
        return QFileDialog.getExistingDirectory(None, title)
    except Exception as e:
        print(f"打开目录对话框时发生错误: {e}")
        return ""


def _fill_table(table, rows):
    """
    把二维列表填进表格, 单元格一律转成文本

    参数:
        table: 表格对象
        rows: 二维数据列表
    """
    data = [list(row) for row in rows]
    table.setRowCount(len(data))
    for r, row in enumerate(data):
        for c, cell in enumerate(row):
            table.setItem(r, c, QTableWidgetItem(str(cell)))


def create_table(window, headers, rows, x, y, width, height, style_sheet=""):
    """
    创建表格

    参数:
        window: 窗口对象或应用窗口元组
        headers: 表头列表
        rows: 数据列表
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        style_sheet: 样式表

    返回:
        QTableWidget: 表格对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    table = QTableWidget(parent=parent)
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels([str(h) for h in headers])
    _fill_table(table, rows)
    table.move(x, y)
    table.resize(width, height)
    if style_sheet:
        table.setStyleSheet(style_sheet)
    return table


def set_table_data(table, rows):
    """
    更新表格的全部数据

    参数:
        table: 表格对象
        rows: 新的数据列表
    """
    try:
        if not isinstance(table, QTableWidget):
            print("错误: 第一个参数必须是表格创建的对象")
            return
        _fill_table(table, rows)
    except Exception as e:
        print(f"更新表格数据时发生错误: {e}")


def get_table_data(table):
    """
    读取表格的全部数据

    参数:
        table: 表格对象

    返回:
        list: 二维文本列表, 失败返回 None
    """
    try:
        if not isinstance(table, QTableWidget):
            print("错误: 参数必须是表格创建的对象")
            return None
        result = []
        for r in range(table.rowCount()):
            row = []
            for c in range(table.columnCount()):
                item = table.item(r, c)
                row.append(item.text() if item else "")
            result.append(row)
        return result
    except Exception as e:
        print(f"读取表格数据时发生错误: {e}")
        return None


def create_list_widget(window, items, x, y, width, height, font_size=10, style_sheet=""):
    """
    创建列表组件

    参数:
        window: 窗口对象或应用窗口元组
        items: 选项列表
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        font_size: 字体大小, 默认 10
        style_sheet: 样式表

    返回:
        QListWidget: 列表对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    list_widget = QListWidget(parent=parent)
    list_widget.addItems([str(item) for item in items])
    list_widget.move(x, y)
    list_widget.resize(width, height)
    font = list_widget.font()
    font.setPointSize(font_size)
    list_widget.setFont(font)
    if style_sheet:
        list_widget.setStyleSheet(style_sheet)
    return list_widget


def get_selected_item(list_widget):
    """
    获取列表当前选中的项

    参数:
        list_widget: 列表对象

    返回:
        str: 选中的文本, 没有选中返回 None
    """
    try:
        item = list_widget.currentItem()
        return item.text() if item else None
    except Exception as e:
        print(f"读取列表选中项时发生错误: {e}")
        return None


def create_image_box(window, image_path, x, y, width, height, style_sheet=""):
    """
    创建图片显示框

    参数:
        window: 窗口对象或应用窗口元组
        image_path: 图片文件路径
        x: x 坐标
        y: y 坐标
        width: 宽度
        height: 高度
        style_sheet: 样式表

    返回:
        QLabel: 图片框对象
    """
    parent = window[1] if isinstance(window, tuple) else window
    label = QLabel(parent=parent)
    pix = QtGui.QPixmap(image_path)
    if not pix.isNull():
        label.setPixmap(
            pix.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ),
        )
    else:
        print(f"警告: 无法加载图片 {image_path}")
    label.move(x, y)
    label.resize(width, height)
    if style_sheet:
        label.setStyleSheet(style_sheet)
    return label


def gui_timer(milliseconds, fun, repeat=True):
    """
    创建界面定时器

    参数:
        milliseconds: 间隔毫秒数, 1 秒等于 1000
        fun: 到点要执行的函数
        repeat: 是否重复执行, 默认 True

    返回:
        QTimer: 定时器对象, 可交给停止界面定时器
    """
    try:
        timer = QTimer()
        timer.timeout.connect(fun)
        timer.setSingleShot(not repeat)
        timer.start(int(milliseconds))
        return timer
    except Exception as e:
        print(f"创建界面定时器时发生错误: {e}")
        return None


def stop_gui_timer(timer):
    """
    停止界面定时器

    参数:
        timer: 界面定时器返回的对象
    """
    try:
        if timer is None:
            print("错误: 没有可停止的定时器, 请先用界面定时器的返回值")
            return
        timer.stop()
    except Exception as e:
        print(f"停止界面定时器时发生错误: {e}")


def apply_layout(container, direction="纵向", margin=10, spacing=10):
    """
    给容器或窗口设置布局

    参数:
        container: 窗口对象, 容器对象或应用窗口元组
        direction: 排列方向, 纵向或横向
        margin: 四周留白, 像素, 默认 10
        spacing: 组件间距, 像素, 默认 10
    """
    try:
        parent = container[1] if isinstance(container, tuple) else container
        layout = QHBoxLayout() if str(direction) == "横向" else QVBoxLayout()
        central = None
        if isinstance(parent, QMainWindow):
            central = QWidget()
            parent.setCentralWidget(central)
            central.setLayout(layout)
        else:
            parent.setLayout(layout)

        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        children = parent.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for child in children:
            if central is not None and child is central:
                continue
            layout.addWidget(child)
        layout.activate()
    except Exception as e:
        print(f"设置布局时发生错误: {e}")


def run_app(wins):
    """
    启动程序, 显示窗口

    参数:
        wins: 应用对象和窗口对象元组
    """
    window = wins[1] if isinstance(wins, tuple) else wins
    window.show()
    app = wins[0] if isinstance(wins, tuple) else QApplication.instance()
    sys.exit(app.exec())  # type: ignore


def interface_library(operation, *args):
    """
    界面操作统一入口

    参数:
        operation: 操作名称
        args: 操作参数

    返回:
        操作结果, 未知操作或出错时返回 False
    """
    operations = {
        # 窗口组件
        "窗口": create_window,
        "盒子": create_div,
        "分组框": create_group_box,

        # 输入组件
        "标签": create_label,
        "输入框": create_input_box,
        "文本框": create_text_box,
        "下拉框": create_combo_box,
        "按钮": create_button,
        "复选框": create_check_box,
        "单选框": create_radio_button,
        "进度条": create_progress_bar,
        "滑块": create_slider,
        "数字框": create_spin_box,
        "表格": create_table,
        "列表": create_list_widget,
        "图片": create_image_box,

        # 对话框
        "弹窗": show_alert,
        "确认框": show_confirm,
        "警告": show_warning,
        "错误": show_error,
        "选择文件": select_file,
        "选择目录": select_dir,

        # 内容操作
        "内容": get_text,
        "设置内容": set_text,
        "获取文本": get_text_box_text,
        "设置文本": set_text_box_text,
        "设置进度": set_progress_value,
        "是否选中": is_checked,
        "设置选中": set_checked,
        "启用": set_enabled,
        "显示": set_visible,
        "设置表格": set_table_data,
        "表格内容": get_table_data,
        "列表选中项": get_selected_item,

        # 程序控制
        "运行": run_app,
        "界面定时器": gui_timer,
        "停止界面定时器": stop_gui_timer,
        "布局": apply_layout,
    }

    try:
        operation_func = operations.get(operation)
        if operation_func:
            return operation_func(*args)
        else:
            print(f"错误: 未知的界面操作 '{operation}'")
            return False
    except Exception as e:
        print(f"执行界面操作 '{operation}' 时发生错误: {e}")
        return False
'''

network_library = r'''import os
import threading
import requests
import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request


app = FastAPI()


def _read_response(response):
    """
    读取响应体

    参数:
        response: requests 的响应对象

    返回:
        能解析成 JSON 就返回 dict/list, 否则返回文本, 空响应返回空字符串
    """
    try:
        return response.json()
    except ValueError:
        return response.text


def _handle_response(response):
    """
    统一处理响应, 2xx 返回解析后的数据, 否则返回状态码和文本

    参数:
        response: requests 的响应对象

    返回:
        dict/list/str 或 状态码和文本的元组
    """
    if 200 <= response.status_code < 300:
        return _read_response(response)
    return response.status_code, response.text


def create_router(path, logic, method):
    """
    创建路由

    参数:
        path: 接口路径
        logic: 处理函数, 必须是异步函数
        method: 请求方法, POST 或 GET

    返回:
        APIRouter: 路由对象
    """
    router = APIRouter()

    async def process_request(request):
        """
        按请求方法解析参数并调用业务逻辑

        参数:
            request: FastAPI 请求对象

        返回:
            业务逻辑返回的结果
        """
        response_data = { "url": str(request.url), "status": 200 }
        if request.method == "GET":
            query_params = request.query_params
            for key, value in query_params.items():
                response_data[key] = value
            return await logic(response_data)
        else:
            body = await request.json()
            body.update(response_data)
            data = await logic(body)
            return data

    if method.upper() == "POST":
        @router.post(path)
        async def _post_request(request: Request):
            """
            POST 路由处理函数

            参数:
                request: FastAPI 请求对象

            返回:
                process_request 的处理结果
            """
            return await process_request(request)
    elif method.upper() == "GET":
        @router.get(path)
        async def _get_request(request: Request):
            """
            GET 路由处理函数

            参数:
                request: FastAPI 请求对象

            返回:
                process_request 的处理结果
            """
            return await process_request(request)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的请求方法: {method}")

    return router


def register_router(url, logic, method):
    """
    注册路由到服务器

    参数:
        url: 接口路径
        logic: 处理函数, 必须是异步函数
        method: 请求方法, POST 或 GET
    """
    router = create_router(url, logic, method)
    app.include_router(router)


_server_state = { "server": None, "thread": None }


def run_server(host, port):
    """
    启动 HTTP 服务器

    参数:
        host: 服务器地址
        port: 端口号
    """
    running = _server_state["server"]
    if running is not None and not running.should_exit:  # type: ignore
        print("服务器已在运行, 如需重启请先调用 网络*('停止')")
        return

    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)

    def runs():
        """在后台线程中运行 uvicorn 服务器"""
        server.run()

    thread = threading.Thread(target=runs, daemon=True)
    _server_state["server"] = server  # type: ignore
    _server_state["thread"] = thread  # type: ignore
    thread.start()
    print(f"服务器已启动: http://{host}:{port}")


def stop_server():
    """
    停止 HTTP 服务器
    """
    server = _server_state["server"]
    if server is None:
        print("服务器还没有启动")
        return

    server.should_exit = True  # type: ignore
    thread = _server_state["thread"]
    if thread is not None:
        thread.join(timeout=5)  # type: ignore
    _server_state["server"] = None
    _server_state["thread"] = None
    print("服务器已停止")


def request_any(url, method="GET", data=None, headers=None, timeout=10):
    """
    发起任意方法的 HTTP 请求

    参数:
        url: 请求地址
        method: 请求方法, GET, POST, PUT, DELETE, PATCH, HEAD 等
        data: 请求数据, 字典类型, GET 时作为查询参数
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 10

    返回:
        dict/list/str: 2xx 返回响应体, 否则返回状态码和文本
    """
    try:
        name = str(method or "GET").upper()
        if name in ("GET", "HEAD", "DELETE", "OPTIONS"):
            response = requests.request(name, url, params=data, headers=headers, timeout=timeout)
        else:
            response = requests.request(name, url, json=data, headers=headers, timeout=timeout)
        return _handle_response(response)
    except Exception as e:
        print(f"发起 {method} 请求 {url} 时发生错误: {e}")
        return None


def download_file_progress(url, save_path, headers=None, timeout=60):
    """
    下载文件并显示进度

    参数:
        url: 文件下载地址
        save_path: 保存路径
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 60
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        if not (200 <= response.status_code < 300):
            print(f"下载文件失败: {response.status_code}")
            return

        total = int(response.headers.get("content-length") or 0)
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)  # type: ignore

        done = 0
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                done += len(chunk)
                if total:
                    percent = done * 100 / total
                    print(f"\r下载中 {percent:5.1f}%  {done / 1048576:.2f}/{total / 1048576:.2f} MB", end="")
                else:
                    print(f"\r已下载 {done / 1048576:.2f} MB", end="")
        print()
        print(f"下载完成: {save_path}")
    except Exception as e:
        print(f"\n下载文件 {url} 时发生错误: {e}")


def post_request(url, data, headers=None, timeout=10):
    """
    发起 POST 请求

    参数:
        url: 请求地址
        data: 请求数据, 字典类型
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 10

    返回:
        dict/tuple: 成功返回 JSON 数据, 失败返回状态码和错误信息
    """
    try:
        response = requests.post(url, json=data, headers=headers, timeout=timeout)
        return _handle_response(response)
    except requests.exceptions.Timeout:
        print(f"POST 请求 {url} 超时")
        return None
    except requests.exceptions.ConnectionError:
        print(f"POST 请求 {url} 连接失败")
        return None
    except Exception as e:
        print(f"发起 POST 请求 {url} 时发生错误: {e}")
        return None


def get_request(url, params=None, headers=None, timeout=10):
    """
    发起 GET 请求

    参数:
        url: 请求地址
        params: 请求参数, 可选, 字典类型
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 10

    返回:
        dict/tuple: 成功返回 JSON 数据, 失败返回状态码和错误信息
    """
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        return _handle_response(response)
    except requests.exceptions.Timeout:
        print(f"GET 请求 {url} 超时")
        return None
    except requests.exceptions.ConnectionError:
        print(f"GET 请求 {url} 连接失败")
        return None
    except Exception as e:
        print(f"发起 GET 请求 {url} 时发生错误: {e}")
        return None


def put_request(url, data, headers=None, timeout=10):
    """
    发起 PUT 请求

    参数:
        url: 请求地址
        data: 请求数据, 字典类型
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 10

    返回:
        dict/tuple: 成功返回 JSON 数据, 失败返回状态码和错误信息
    """
    try:
        response = requests.put(url, json=data, headers=headers, timeout=timeout)
        return _handle_response(response)
    except requests.exceptions.Timeout:
        print(f"PUT 请求 {url} 超时")
        return None
    except requests.exceptions.ConnectionError:
        print(f"PUT 请求 {url} 连接失败")
        return None
    except Exception as e:
        print(f"发起 PUT 请求 {url} 时发生错误: {e}")
        return None


def delete_request(url, headers=None, timeout=10):
    """
    发起 DELETE 请求

    参数:
        url: 请求地址
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 10

    返回:
        dict/tuple: 成功返回 JSON 数据, 失败返回状态码和错误信息
    """
    try:
        response = requests.delete(url, headers=headers, timeout=timeout)
        return _handle_response(response)
    except requests.exceptions.Timeout:
        print(f"DELETE 请求 {url} 超时")
        return None
    except requests.exceptions.ConnectionError:
        print(f"DELETE 请求 {url} 连接失败")
        return None
    except Exception as e:
        print(f"发起 DELETE 请求 {url} 时发生错误: {e}")
        return None


def download_file(url, save_path, headers=None, timeout=30):
    """
    下载文件

    参数:
        url: 文件下载地址
        save_path: 保存路径
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 30
    """
    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        if 200 <= response.status_code < 300:
            save_dir = os.path.dirname(save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)  # type: ignore
            with open(save_path, 'wb') as f:
                f.writelines(response.iter_content(chunk_size=8192))
            return
        print(f"下载文件失败: {response.status_code}")
    except Exception as e:
        print(f"下载文件 {url} 时发生错误: {e}")


def upload_file(url, file_path, field_name="file", headers=None, timeout=30):
    """
    上传文件

    参数:
        url: 上传地址
        file_path: 文件路径
        field_name: 表单字段名, 默认 file
        headers: 请求头, 可选
        timeout: 超时时间, 单位秒, 默认 30

    返回:
        dict/tuple: 成功返回 JSON 数据, 失败返回状态码和错误信息
    """
    try:
        with open(file_path, 'rb') as f:
            files = { field_name: f }
            response = requests.post(url, files=files, headers=headers, timeout=timeout)
        return _handle_response(response)
    except Exception as e:
        print(f"上传文件 {file_path} 时发生错误: {e}")
        return None


def network_library(operation=None, *args):
    """
    网络操作统一入口

    参数:
        operation: 操作名称
        args: 操作参数

    返回:
        操作结果, 未知操作或出错时返回 False
    """
    operations = {
        "创建路由": create_router,
        "路由": register_router,
        "启动": run_server,
        "停止": stop_server,
        "获取请求": get_request,
        "发送请求": post_request,
        "更新请求": put_request,
        "删除请求": delete_request,
        "通用请求": request_any,
        "下载": download_file,
        "下载进度": download_file_progress,
        "上传": upload_file,
    }

    try:
        operation_func = operations.get(operation)
        if operation_func:
            return operation_func(*args)
        else:
            print(f"错误: 未知的网络操作 '{operation}'")
            return False
    except Exception as e:
        print(f"执行网络操作 '{operation}' 时发生错误: {e}")
        return False
'''

random_library = r'''import random


def generate_random_int(minValue, maxValue):
    """
    生成随机整数

    参数:
        minValue: 最小值, 包含
        maxValue: 最大值, 包含

    返回:
        int: 随机整数, 失败返回 None
    """
    try:
        if minValue > maxValue:
            print(f"错误: 最小值 {minValue} 不能大于最大值 {maxValue}")
            return None
        return random.randint(minValue, maxValue)
    except Exception as e:
        print(f"生成随机整数时发生错误: {e}")
        return None


def generate_random_float(minValue, maxValue):
    """
    生成随机浮点数

    参数:
        minValue: 最小值
        maxValue: 最大值

    返回:
        float: 随机浮点数, 失败返回 None
    """
    try:
        if minValue > maxValue:
            print(f"错误: 最小值 {minValue} 不能大于最大值 {maxValue}")
            return None
        return random.uniform(minValue, maxValue)
    except Exception as e:
        print(f"生成随机浮点数时发生错误: {e}")
        return None


def choose_random_element(*elements):
    """
    从多个元素中随机选择一个

    参数:
        *elements: 可变参数, 可以是任意数量的元素

    返回:
        任意类型: 随机选择的元素, 失败返回 None
    """
    try:
        if not elements:
            print("错误: 至少需要提供一个元素")
            return None
        return random.choice(elements)
    except Exception as e:
        print(f"随机选择元素时发生错误: {e}")
        return None


def choose_random_from_list(lst):
    """
    从列表中随机选择一个元素

    参数:
        lst: 列表

    返回:
        任意类型: 随机选择的元素, 失败返回 None
    """
    try:
        if not lst:
            print("错误: 列表不能为空")
            return None
        return random.choice(lst)
    except Exception as e:
        print(f"从列表随机选择时发生错误: {e}")
        return None


def shuffle_list(lst):
    """
    随机打乱列表, 返回新列表, 不修改原列表

    参数:
        lst: 要被打乱的列表

    返回:
        list: 打乱后的新列表, 失败返回 None
    """
    try:
        if not lst:
            print("错误: 列表不能为空")
            return None
        shuffled_list = lst.copy()
        random.shuffle(shuffled_list)
        return shuffled_list
    except Exception as e:
        print(f"打乱列表时发生错误: {e}")
        return None


def generate_random_sample(lst, k):
    """
    从列表中随机抽样, 不放回

    参数:
        lst: 源列表
        k: 抽样数量

    返回:
        list: 抽样结果列表, 失败返回 None
    """
    try:
        if not lst:
            print("错误: 列表不能为空")
            return None
        if k > len(lst):
            print(f"错误: 抽样数量 {k} 不能大于列表长度 {len(lst)}")
            return None
        return random.sample(lst, k)
    except Exception as e:
        print(f"随机抽样时发生错误: {e}")
        return None


def generate_random_choices(lst, k, weights=None):
    """
    从列表中随机抽样, 有放回

    参数:
        lst: 源列表
        k: 抽样数量
        weights: 权重列表, 可选

    返回:
        list: 抽样结果列表, 失败返回 None
    """
    try:
        if not lst:
            print("错误: 列表不能为空")
            return None
        return random.choices(lst, weights=weights, k=k)
    except Exception as e:
        print(f"有放回抽样时发生错误: {e}")
        return None


def set_seed(seed):
    """
    设置随机数种子

    参数:
        seed: 种子值, 整数
    """
    try:
        random.seed(seed)
    except Exception as e:
        print(f"设置随机种子时发生错误: {e}")


def generate_random_bool():
    """
    生成随机布尔值

    返回:
        bool: 真或假, 各占一半概率
    """
    return random.choice([True, False])


def generate_captcha(length=4, char_type="数字"):
    """
    生成随机验证码

    参数:
        length: 验证码位数, 默认 4 位
        char_type: 字符类型, 可选数字, 字母, 混合, 默认数字

    返回:
        str: 验证码文本, 失败返回空字符串
    """
    digits = "0123456789"
    letters = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
    pools = { "数字": digits, "字母": letters, "混合": digits + letters }
    try:
        pool = pools.get(str(char_type), digits)
        count = int(length)
        if count <= 0:
            print(f"错误: 验证码位数必须大于0, 收到 {length}")
            return ""
        return "".join(random.choice(pool) for _ in range(count))
    except Exception as e:
        print(f"生成验证码时发生错误: {e}")
        return ""


def choose_by_weight(lst, weights):
    """
    按权重随机选择

    参数:
        lst: 候选列表
        weights: 权重列表, 和候选一一对应, 数字越大越容易被选中

    返回:
        任意类型: 选中的元素, 失败返回 None
    """
    try:
        if not lst:
            print("错误: 列表不能为空")
            return None
        if weights is None or len(weights) != len(lst):
            print(f"错误: 权重个数 {0 if weights is None else len(weights)} 必须和列表长度 {len(lst)}一致")
            return None
        return random.choices(lst, weights=weights, k=1)[0]
    except Exception as e:
        print(f"按权重选择时发生错误: {e}")
        return None


def random_library(operation=None, *args):
    """
    随机操作统一入口

    参数:
        operation: 操作名称
        args: 操作参数

    返回:
        操作结果, 未知操作或出错时返回 False
    """
    operations = {
        "整数": generate_random_int,
        "浮点数": generate_random_float,
        "元素": choose_random_element,
        "从列表选择": choose_random_from_list,
        "列表": shuffle_list,
        "抽样": generate_random_sample,
        "有放回抽样": generate_random_choices,
        "设置种子": set_seed,
        "布尔": generate_random_bool,
        "验证码": generate_captcha,
        "按权重选择": choose_by_weight,
    }

    try:
        operation_func = operations.get(operation)
        if operation_func:
            return operation_func(*args)
        else:
            print(f"错误: 不支持的随机操作 '{operation}'")
            return False
    except Exception as e:
        print(f"执行随机操作 '{operation}' 时发生错误: {e}")
        return False
'''

system_library = r'''import hashlib
import os
import subprocess
import time
import webbrowser
import winreg
import psutil
from pycaw.pycaw import AudioUtilities


# 发送系统通知时使用的应用标识与默认来源名
_NOTIFY_APP_ID = "PandaEditor"
_NOTIFY_APP_NAME = "熊猫编辑器"


def _run_powershell(script):
    """
    执行一段 PowerShell 脚本并取回标准输出

    参数:
        script: 要执行的脚本内容

    返回:
        str: 去掉首尾空白的输出, 失败返回空字符串
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return (result.stdout or "").strip()
    except Exception as e:
        print(f"执行系统脚本失败: {e}")
        return ""


def _ps_text(text):
    """
    把文本转成 PowerShell 单引号字面量

    参数:
        text: 原始文本

    返回:
        str: 转义后的字面量, 单引号写成两个单引号
    """
    return "'" + str(text).replace("'", "''") + "'"


def _volume_control():
    """
    取系统主音量的控制接口

    返回:
        音量接口对象, 缺少依赖或没有音频设备时返回 None
    """
    try:
        return AudioUtilities.GetSpeakers().EndpointVolume
    except Exception as e:
        print(f"获取音量控制接口失败: {e}")
        return None


def get_volume():
    """
    读取系统主音量

    返回:
        int: 0 到 100 的音量百分比, 失败返回 -1
    """
    volume = _volume_control()
    if volume is None:
        return -1
    try:
        return int(round(volume.GetMasterVolumeLevelScalar() * 100))  # type: ignore
    except Exception as e:
        print(f"读取音量失败: {e}")
        return -1


def set_volume(percent=50):
    """
    设置系统主音量

    参数:
        percent: 音量百分比, 0 到 100, 超出范围按边界处理
    """
    volume = _volume_control()
    if volume is None:
        return
    try:
        value = max(0, min(100, int(percent)))
        volume.SetMasterVolumeLevelScalar(value / 100, None)  # type: ignore

        # 静音状态下调音量是听不见的, 顺手解除静音
        if volume.GetMute():  # type: ignore
            volume.SetMute(0, None)  # type: ignore
    except Exception as e:
        print(f"设置音量失败: {e}")


def get_brightness():
    """
    读取当前屏幕亮度

    返回:
        int: 0 到 100 的亮度, 台式机外接显示器等不支持时返回 -1
    """
    script = (
        "$b = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness -ErrorAction SilentlyContinue;"
        "if ($b) { @($b)[0].CurrentBrightness } else { 'NO' }"
    )
    output = _run_powershell(script)
    return int(output) if output.isdigit() else -1


def set_brightness(percent=50):
    """
    设置屏幕亮度

    参数:
        percent: 亮度百分比, 0 到 100, 超出范围按边界处理
    """
    value = max(0, min(100, int(percent)))
    script = (
        "$m = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue;"
        f"if (-not $m) {{ 'NO' }} else {{ foreach ($i in $m) {{ $i.WmiSetBrightness(1, {value}) }}; 'OK' }}"
    )
    if _run_powershell(script) != "OK":
        print("当前显示器不支持调节亮度, 常见于台式机外接屏")


def restart(timeout=5):
    """
    定时重启电脑

    参数:
        timeout: 重启前的等待秒数, 期间可以用取消关机撤销
    """
    try:
        subprocess.run(f"shutdown /r /t {int(timeout)}", shell=True)
    except Exception as e:
        print(f"重启失败: {e}")


def sleep_system():
    """让电脑进入睡眠, 系统开启了休眠时会进入休眠"""
    try:
        subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
    except Exception as e:
        print(f"进入睡眠失败: {e}")


def _app_id_for(app_name):
    """
    按来源名取应用标识

    参数:
        app_name: 通知来源显示的应用名

    返回:
        str: 应用标识
    """
    if app_name == _NOTIFY_APP_NAME:
        return _NOTIFY_APP_ID
    digest = hashlib.md5(app_name.encode("utf-8")).hexdigest()[:8]
    return _NOTIFY_APP_ID + "." + digest


def notify(title="熊猫编辑器", message="", source="", icon=""):
    """
    弹出系统通知

    参数:
        title: 通知标题
        message: 通知内容
        source: 通知来源显示的应用名, 留空显示熊猫编辑器
        icon: 来源图标的图片路径, 留空不设置图标
    """
    app_name = str(source).strip() or _NOTIFY_APP_NAME
    app_id = _app_id_for(app_name)
    try:
        key_path = "Software\\Classes\\AppUserModelId\\" + app_id
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, app_name)
            icon_path = str(icon).strip()
            if not icon_path:
                try:
                    winreg.DeleteValue(key, "IconUri")
                except OSError:
                    pass
            elif os.path.isfile(icon_path):
                winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, icon_path)
            else:
                print(f"图标文件不存在, 跳过设置: {icon_path}")
    except Exception as e:
        print(f"注册通知标识失败: {e}")
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null;"
        "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
        "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        "$x = $t.GetElementsByTagName('text');"
        f"$x.Item(0).AppendChild($t.CreateTextNode({_ps_text(title)})) | Out-Null;"
        f"$x.Item(1).AppendChild($t.CreateTextNode({_ps_text(message)})) | Out-Null;"
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($t);"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{app_id}').Show($toast);"
        "'OK'"
    )
    if _run_powershell(script) != "OK":
        print("系统通知发送失败, 请检查系统通知权限")


def open_url(url):
    """
    打开网页

    参数:
        url: 网页地址
    """
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"打开网页失败: {url}, 错误: {e}")


def shutdown(timeout):
    """
    定时关机

    参数:
        timeout: 关机倒计时时间, 单位秒
    """
    try:
        subprocess.run(f"shutdown /s /f /t {timeout}", shell=True)
    except Exception as e:
        print(f"定时关机失败: {timeout}, 错误: {e}")


def cancel_shutdown():
    """取消定时关机"""
    try:
        result = subprocess.run("shutdown /a", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print("没有正在等待的关机计划, 无需取消")
            return
        print("已取消定时关机")
    except Exception as e:
        print(f"取消关机失败: {e}")


def toggle_desktop(enable):
    """
    控制桌面显示或隐藏

    参数:
        enable: True 显示桌面, False 隐藏桌面
    """
    try:
        if enable:
            subprocess.run('start explorer.exe', shell=True)
        else:
            subprocess.run('taskkill /f /im explorer.exe', shell=True)
    except Exception as e:
        print(f"操作桌面失败: {enable}, 错误: {e}")


def toggle_task_manager(enable):
    """
    控制任务管理器启用或禁用

    参数:
        enable: True 启用任务管理器, False 禁用任务管理器
    """
    try:
        index = 0 if enable else 1
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, index)
    except Exception as e:
        print(f"控制任务管理器失败: {enable}, 错误: {e}")


def get_process_list():
    """获取当前进程列表并打印"""
    try:
        print(f"{'PID'.ljust(10)} {'名称'.ljust(30)} {'用户名'.ljust(20)}")
        print("=" * 100)
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                pid = str(proc.info['pid']).ljust(10)
                name = str(proc.info['name']).ljust(30)
                username = str(proc.info['username']).ljust(20)
                print(f"{pid} {name} {username}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        print(f"获取进程列表失败: {e}")


def kill_process(name=None):
    """
    杀死指定名称的进程

    参数:
        name: 进程名称, 必须指定
    """
    try:
        if not name:
            print("错误: 请填写要结束的进程名, 如 系统*('杀死进程', 'notepad.exe')")
            return

        killed = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == name:
                    proc.terminate()
                    proc.wait(timeout=3)
                    killed += 1
                    print(f"进程 {proc.info['name']} (PID: {proc.info['pid']}) 已被终止")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        if not killed:
            print(f"未找到进程: {name}")
    except Exception as e:
        print(f"杀死进程失败: {e}")


def get_date_time(timestamp=None):
    """
    获取当前时间字符串

    参数:
        timestamp: 时间戳, 可选, 默认当前时间

    返回:
        str: 格式化的时间字符串, 失败返回空字符串
    """
    try:
        if timestamp is None:
            timestamp = time.localtime()
        elif isinstance(timestamp, (int, float)):
            timestamp = time.localtime(timestamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
    except Exception as e:
        print(f"获取时间字符串失败: {e}")
        return ""


def system_library(operation, *args):
    """
    系统操作统一入口

    参数:
        operation: 操作名称
        args: 操作参数

    返回:
        操作结果, 未知操作或出错时返回 False
    """
    operations = {
        "打开网页": open_url,
        "定时关机": shutdown,
        "取消关机": cancel_shutdown,
        "重启": restart,
        "睡眠": sleep_system,
        "控制桌面": toggle_desktop,
        "任务管理器": toggle_task_manager,
        "获取进程": get_process_list,
        "杀死进程": kill_process,
        "读取音量": get_volume,
        "设置音量": set_volume,
        "读取亮度": get_brightness,
        "设置亮度": set_brightness,
        "系统通知": notify,
        "格式化时间戳": get_date_time,
    }

    try:
        operation_func = operations.get(operation)
        if operation_func:
            return operation_func(*args)
        else:
            print(f"未知的系统操作: {operation}")
            return False
    except Exception as e:
        print(f"执行系统操作 {operation} 时发生错误: {e}")
        return False
'''
