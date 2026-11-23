from src.module.builtin_map import builtin
from src.module.keyword_map import keyword
from src.module.lib_map import lib
from src.module.method_map import method
from src.module.punctuation_map import punctuation
from src.module.stdlib_map import stdlib


## 完整语法映射表
grammar = { **stdlib, **lib, **method, **builtin, **keyword }

# 符号映射表
symbols = { **punctuation }
