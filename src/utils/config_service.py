import json
import os
import shutil
import sys
import threading
from typing import Any, Optional
from platformdirs import user_config_dir
from src.utils.exceptions import ConfigException, safe_log


def is_compiled() -> bool:
    """
    判断当前是否运行在打包产物里

    Returns:
        True 表示 PyInstaller 冻结或 Nuitka 编译, False 表示直接跑源码
    """
    main_module = sys.modules.get("__main__")
    return getattr(sys, "frozen", False) or hasattr(main_module, "__compiled__")


def _resolve_root_dir() -> str:
    """
    解析程序根目录, 编译模式取可执行文件所在目录

    Returns:
        程序根目录的绝对路径
    """
    if is_compiled():
        return os.path.abspath(os.path.dirname(sys.argv[0]))
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def _resolve_config_dir() -> str:
    """
    解析用户配置目录, 使用平台标准的用户配置位置

    Returns:
        用户配置目录的绝对路径
    """
    return user_config_dir("PandaEditor", appauthor=False, roaming=True)


def _legacy_appdata_dir() -> str:
    """
    旧手写版本的配置目录, 用于迁移

    Returns:
        旧配置目录的绝对路径
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return os.path.join(appdata, "PandaEditor")
    return os.path.join(os.path.expanduser("~"), ".panda-editor")


# 程序根目录
ROOT_DIR: str = _resolve_root_dir()

# 用户配置目录 %APPDATA% 与旧版安装目录配置
CONFIG_DIR: str = _resolve_config_dir()
LEGACY_CONFIG_DIR: str = os.path.join(ROOT_DIR, "src", "config")

# 配置文件名列表
_CONFIG_FILES = ("AppConfig.json", "FileConfig.json", "SessionConfig.json", "PersonalConfig.json")


def _default_python_path() -> str:
    """
    内置解释器的默认路径

    Returns:
        编译模式为可执行文件同级的 python.exe, 脚本模式为 Environment 下的 python.exe
    """
    folder = "" if is_compiled() else "Environment"
    return os.path.join(ROOT_DIR, folder, "python.exe")


def _migrate_legacy_config() -> None:
    """一次性迁移, 旧版安装目录与旧配置路径的配置迁移到新的用户配置目录"""
    if os.path.isdir(CONFIG_DIR):
        return

    # 旧 AppData 目录里的配置一般比安装目录里的新, 优先采用
    sources = [_legacy_appdata_dir(), LEGACY_CONFIG_DIR]
    for source_dir in sources:
        if not os.path.isdir(source_dir):
            continue
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            copied = False
            for file_name in _CONFIG_FILES:
                legacy_file = os.path.join(source_dir, file_name)
                if os.path.isfile(legacy_file):
                    shutil.copy2(legacy_file, os.path.join(CONFIG_DIR, file_name))
                    copied = True
            if copied:
                safe_log(f"已从 {source_dir} 迁移配置到 {CONFIG_DIR}")
                return
        except Exception as e:
            safe_log(f"迁移旧配置失败: {e}")


# 默认应用配置
DEFAULT_APP_CONFIG: dict[str, Any] = {
    "root_dir": ROOT_DIR,
    "python_path": _default_python_path(),
    "icon_path": os.path.join(ROOT_DIR, "src", "static", "logo.ico"),
    "first_run": True,
}

# 默认文件配置
DEFAULT_FILE_CONFIG: dict[str, Any] = {
    "source_code_path": "",
    "code_name": "",
    "file_ext": ".cn",
}

# 默认会话配置
DEFAULT_SESSION_CONFIG: dict[str, Any] = {
    "last_tabs": [],
    "last_active_tab": 0,
}

# 默认个性化配置
DEFAULT_PERSONAL_CONFIG: dict[str, Any] = {
    "fontSize": 16,
    "darkMode": True,
    "highlightSyntax": True,
    "windowTop": False,
    "pipMirror": "taobao",
    "hideWindow": False,
    "adminPrivilege": False,
    "compileIconPath": "",
    "useDefaultCompileIcon": True,
    "singleFileMode": True,
    "addDataPaths": [],
    "independentRun": False,
    "blocklyPanel": True,
}

# 文件名到默认值的映射, 配置文件损坏时按此回退
_DEFAULT_CONFIGS: dict[str, dict[str, Any]] = {
    "AppConfig.json": DEFAULT_APP_CONFIG,
    "FileConfig.json": DEFAULT_FILE_CONFIG,
    "SessionConfig.json": DEFAULT_SESSION_CONFIG,
    "PersonalConfig.json": DEFAULT_PERSONAL_CONFIG,
}


class ConfigService:
    """配置服务单例类"""
    _instance: Optional["ConfigService"] = None
    _lock = threading.Lock()

    def __init__(self):
        """
        初始化实例, 真正的缓存与锁初始化由 __new__ 完成

        Args:
            self: 类实例自身
        """
        self._initialized = None

    def __new__(cls) -> "ConfigService":
        """
        单例模式实现

        Returns:
            ConfigService 单例实例
        """
        if cls._instance is None:
            # 双重检查加锁, 保证多线程下只创建一个实例
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = { }
                    cls._instance._initialized = False
                    cls._instance._write_lock = threading.Lock()
        assert cls._instance is not None
        return cls._instance

    def init_config(self) -> None:
        """
        初始化配置文件

        Raises:
            ConfigException, 配置初始化失败时抛出
        """
        if self._initialized:
            return

        try:
            # 旧版安装目录配置一次性迁移到用户配置目录
            _migrate_legacy_config()

            # 创建配置目录
            os.makedirs(CONFIG_DIR, exist_ok=True)

            # 获取默认配置文件路径
            app_config_path = os.path.join(CONFIG_DIR, "AppConfig.json")
            file_config_path = os.path.join(CONFIG_DIR, "FileConfig.json")
            session_config_path = os.path.join(CONFIG_DIR, "SessionConfig.json")
            personal_config_path = os.path.join(CONFIG_DIR, "PersonalConfig.json")

            # 创建默认配置文件
            if not os.path.exists(app_config_path): self._write_json(app_config_path, DEFAULT_APP_CONFIG)
            if not os.path.exists(file_config_path): self._write_json(file_config_path, DEFAULT_FILE_CONFIG)
            if not os.path.exists(session_config_path): self._write_json(session_config_path, DEFAULT_SESSION_CONFIG)
            if not os.path.exists(personal_config_path): self._write_json(personal_config_path, DEFAULT_PERSONAL_CONFIG)

            # 加载配置到缓存
            self._load_from_file("AppConfig.json")
            self._load_from_file("FileConfig.json")
            self._load_from_file("SessionConfig.json")
            self._load_from_file("PersonalConfig.json")

            # 处理启动传入的文件/文件夹
            launch_path_handled = False
            if len(sys.argv) > 1:
                # 清理拖拽/命令行传入的路径
                launch_path = sys.argv[1].strip().strip('"').strip("'")
                if os.path.isdir(launch_path):
                    # 拖拽的是文件夹直接设置为源码路径
                    self.update_file_config("source_code_path", os.path.normpath(launch_path))
                    self.update_file_config("code_name", "")
                    launch_path_handled = True
                elif os.path.isfile(launch_path):
                    # 拖拽的是文件解析文件路径
                    from src.utils.file_ops import split_file_path
                    split_file_path(launch_path)
                    launch_path_handled = True

            # 自动创建默认 code.cn 文件
            if not launch_path_handled:
                code_name = self.get_file_config("code_name")
                if not code_name:
                    code_dir = os.path.join(ROOT_DIR, "code")
                    code_file = os.path.join(code_dir, "code.cn")
                    os.makedirs(code_dir, exist_ok=True)

                    # 判断文件是否存在有内容就跳过写入
                    if not (os.path.exists(code_file) and os.path.getsize(code_file) > 0):
                        with open(code_file, "w", encoding="utf-8") as f:
                            f.write('输出*（“你好，世界”）')

                    self.update_file_config("code_name", "code")
                    self.update_file_config("source_code_path", code_dir)

            # 标记为已初始化
            self._initialized = True
        except Exception as e:
            safe_log(f"配置初始化失败: {e}")
            raise ConfigException("配置初始化失败", str(e)) from e

    def read_config(self, file_name: str, key: str | None = None) -> Any:
        """
        从缓存读取配置

        Args:
            file_name: 配置文件名
            key: 配置键名, 为 None 时返回整个配置字典

        Returns:
            配置值或配置字典, 若不存在则返回 None
        """
        config = self._cache.get(file_name)
        if config is None:
            self._load_from_file(file_name)
            config = self._cache.get(file_name)
        if config is None: return None
        assert isinstance(config, dict)
        if key is None: return dict(config)
        return config.get(key)

    def update_config(self, file_name: str, key: str, value: Any) -> bool:
        """
        更新配置

        Args:
            file_name: 配置文件名
            key: 要更新的键名
            value: 新值

        Returns:
            更新是否成功

        Raises:
            ConfigException, 配置更新失败时抛出
        """
        config_path = os.path.join(CONFIG_DIR, file_name)

        try:
            with self._write_lock:
                # 确保缓存中存在该配置
                if file_name not in self._cache:
                    self._load_from_file(file_name)
                    if file_name not in self._cache: self._cache[file_name] = { }

                # 更新键值
                self._cache[file_name][key] = value

                # 持久化到文件
                self._write_json(config_path, self._cache[file_name])
            return True
        except ConfigException:
            raise
        except Exception as e:
            safe_log(f"配置更新失败: {e}")
            raise ConfigException("配置更新失败", str(e)) from e

    def _load_from_file(self, file_name: str) -> None:
        """
        从文件加载配置到缓存

        Args:
            file_name: 配置文件名

        Raises:
            ConfigException, 读取失败时抛出, JSON 损坏时自动备份并回退默认值
        """
        config_path = os.path.join(CONFIG_DIR, file_name)
        if not os.path.exists(config_path): return
        try:
            with open(config_path, "r", encoding="utf-8") as f: self._cache[file_name] = json.load(f)
        except json.JSONDecodeError as e:
            self._recover_config(file_name, config_path, e)
        except Exception as e:
            safe_log(f"读取配置失败: {e}")
            raise ConfigException("读取配置失败", str(e)) from e

    def _recover_config(self, file_name: str, config_path: str, error: Exception) -> None:
        """
        JSON 损坏时备份原文件并用默认值重建, 避免整个程序无法启动

        Args:
            file_name: 配置文件名
            config_path: 损坏文件的完整路径
            error: 原始解析异常
        """
        backup_path = f"{config_path}.corrupt"
        try:
            # 同一秒内多次损坏时覆盖上一份备份即可, 保留最新的一份现场
            os.replace(config_path, backup_path)
        except OSError as e:
            safe_log(f"备份配置文件 {file_name} 失败, 将重建默认配置: {e}")
            backup_path = f"备份失败 {e}"

        default_config = _DEFAULT_CONFIGS.get(file_name, { })
        self._cache[file_name] = dict(default_config)
        safe_log(f"配置文件 {file_name} 解析失败, 已备份到 {backup_path}, 原因 {error}")
        try:
            self._write_json(config_path, self._cache[file_name])
        except Exception as e:
            safe_log(f"重建配置文件 {file_name} 失败: {e}")

    @staticmethod
    def _write_json(path: str, data: Any) -> None:
        """
        写入 JSON 配置文件

        Args:
            path: 文件完整路径
            data: 要写入的数据
        """

        # 先写临时文件再原子替换, 中途崩溃也不会留下半截 JSON
        temp_path = f"{path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)

    def get_app_config(self, key: str | None = None) -> Any:
        """
        获取应用配置

        Args:
            key: 配置键名, 为 None 时返回整个配置字典

        Returns:
            配置值或配置字典
        """
        return self.read_config("AppConfig.json", key)

    def get_file_config(self, key: str | None = None) -> Any:
        """
        获取文件配置

        Args:
            key: 配置键名, 为 None 时返回整个配置字典

        Returns:
            配置值或配置字典
        """
        return self.read_config("FileConfig.json", key)

    def get_session_config(self, key: str | None = None) -> Any:
        """
        获取会话配置

        Args:
            key: 配置键名, 为 None 时返回整个配置字典

        Returns:
            配置值或配置字典
        """
        return self.read_config("SessionConfig.json", key)

    def get_personal_config(self, key: str | None = None) -> Any:
        """
        获取个性化配置

        Args:
            key: 配置键名, 为 None 时返回整个配置字典

        Returns:
            配置值或配置字典
        """
        return self.read_config("PersonalConfig.json", key)

    def update_app_config(self, key: str, value: Any) -> bool:
        """
        更新应用配置

        Args:
            key: 配置键名
            value: 新值

        Returns:
            更新是否成功
        """
        return self.update_config("AppConfig.json", key, value)

    def update_file_config(self, key: str, value: Any) -> bool:
        """
        更新文件配置

        Args:
            key: 配置键名
            value: 新值

        Returns:
            更新是否成功
        """
        return self.update_config("FileConfig.json", key, value)

    def update_session_config(self, key: str, value: Any) -> bool:
        """
        更新会话配置

        Args:
            key: 配置键名
            value: 新值

        Returns:
            更新是否成功
        """
        return self.update_config("SessionConfig.json", key, value)

    def update_personal_config(self, key: str, value: Any) -> bool:
        """
        更新个性化配置

        Args:
            key: 配置键名
            value: 新值

        Returns:
            更新是否成功
        """
        return self.update_config("PersonalConfig.json", key, value)


def get_config_service() -> ConfigService:
    """
    获取 ConfigService 单例

    Returns:
        ConfigService 单例实例
    """
    return ConfigService()
