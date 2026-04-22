import os
import ast
from tkinter import messagebox
from src.utils.config import read_config


# 获取目录路径
def _get_file_dir() -> str | None:
    """获取 /File 目录路径"""
    root_path = read_config("FileConfig.json", "Root")
    if not root_path: return None
    file_dir = os.path.join(root_path, "File")
    if not os.path.isdir(file_dir):
        messagebox.showwarning("目录不存在", f"扩展库目录不存在：\n{file_dir}")
        return None
    return file_dir


# 遍历目录下所有 .py 文件
def _iter_py_files(file_dir: str):
    """遍历目录下所有 .py 文件，生成 (文件名, 文件路径) 迭代器"""
    for filename in os.listdir(file_dir):
        if not filename.endswith(".py"): continue
        file_path = os.path.join(file_dir, filename)
        if os.path.isfile(file_path): yield filename, file_path


# 扩展库加载
def extend_library(directory: dict) -> None:
    """遍历 /File 目录，以文件名为键、内容为值存入字典"""
    file_dir = _get_file_dir()
    if not file_dir:
        return

    for filename, file_path in _iter_py_files(file_dir):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lib_name = os.path.splitext(filename)[0]
                directory[lib_name] = f.read()
        except Exception as e:
            messagebox.showerror("加载失败", f"文件 {filename} 加载失败：\n{e}")


# 提取函数名
def extract_fun(directory: dict) -> None:
    """AST 解析所有 .py 文件，提取所有函数名存入字典"""
    file_dir = _get_file_dir()
    if not file_dir: return
    for filename, file_path in _iter_py_files(file_dir):
        try:
            with open(file_path, "r", encoding="utf-8") as f: code = f.read()
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    directory[func_name] = func_name
        except Exception as e:
            messagebox.showerror("解析失败", f"文件 {filename} 解析出错：\n{e}")
