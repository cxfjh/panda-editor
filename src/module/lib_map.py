from src.module.lib_sources import automation_library, concurrent_libraries, document_library, interface_library, network_library, random_library, system_library
from src.utils.extend import extend_library


# 内置库映射表
lib = { }

all_library = network_library + system_library + interface_library + automation_library + concurrent_libraries + random_library + document_library

lib.update(
    {
        "@库": all_library,
        "@文件库": document_library,
        "@系统库": system_library,
        "@网络库": network_library,
        "@界面库": interface_library,
        "@自动化库": automation_library,
        "@并发库": concurrent_libraries,
        "@随机库": random_library,
        "@外部依赖": "import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))",
    },
)

lib.update(
    {
        "数学库": "math",
        "随机库": "random",
        "系统库": "os",
        "路径库": "pathlib",
        "时间库": "time",
        "日期库": "datetime",
        "画笔库": "turtle",
    },
)

extend_library(lib)
