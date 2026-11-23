import ast
import importlib.util
import inspect
import json
import os
import shutil
import sys
import zipfile
from src.utils.exceptions import safe_log


# 插件清单与积木清单的固定文件名
MANIFEST_NAME = "plugin.json"
BLOCKS_NAME = "blocks.json"

# 当前程序支持的插件接口版本, 清单里对不上就不加载
API_VERSION = 1

# 没有在清单里指定颜色时用的默认积木色
DEFAULT_COLOUR = 200

# docstring 首行里的形状标记, 用于覆盖按 return 推导出的结果
SHAPE_MARKS = { "[方块]": "statement", "[椭圆]": "output" }

# 不进入积木参数槽的形参类型, 可变参数没法固定成槽位
SKIP_PARAM_KINDS = (
    inspect.Parameter.VAR_POSITIONAL,
    inspect.Parameter.VAR_KEYWORD,
    inspect.Parameter.KEYWORD_ONLY,
)

# 加载结果缓存, 界面就绪后从这里取积木定义
_block_payload: dict = { "categories": [] }
_loaded: list = []

# 已注册进转译表的插件标识, 重新加载前要先撤掉
_registered_ids: list = []


def plugins_root() -> str:
    """
    取插件根目录, 与现有扩展库共用 File 目录

    Returns:
        插件根目录路径, 未配置程序根目录时返回空字符串
    """
    from src.utils.config_service import get_config_service

    root = get_config_service().get_app_config("root_dir") or ""
    if not root:
        return ""
    return os.path.join(root, "File")


def _read_json(path: str) -> dict:
    """
    读取 JSON 文件

    Args:
        path: 文件路径

    Returns:
        解析结果, 读取或解析失败时返回空字典
    """
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else { }
    except (OSError, json.JSONDecodeError) as e:
        safe_log(f"读取插件文件 {path} 失败: {e}")
        return { }


def _read_blocks(path: str) -> list:
    """
    读取积木清单

    Args:
        path: blocks.json 路径

    Returns:
        积木定义列表, 失败时返回空列表
    """
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as e:
        safe_log(f"读取积木清单 {path} 失败: {e}")
        return []
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def _build_dispatch(plugin_id: str, ops: list) -> str:
    """
    生成插件操作的分发函数

    Args:
        plugin_id: 插件标识, 同时作为中文代码里的入口名
        ops: 操作列表, 每项含 op 与 func

    Returns:
        可直接拼接在插件源码后的分发函数文本
    """
    lines = [f"def {plugin_id}_library(操作, *参数):", '    """插件操作入口"""', "    操作表 = {"]
    for item in ops:
        lines.append(f'        "{item["op"]}": {item["func"]},')
    lines.append("    }")
    lines.append("    函数 = 操作表.get(操作)")
    lines.append("    if 函数 is None:")
    lines.append('        print("插件不支持的操作: " + str(操作))')
    lines.append("        return None")
    lines.append("    return 函数(*参数)")
    return "\n".join(lines) + "\n"


def _load_module(entry_path: str, plugin_id: str):
    """
    按路径加载插件模块, 只用于校验与取函数名

    Args:
        entry_path: 插件入口文件路径
        plugin_id: 插件标识, 用作模块名

    Returns:
        已加载的模块, 失败时返回 None
    """
    module_name = f"panda_plugin_{plugin_id}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, entry_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        safe_log(f"插件 {plugin_id} 导入失败: {e}")
        return None


def _normalize_ops(blocks: list, module) -> list:
    """
    整理积木清单里的操作, 校验对应函数是否存在

    Args:
        blocks: blocks.json 里的积木列表
        module: 已加载的插件模块

    Returns:
        合法操作列表, 每项含 op func label params shape tip colour
    """
    result = []
    seen_ops: set = set()
    for item in blocks:
        op = str(item.get("op") or "").strip()
        if not op:
            continue

        # 分发函数按操作名建表, 同名会互相覆盖, 只保留先出现的
        if op in seen_ops:
            safe_log(f"插件操作重名, 跳过后者: {op}")
            continue
        func = str(item.get("func") or op).strip()
        if not hasattr(module, func):
            safe_log(f"插件缺少函数 {func}, 跳过操作 {op}")
            continue
        seen_ops.add(op)
        params = item.get("params") or []
        if not isinstance(params, list):
            params = []
        result.append(
            {
                "op": op,
                "func": func,
                "label": str(item.get("label") or op),
                "params": [str(param) for param in params],
                "shape": "statement" if item.get("shape") == "statement" else "output",
                "tip": str(item.get("tip") or f"{op}: 插件提供的操作"),
                "colour": int(item.get("colour") or 200),
            },
        )
    return result


