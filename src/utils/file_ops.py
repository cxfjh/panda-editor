import os
import shutil
from tkinter import filedialog, messagebox
from src.utils.config import update_config, read_config


# 获取当前配置中的 .cn 文件路径
def _get_current_file_path() -> str | None:
    """获取当前配置中的 .cn 文件路径"""
    source_dir = read_config("FileConfig.json", "SourceCodePath")
    code_name = read_config("FileConfig.json", "CodeName")
    if not all([source_dir, code_name]): return None
    return os.path.normpath(os.path.join(source_dir, f"{code_name}.cn"))


# 确保文件所在目录存在
def _ensure_dir(file_path: str) -> None:
    """确保文件所在目录存在"""
    dir_path = os.path.dirname(file_path)
    os.makedirs(dir_path, exist_ok=True)


# 文件路径解析
def split_file_path(file_path: str | None) -> None:
    """解析文件路径，更新目录和文件名配置"""
    if not file_path: return
    file_dir, file_name = os.path.split(file_path)
    base_name, _ = os.path.splitext(file_name)
    update_config("FileConfig.json", "CodeName", base_name)
    update_config("FileConfig.json", "SourceCodePath", os.path.normpath(file_dir))


# 打开文件
def open_file() -> None:
    """打开 .cn 格式代码文件"""
    try:
        file_path = filedialog.askopenfilename(filetypes=[("CN 文件", "*.cn")], title="打开 CN 文件", )
        if file_path: split_file_path(os.path.normpath(file_path))
    except Exception as e:
        messagebox.showerror("打开失败", f"无法打开文件：\n{e}")


# 保存文件
def save_file(content: str) -> None:
    """保存到当前配置的文件"""
    try:
        file_path = _get_current_file_path()
        if not file_path:
            messagebox.showwarning("保存失败", "请先使用【另存为】指定保存路径")
            return
        _ensure_dir(file_path)
        with open(file_path, "w", encoding="utf-8") as f: f.write(content)
    except Exception as e:
        messagebox.showerror("保存失败", f"保存文件出错：\n{e}")


# 另存为
def save_as_file(content: str) -> None:
    """另存为新文件并更新配置"""
    try:
        file_path = filedialog.asksaveasfilename(filetypes=[("CN 文件", "*.cn")], defaultextension=".cn", title="另存为 CN 文件")
        if not file_path: return
        normalized_path = os.path.normpath(file_path)
        _ensure_dir(normalized_path)
        with open(normalized_path, "w", encoding="utf-8") as f: f.write(content)
        split_file_path(normalized_path)
    except Exception as e:
        messagebox.showerror("另存失败", f"无法保存文件：\n{e}")


# 读取当前文件内容
def read_file_content() -> str | None:
    """读取当前配置文件内容"""
    try:
        file_path = _get_current_file_path()
        if not file_path or not os.path.isfile(file_path):
            update_config("FileConfig.json", "SourceCodePath", "")
            update_config("FileConfig.json", "CodeName", "")
            return None
        with open(file_path, "r", encoding="utf-8") as f: return f.read()
    except Exception as e:
        messagebox.showerror("读取失败", f"无法读取文件内容：\n{e}")
        return None


# 导入扩展库文件
def import_file() -> None:
    """导入 .py 扩展文件到 /File 目录"""
    try:
        file_path = filedialog.askopenfilename(filetypes=[("Python 文件", "*.py")], title="导入 PY 扩展文件", )
        if not file_path: return
        src_path = os.path.normpath(file_path)
        if not os.path.isfile(src_path):
            messagebox.showerror("导入失败", "文件不存在")
            return

        # 获取目标目录
        root = read_config("FileConfig.json", "Root")
        target_dir = os.path.join(root, "File")
        _ensure_dir(target_dir)

        # 复制文件
        file_name = os.path.basename(src_path)
        target_path = os.path.join(target_dir, file_name)
        shutil.copyfile(src_path, target_path)
        messagebox.showinfo("导入成功", f"文件已导入：\n{target_path}\n重启生效")
    except Exception as e:
        messagebox.showerror("导入失败", f"无法导入文件：\n{e}")
