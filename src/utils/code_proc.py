import os
import re
import shutil
import threading
import subprocess
from tkinter import messagebox
from src.utils.config import read_config
from src.module.std_lib import grammar, symbols


# 字符映射（中文引号 → 英文引号）
CHARACTER_MAPPING = { "“": '"', "”": '"' }

# 预编译正则表达式（仅初始化一次，提升性能）
GRAMMAR_PATTERN = re.compile(fr'(?<![\w\u4e00-\u9fff])({"|".join(map(re.escape, grammar.keys()))})(?![\w\u4e00-\u9fff])', )
SYMBOLS_PATTERN = re.compile('|'.join(map(re.escape, symbols.keys())))
CHARACTER_PATTERN = re.compile('|'.join(map(re.escape, CHARACTER_MAPPING.keys())))


# 配置读取
def _get_config() -> dict | None:
    """
    从配置文件读取路径信息，增加空值与合法性校验
    :return: 配置字典 / 异常返回None
    """
    try:
        root = read_config("FileConfig.json", "Root")
        python_dir = read_config("FileConfig.json", "PythonDirectory")
        source_code_path = read_config("FileConfig.json", "SourceCodePath")
        code_name = read_config("FileConfig.json", "CodeName")
        icon_path = read_config("FileConfig.json", "ICON")

        # 基础路径校验
        if not all([python_dir, source_code_path, code_name, root]): return None
        exe_path = os.path.join(source_code_path, code_name)
        code_path = f"{exe_path}.py"

        return {
            "python_dir": python_dir,
            "source_code_path": source_code_path,
            "exe_path": exe_path,
            "code_path": code_path,
            "icon_path": icon_path,
            "code_name": code_name,
            "root": root,
        }
    except Exception as e:
        print(f"配置读取异常: {e}")
        return None


# 代码解析核心
def _protect_parts(code_str: str) -> tuple[str, dict]:
    """
    保护中文引号内内容，避免被替换
    :return: (处理后字符串, 占位符映射表)
    """
    protected_parts = re.findall(r'“([^”]*)”', code_str)
    placeholders = { }
    for idx, part in enumerate(protected_parts):
        placeholder = f"__PROTECTED_{idx}__"
        placeholders[placeholder] = part
        code_str = code_str.replace(f"“{part}”", placeholder)
    return code_str, placeholders


# 还原被保护的内容
def _restore_parts(code_str: str, placeholders: dict) -> str:
    """还原被保护的内容"""
    for placeholder, origin in placeholders.items(): code_str = code_str.replace(placeholder, f"“{origin}”")
    return code_str


# 代码解析主函数
def parse_code(code_str: str) -> bool:
    """
    中文代码 → Python代码 解析替换主函数
    :param code_str: 中文代码字符串
    :return: 解析成功True / 失败False
    """
    try:
        config = _get_config()
        if not config:
            messagebox.showerror("配置错误", "请先正确配置文件路径！")
            return False

        # 解析语法内容
        protected_str, placeholders = _protect_parts(code_str)  # 保护引号内内容
        parsed_str = GRAMMAR_PATTERN.sub(lambda m: grammar[m.group(0)], protected_str)  # 替换语法关键词
        parsed_str = SYMBOLS_PATTERN.sub(lambda m: symbols[m.group(0)], parsed_str)  # 替换符号
        parsed_str = _restore_parts(parsed_str, placeholders)  # 还原保护内容
        parsed_str = CHARACTER_PATTERN.sub(lambda m: CHARACTER_MAPPING[m.group(0)], parsed_str)  # 替换特殊字符

        # 确保目录存在并写入文件
        os.makedirs(os.path.dirname(config["code_path"]), exist_ok=True)
        with open(config["code_path"], "w", encoding="utf-8") as f: f.write(parsed_str)
        return True
    except Exception as e:
        messagebox.showerror("代码解析失败", f"解析异常：\n{str(e)}")
        return False


# 运行代码
def _run_thread() -> None:
    """执行Python代码的线程任务"""
    config = _get_config()
    if not config or not os.path.exists(config["code_path"]):
        messagebox.showerror("错误", "代码文件不存在，请先保存！")
        return

    try:
        # 捕获标准输出/错误
        subprocess.run([config["python_dir"], config["code_path"]], cwd=os.path.dirname(config["code_path"]), )
    except subprocess.CalledProcessError as e:
        messagebox.showerror("运行错误", f"代码执行失败：\n{e.stderr}")
    except Exception as e:
        messagebox.showerror("运行异常", f"运行失败：\n{str(e)}")


# 运行代码入口
def run_code(text_code: str) -> None:
    """运行代码入口"""
    if parse_code(text_code):
        thread = threading.Thread(target=_run_thread, daemon=True)
        thread.start()


# 编译打包
def _compile_thread() -> None:
    """PyInstaller 打包线程任务"""
    config = _get_config()
    if not config:
        messagebox.showerror("配置错误", "缺少必要配置，无法编译！")
        return

    # 图标文件校验
    if not os.path.isfile(config["icon_path"]):
        messagebox.showerror("图标错误", "图标文件不存在或路径无效！")
        return

    try:
        # 构建打包命令
        cmd = [
            config["python_dir"], "-m", "PyInstaller",
            "-F",
            f"--distpath={config['source_code_path']}",
            f"-i{config['icon_path']}",
            config["code_path"],
        ]

        # 无窗口模式
        if config["code_name"].endswith("-w"): cmd.insert(3, "-w")

        # 执行打包
        subprocess.run(cmd)
        os.startfile(config["source_code_path"])
        _clean_build_files(config["root"])  # 清理临时文件
        messagebox.showinfo("编译完成", "代码打包成功！")
    except subprocess.CalledProcessError:
        messagebox.showerror("编译失败", "PyInstaller 执行出错，请检查依赖与代码！")
    except Exception as e:
        messagebox.showerror("编译异常", f"打包失败：\n{str(e)}")


# 编译代码入口
def compile_code(text_code: str) -> None:
    """编译代码入口"""
    if parse_code(text_code):
        thread = threading.Thread(target=_compile_thread, daemon=True)
        thread.start()
        messagebox.showinfo("提示", "正在编译中，请耐心等待……\n请勿重复操作！")


# 清理临时文件
def _clean_build_files(work_dir: str) -> None:
    """
    清理PyInstaller生成的 build/ 和 .spec 文件
    :param work_dir: 工作目录
    """
    try:
        # 清理 build 目录
        build_path = os.path.join(work_dir, "build")
        if os.path.isdir(build_path): shutil.rmtree(build_path)

        # 清理 .spec 文件
        for file in os.listdir(work_dir):
            if file.endswith(".spec"):
                spec_path = os.path.join(work_dir, file)
                if os.path.isfile(spec_path): os.remove(spec_path)
    except Exception as e:
        messagebox.showerror("清理异常", f"清理临时文件失败：\n{str(e)}")