def _has_value_return(source: str) -> dict:
    """
    统计源码里哪些函数带返回值的 return

    Args:
        source: 插件源码

    Returns:
        函数名到是否有返回值的映射, 解析失败时返回空字典
    """
    mapping = { }
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        safe_log(f"插件源码解析失败, 积木形状按方块处理: {e}")
        return mapping
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            mapping[node.name] = any(isinstance(child, ast.Return) and child.value is not None for child in ast.walk(node))
    return mapping


def _derive_ops(module, source: str, colour: int) -> list:
    """
    从插件源码推导积木定义, 让作者只写函数

    Args:
        module: 已加载的插件模块
        source: 插件源码, 用于判断函数是否有返回值
        colour: 积木颜色

    Returns:
        操作列表, 结构与 blocks.json 解析结果一致
    """
    returns = _has_value_return(source)
    result = []
    for name, func in vars(module).items():
        if name.startswith("_") or not inspect.isfunction(func) or func.__module__ != module.__name__:
            continue
        try:
            params = [
                param.name
                for param in inspect.signature(func).parameters.values()
                if param.kind not in SKIP_PARAM_KINDS
            ]
        except (TypeError, ValueError):
            params = []

        tip = (func.__doc__ or "").strip().split("\n")[0].strip()
        shape = "output" if returns.get(name) else "statement"
        for mark, marked in SHAPE_MARKS.items():
            if mark in tip:
                shape = marked
                tip = tip.replace(mark, "").strip()
                break

        result.append(
            {
                "op": name,
                "func": name,
                "label": name,
                "params": params,
                "shape": shape,
                "tip": tip or f"{name}: 插件提供的操作",
                "colour": colour,
            },
        )
    return result


def _block_meta(plugin_id: str, plugin_name: str, ops: list) -> list:
    """
    生成积木元数据, 结构与内置扩展库保持一致

    Args:
        plugin_id: 插件标识
        plugin_name: 插件显示名
        ops: 已校验的操作列表

    Returns:
        积木元数据列表, 供界面注册积木使用
    """
    metas = []
    for index, item in enumerate(ops):
        metas.append(
            {
                "type": f"cn_op_plugin_{plugin_id}_{index}",
                "label": item["label"],
                "lib": f"扩展·{plugin_name}",
                "kind": "op",
                "entry": f"{plugin_id}$",
                "op": item["op"],
                "decorator": f"${plugin_id}",
                "args": len(item["params"]),
                "slots": len(item["params"]),
                "labels": item["params"],
                "shape": item["shape"],
                "tip": item["tip"],
                "colour": item["colour"],
            },
        )
    return metas


def _register_python(plugin_id: str, source: str, ops: list) -> None:
    """
    把插件注册进转译映射表, 让中文代码能调用到它

    Args:
        plugin_id: 插件标识
        source: 插件源码与分发函数的拼接结果
        ops: 已校验的操作列表
    """
    from src.module import builtin_map, grammar as grammar_module, lib_map

    decorator = f"${plugin_id}"
    entry = f"{plugin_id}$"
    dispatch = f"{plugin_id}_library"

    lib_map.lib[decorator] = source
    builtin_map.builtin[entry] = dispatch
    grammar_module.grammar[decorator] = source
    grammar_module.grammar[entry] = dispatch
    if plugin_id not in _registered_ids:
        _registered_ids.append(plugin_id)


def _unregister_previous() -> None:
    """
    移除上一轮注册的插件键

    插件被删除或改名后, 残留的键还能转译出调用, 运行时会因为函数不存在而报错
    """
    if not _registered_ids:
        return

    from src.module import builtin_map, grammar as grammar_module, lib_map

    for plugin_id in _registered_ids:
        decorator = f"${plugin_id}"
        entry = f"{plugin_id}$"
        lib_map.lib.pop(decorator, None)
        builtin_map.builtin.pop(entry, None)
        grammar_module.grammar.pop(decorator, None)
        grammar_module.grammar.pop(entry, None)
    _registered_ids.clear()


