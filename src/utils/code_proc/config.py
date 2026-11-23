import os
from src.utils.config_service import get_config_service
from src.utils.exceptions import safe_log


def get_config() -> dict | None:
    """
    从配置文件读取路径信息

    Returns:
        包含路径信息的字典, 若配置不完整则返回 None, 字典键包含 python_dir, source_code_path, exe_path, code_path, icon_path, code_name, root
    """
    try:
        root = get_config_service().get_app_config("root_dir")
        python_dir = get_config_service().get_app_config("python_path")
        source_code_path = get_config_service().get_file_config("source_code_path")
        code_name = get_config_service().get_file_config("code_name")
        icon_path = get_config_service().get_app_config("icon_path")

        # 校验必要配置项是否完整
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
        safe_log(f"配置读取异常: {e}")
        return None


def apply_file_path(config: dict, file_path: str | None) -> dict:
    """
    用显式传入的 .cn 路径覆盖配置里的目录与文件名

    Args:
        config: 配置字典, 原地修改
        file_path: 当前 .cn 文件路径

    Returns:
        修改后的配置字典
    """
    if not file_path:
        return config
    file_dir, file_name = os.path.split(file_path)
    base_name, _ = os.path.splitext(file_name)
    config["source_code_path"] = file_dir
    config["code_name"] = base_name
    config["exe_path"] = os.path.join(file_dir, base_name)
    config["code_path"] = f"{config['exe_path']}.py"
    return config
