import json
import os
import sys
from tkinter import messagebox


# 程序根目录
ROOT_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

# 配置目录
CONFIG_DIR = os.path.join(ROOT_DIR, "src", "config")

# 启动参数传入的文件路径
USER_FILE_PATH = sys.argv[1] if len(sys.argv) > 1 else None

# 默认文件配置
DEFAULT_FILE_CONFIG = {
    "Root": ROOT_DIR,
    "ConfigDirectory": os.path.join(CONFIG_DIR, "FileConfig.json"),
    "PersonalConfig": os.path.join(CONFIG_DIR, "PersonalConfig.json"),
    "PythonDirectory": os.path.join(ROOT_DIR, "python.exe"),
    "ICON": os.path.join(ROOT_DIR, "src", "static", "logo.ico"),
    "SourceCodePath": "",
    "CodeName": "",
}

# 默认个性化配置
DEFAULT_PERSONAL_CONFIG = {
    "fontSize": 20,
    "darkMode": True,
    "highlightSyntax": True,
    "windowTop": False,
}


# 配置初始化
def init_config() -> None:
    """初始化配置文件，不存在则创建，已存在则不覆盖"""
    try:
        # 确保配置目录存在
        os.makedirs(CONFIG_DIR, exist_ok=True)
        file_config_path = DEFAULT_FILE_CONFIG["ConfigDirectory"]
        personal_config_path = DEFAULT_FILE_CONFIG["PersonalConfig"]

        # 初始化文件配置
        if not os.path.exists(file_config_path):
            with open(file_config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_FILE_CONFIG, f, ensure_ascii=False, indent=4)

        # 初始化个性化配置
        if not os.path.exists(personal_config_path):
            with open(personal_config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_PERSONAL_CONFIG, f, ensure_ascii=False, indent=4)

        # 处理启动传入的文件
        if USER_FILE_PATH:
            from src.utils.file_ops import split_file_path
            split_file_path(USER_FILE_PATH)

        # 自动创建默认 code.cn 文件
        code_name = read_config("FileConfig.json", "CodeName")
        if not code_name:
            code_dir = os.path.join(ROOT_DIR, "code")
            code_file = os.path.join(code_dir, "code.cn")
            os.makedirs(code_dir, exist_ok=True)
            with open(code_file, "w", encoding="utf-8") as f: f.write("@帮助")
            update_config("FileConfig.json", "CodeName", "code")
            update_config("FileConfig.json", "SourceCodePath", code_dir)
    except Exception as e:
        messagebox.showerror("配置初始化失败", f"初始化出错：\n{str(e)}")


# 读取配置
def read_config(file_name: str, key: str | None = None):
    """
    读取配置文件
    :param file_name: 配置文件名（如 FileConfig.json）
    :param key: 读取指定键，为 None 时返回全部配置
    """
    config_path = os.path.join(CONFIG_DIR, file_name)
    if not os.path.exists(config_path): return None
    try:
        with open(config_path, "r", encoding="utf-8") as f: config_data = json.load(f)
        if key is None:  return config_data
        return config_data.get(key)
    except json.JSONDecodeError:
        messagebox.showerror("配置错误", f"JSON 格式损坏：\n{config_path}")
    except Exception as e:
        messagebox.showerror("读取失败", f"读取配置失败：\n{str(e)}")
    return None


# 更新配置
def update_config(file_name: str, key, new_value=None) -> bool:
    """
    更新配置文件
    :param file_name: 配置文件名
    :param key: 要更新的键 / 传入完整字典时为整个配置
    :param new_value: 新值，为 None 时直接覆盖配置
    """
    config_path = os.path.join(CONFIG_DIR, file_name)
    try:
        # 直接覆盖整个配置
        if new_value is None:
            with open(config_path, "w", encoding="utf-8") as f: json.dump(key, f, ensure_ascii=False, indent=4)
            return True

        # 配置文件不存在则退出
        if not os.path.exists(config_path):
            messagebox.showerror("文件不存在", f"配置文件不存在：\n{config_path}")
            return False

        # 读取并更新
        with open(config_path, "r", encoding="utf-8") as f: config_data = json.load(f)
        config_data[key] = new_value

        # 写入更新
        with open(config_path, "w", encoding="utf-8") as f: json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except json.JSONDecodeError:
        messagebox.showerror("格式错误", f"配置文件 JSON 格式错误：\n{config_path}")
    except Exception as e:
        messagebox.showerror("更新失败", f"保存配置失败：\n{str(e)}")
    return False
