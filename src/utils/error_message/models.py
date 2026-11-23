from dataclasses import dataclass


@dataclass
class CodeError:
    """一次运行期崩溃的结构化信息"""
    type_name: str
    message: str
    line_no: int
    func_name: str

@dataclass
class ErrorReport:
    """终端里要显示的中文说明与需要标红的位置"""
    lines: list[str]
    mark: str
    hint_index: int