def load_plugin(plugin_dir: str, seen_ids: set | None = None) -> tuple:
    """
    加载单个插件

    Args:
        plugin_dir: 插件目录
        seen_ids: 已加载的插件标识集合, 用于拦截重复 id

    Returns:
        插件信息与积木元数据组成的元组, 失败时信息里的 ok 为 False
    """
    manifest = _read_json(os.path.join(plugin_dir, MANIFEST_NAME))
    plugin_id = str(manifest.get("id") or os.path.basename(plugin_dir)).strip()
    info = {
        "id": plugin_id,
        "name": str(manifest.get("name") or plugin_id),
        "version": str(manifest.get("version") or "0"),
        "path": plugin_dir,
        "ok": False,
        "reason": "",
        "blocks": 0,
    }
    if not plugin_id.isidentifier():
        info["reason"] = "插件标识只能用字母 数字 下划线"
        return info, []

    # id 决定积木类型, 重复会让两套积木撞在一起, 后加载的直接不认
    if seen_ids is not None:
        if plugin_id in seen_ids:
            info["reason"] = "id 与已加载的插件重复"
            return info, []
        seen_ids.add(plugin_id)
    if int(manifest.get("api_version") or 0) != API_VERSION:
        info["reason"] = f"接口版本不匹配, 需要 {API_VERSION}"
        return info, []

    entry_name = str(manifest.get("entry") or "main.py")
    entry_path = os.path.join(plugin_dir, entry_name)
    if not os.path.isfile(entry_path):
        info["reason"] = f"缺少入口文件 {entry_name}"
        return info, []

    module = _load_module(entry_path, plugin_id)
    if module is None:
        info["reason"] = "入口文件导入失败, 详见日志"
        return info, []

    try:
        with open(entry_path, encoding="utf-8") as handle:
            source = handle.read()
    except OSError as e:
        info["reason"] = f"读取入口文件失败: {e}"
        return info, []

    # 有积木清单就照它来, 没有就按函数签名推导, 作者只写函数即可
    declared = manifest.get("blocks", BLOCKS_NAME)
    blocks_path = os.path.join(plugin_dir, str(declared)) if str(declared or "").strip() else ""
    if blocks_path and os.path.isfile(blocks_path):
        ops = _normalize_ops(_read_blocks(blocks_path), module)
    else:
        try:
            colour = int(manifest.get("colour", DEFAULT_COLOUR))
        except (TypeError, ValueError):
            colour = DEFAULT_COLOUR
        ops = _derive_ops(module, source, colour)
    if not ops:
        info["reason"] = "没有可用的操作, 函数不能以下划线开头, 且不能只写可变参数"
        return info, []

    _register_python(plugin_id, source + "\n\n" + _build_dispatch(plugin_id, ops), ops)
    info["ok"] = True
    info["blocks"] = len(ops)
    return info, _block_meta(plugin_id, info["name"], ops)


def load_all() -> list:
    """
    扫描并加载全部插件, 单个插件失败不影响其他插件

    Returns:
        每个插件的加载结果列表
    """
    global _block_payload, _loaded
    _block_payload = { "categories": [] }
    _loaded = []
    _unregister_previous()

    root = plugins_root()
    if not root or not os.path.isdir(root):
        _reset_translate_cache()
        return _loaded

    seen_ids: set = set()
    used_names: set = set()

    for name in sorted(os.listdir(root)):
        plugin_dir = os.path.join(root, name)
        if not os.path.isdir(plugin_dir):
            continue
        if not os.path.isfile(os.path.join(plugin_dir, MANIFEST_NAME)):
            continue
        info, metas = load_plugin(plugin_dir, seen_ids)
        _loaded.append(info)
        if not info["ok"] or not metas:
            continue

        # 显示名重复时补上 id, 否则两套积木都挂在同名分类下, 后一套在面板上看不到
        category_name = f"扩展·{info['name']}"
        if category_name in used_names:
            category_name = f"{category_name} · {info['id']}"
        used_names.add(category_name)
        category = {
            "kind": "category",
            "name": category_name,
            "colour": metas[0]["colour"],
            "contents": [{ "kind": "block", "type": meta["type"] } for meta in metas],
        }
        _block_payload["categories"].append({ "category": category, "metas": metas })

    _reset_translate_cache()
    safe_log(f"插件加载完成, 成功 {sum(1 for item in _loaded if item['ok'])} 个, 共 {len(_loaded)} 个")
    return _loaded


