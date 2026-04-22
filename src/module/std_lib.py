import src.module.keywords as key_words  # 导入关键字词
import src.module.builtins as builtins  # 导入内置库
import src.module.builtin_funcs as builtin_funcs  # 导入内置库方法
import src.module.punctuations as punctuations  # 导入标点符号


grammar = { **builtin_funcs.builtin_funcs, **key_words.key_words, **builtins.builtins }  # 合并语法
symbols = { **punctuations.punctuations }  # 合并符号