def _reset_translate_cache() -> None:
    """
    丢弃转译缓存, 让带插件调用的代码重新转译一次

    语法表在插件加载时追加了新键, 缓存里存的是没有插件代码的旧结果
    """
    try:
        from src.utils.code_proc.translate import reset_cache

        reset_cache()
    except Exception as e:
        safe_log(f"清理转译缓存失败: {e}")


def block_payload() -> dict:
    """
    取界面注册积木需要的载荷

    Returns:
        分类与积木元数据, 界面据此注册 Blockly 积木并重建工具箱
    """
    return _block_payload


def loaded_plugins() -> list:
    """
    取上次加载结果

    Returns:
        插件信息列表
    """
    return _loaded


def zip_plugin_id(zip_path: str) -> str:
    """
    只读压缩包里的插件标识, 不落盘

    Args:
        zip_path: 插件压缩包路径

    Returns:
        清单里的 id, 读不到时返回空字符串
    """
    try:
        with zipfile.ZipFile(zip_path) as archive:
            name = next(
                (item for item in archive.namelist() if os.path.basename(item) == MANIFEST_NAME), "",
            )
            if not name:
                return ""
            data = json.loads(archive.read(name).decode("utf-8"))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError) as e:
        safe_log(f"读取插件压缩包失败: {e}")
        return ""
    return str(data.get("id") or "").strip() if isinstance(data, dict) else ""


def import_zip(zip_path: str) -> str:
    """
    从压缩包导入插件

    Args:
        zip_path: 插件压缩包路径

    Returns:
        导入的插件标识

    Raises:
        ValueError: 压缩包结构不合法时抛出
    """
    root = plugins_root()
    if not root:
        raise ValueError("未配置程序根目录")

    with zipfile.ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        manifest_name = next((name for name in names if os.path.basename(name) == MANIFEST_NAME), "")
        if not manifest_name:
            raise ValueError("压缩包里没有 plugin.json")

        # 允许整包套一层目录, 以清单所在目录为插件根
        prefix = manifest_name[: -len(MANIFEST_NAME)]
        manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
        plugin_id = str(manifest.get("id") or "").strip()
        if not plugin_id.isidentifier():
            raise ValueError("plugin.json 里的 id 不合法")

        target = os.path.join(root, plugin_id)
        if os.path.isdir(target):
            shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)
        for name in names:
            if not name.startswith(prefix):
                continue
            relative = name[len(prefix):]
            if not relative or ".." in relative:
                continue
            destination = os.path.join(target, relative.replace("/", os.sep))
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with archive.open(name) as source, open(destination, "wb") as handle:
                shutil.copyfileobj(source, handle)

    safe_log(f"插件 {plugin_id} 已导入到 {target}")
    return plugin_id


def remove_plugin(plugin_id: str) -> None:
    """
    把已加载的插件目录移入回收站

    Args:
        plugin_id: 插件标识

    Raises:
        ValueError: 插件不存在时抛出
        OSError: 移入回收站失败时抛出
    """
    from src.utils.recycle_bin import move_to_recycle_bin

    target = next((item["path"] for item in _loaded if item["id"] == plugin_id), "")
    if not target or not os.path.isdir(target):
        raise ValueError(f"插件不存在: {plugin_id}")
    if not move_to_recycle_bin(target):
        raise OSError(f"无法删除插件目录: {target}")
    safe_log(f"插件 {plugin_id} 已移入回收站: {target}")


def export_zip(plugin_id: str, zip_path: str) -> None:
    """
    把插件目录打包成可分享的压缩包

    Args:
        plugin_id: 插件标识
        zip_path: 目标压缩包路径
    """
    root = plugins_root()
    plugin_dir = os.path.join(root or "", plugin_id)
    if not os.path.isdir(plugin_dir):
        raise ValueError(f"插件目录不存在: {plugin_dir}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for base, dirs, files in os.walk(plugin_dir):
            # 字节码缓存跟着插件发给别人没有意义, 换台机器还会失效
            dirs[:] = [name for name in dirs if name != "__pycache__"]
            for name in files:
                if name.endswith((".pyc", ".pyo")):
                    continue
                full = os.path.join(base, name)
                if os.path.abspath(full) == os.path.abspath(zip_path):
                    continue
                relative = os.path.relpath(full, plugin_dir)
                archive.write(full, os.path.join(plugin_id, relative).replace(os.sep, "/"))
    safe_log(f"插件 {plugin_id} 已导出到 {zip_path}")
