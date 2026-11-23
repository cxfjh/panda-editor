(() => {
    "use strict";
    
    // 积木分类色相, 与 Blockly 主题配合使用
    const COLOUR = {
        io: 230, // 输出与输入
        variable: 330, // 变量
        logic: 260, // 条件判断
        loop: 120, // 循环
        data: 20, // 数据与对象
        math: 160, // 运算
        func: 290, // 函数与类
        error: 0, // 异常处理
        module: 45 // 模块与其它
    };
    
    // 异常类型, 显示中文而生成 Python 认得的类名
    const EXC_OPTIONS = [
        ["任意异常", "ALL"],
        ["除零错误", "ZeroDivisionError"],
        ["值错误", "ValueError"],
        ["类型错误", "TypeError"],
        ["索引错误", "IndexError"],
        ["键错误", "KeyError"],
        ["名称错误", "NameError"],
        ["属性错误", "AttributeError"],
        ["文件未找到", "FileNotFoundError"],
        ["导入错误", "ImportError"],
        ["运行错误", "RuntimeError"],
        ["断言错误", "AssertionError"],
        ["溢出错误", "OverflowError"],
        ["权限错误", "PermissionError"]
    ];
    
    // 常用中文模块名 -> 真实模块名, 引入后可直接用 数学.平方根 这类写法
    const MODULE_OPTIONS = [
        ["数学（math）", "math"],
        ["随机（random）", "random"],
        ["系统（os）", "os"],
        ["时间（time）", "time"],
        ["日期（datetime）", "datetime"],
        ["路径（pathlib）", "pathlib"],
        ["JSON（json）", "json"],
        ["正则（re）", "re"],
        ["集合工具（collections）", "collections"],
        ["迭代工具（itertools）", "itertools"],
        ["系统参数（sys）", "sys"]
    ];
    
    // 常用对象方法, 均为 module/method_map 中可安全转译的中文名
    const METHOD_OPTIONS = [
        ["追加", "追加"],
        ["插入", "插入"],
        ["弹出", "弹出"],
        ["清空", "清空"],
        ["反转", "反转"],
        ["排序", "排序"],
        ["计数", "计数"],
        ["扩展", "扩展"],
        ["索引", "索引"],
        ["取键", "取键"],
        ["取值", "取值"],
        ["取项", "取项"],
        ["更新", "更新"],
        ["获取", "获取"],
        ["设默认", "设默认"],
        ["分割", "分割"],
        ["连接", "连接"],
        ["替换", "替换"],
        ["查找", "查找"],
        ["大写", "大写"],
        ["小写", "小写"],
        ["去空格", "去空格"],
        ["开头匹配", "开头匹配"],
        ["结尾匹配", "结尾匹配"],
        ["读取", "读取"],
        ["读取行", "读取行"],
        ["写入", "写入"],
        ["关闭", "关闭"],
        ["添加", "添加"],
        ["丢弃", "丢弃"],
        ["交集", "交集"],
        ["并集", "并集"],
        ["差集", "差集"]
    ];
    
    // 全部积木类型, 顶层出现表达式积木时不再生成代码
    const BLOCKS = [
        // 输出与输入
        {
            type: "cn_print",
            message0: "输出*（%1）",
            args0: [{ type: "input_value", name: "VALUE" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.io,
            tooltip: "向控制台输出内容, 对应 CnLang 的 输出*",
            inputsInline: true
        },
        {
            type: "cn_input",
            message0: "输入*（%1）",
            args0: [{ type: "input_value", name: "PROMPT" }],
            output: null,
            colour: COLOUR.io,
            tooltip: "读取用户输入, 对应 CnLang 的 输入*",
            inputsInline: true
        },
        
        // 变量
        {
            type: "cn_set_var",
            message0: "设 %1 为 %2",
            args0: [
                { type: "field_variable", name: "VAR", variable: "变量" },
                { type: "input_value", name: "VALUE" }
            ],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.variable,
            tooltip: "给变量赋值"
        },
        {
            type: "cn_change_var",
            message0: "让 %1 增加 %2",
            args0: [
                { type: "field_variable", name: "VAR", variable: "变量" },
                { type: "input_value", name: "VALUE" }
            ],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.variable,
            tooltip: "在原值基础上累加, 减少时填负数"
        },
        {
            type: "cn_get_var",
            message0: "变量 %1",
            args0: [{ type: "field_variable", name: "VAR", variable: "变量" }],
            output: null,
            colour: COLOUR.variable,
            tooltip: "读取变量的值"
        },
        {
            type: "cn_none",
            message0: "空",
            output: null,
            colour: COLOUR.variable,
            tooltip: "空值, 对应 CnLang 的 空"
        },
        {
            type: "cn_global",
            message0: "%1 变量 %2",
            args0: [
                {
                    type: "field_dropdown",
                    name: "SCOPE",
                    options: [
                        ["全局", "全局"],
                        ["外层", "外层"]
                    ]
                },
                { type: "field_input", name: "NAMES", text: "变量" }
            ],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.variable,
            tooltip: "在函数内声明使用全局变量或外层变量, 多个名字用逗号分隔"
        },
        
        // 条件判断
        {
            type: "cn_if",
            message0: "如果 %1 那么",
            args0: [{ type: "input_value", name: "IF0" }],
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO0" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.logic,
            tooltip: "条件成立时执行内部积木"
        },
        {
            type: "cn_elif",
            message0: "另如 %1 那么",
            args0: [{ type: "input_value", name: "COND" }],
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.logic,
            tooltip: "紧接在 如果 积木之后, 用于多条件判断"
        },
        {
            type: "cn_else",
            message0: "否则",
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.logic,
            tooltip: "紧接在 如果 或 另如 积木之后"
        },
        {
            type: "cn_if_else",
            message0: "如果 %1 那么",
            args0: [{ type: "input_value", name: "IF0" }],
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO0" }],
            message2: "否则",
            message3: "执行 %1",
            args3: [{ type: "input_statement", name: "ELSE" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.logic,
            tooltip: "条件成立与不成立时分别执行不同的积木"
        },
        {
            type: "cn_bool",
            message0: "%1",
            args0: [
                {
                    type: "field_dropdown",
                    name: "BOOL",
                    options: [
                        ["真", "TRUE"],
                        ["假", "FALSE"]
                    ]
                }
            ],
            output: null,
            colour: COLOUR.logic,
            tooltip: "逻辑真值 真 或 假"
        },
        {
            type: "cn_compare",
            message0: "%1 %2 %3",
            args0: [
                { type: "input_value", name: "A" },
                {
                    type: "field_dropdown",
                    name: "OP",
                    options: [
                        ["=", "EQ"],
                        ["≠", "NEQ"],
                        ["<", "LT"],
                        ["≤", "LTE"],
                        [">", "GT"],
                        ["≥", "GTE"],
                        ["是（同一对象）", "IS"],
                        ["不是（不同对象）", "IS_NOT"]
                    ]
                },
                { type: "input_value", name: "B" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.logic,
            tooltip: "比较两个值的大小、是否相等或是否同一对象; 判断空值请用 是 / 不是"
        },
        {
            type: "cn_logic",
            message0: "%1 %2 %3",
            args0: [
                { type: "input_value", name: "A" },
                {
                    type: "field_dropdown",
                    name: "OP",
                    options: [
                        ["且", "AND"],
                        ["或", "OR"]
                    ]
                },
                { type: "input_value", name: "B" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.logic,
            tooltip: "逻辑与 且 / 逻辑或 或"
        },
        {
            type: "cn_not",
            message0: "非 %1",
            args0: [{ type: "input_value", name: "A" }],
            inputsInline: true,
            output: null,
            colour: COLOUR.logic,
            tooltip: "逻辑取反"
        },
        {
            type: "cn_ternary",
            message0: "如果 %1 那么 %2 否则 %3",
            args0: [
                { type: "input_value", name: "COND" },
                { type: "input_value", name: "THEN" },
                { type: "input_value", name: "ELSE" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.logic,
            tooltip: "条件表达式, 条件成立取前一个值, 不成立取后一个值, 生成 甲 如果 条件 否则 乙"
        },
        {
            type: "cn_in",
            message0: "%1 %2 %3",
            args0: [
                { type: "input_value", name: "A" },
                {
                    type: "field_dropdown",
                    name: "OP",
                    options: [
                        ["在", "IN"],
                        ["不在", "NOT_IN"]
                    ]
                },
                { type: "input_value", name: "B" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.logic,
            tooltip: "判断某个值是否包含在列表、字典或文本中"
        },
        {
            type: "cn_match",
            message0: "匹配 %1",
            args0: [{ type: "input_value", name: "VALUE" }],
            message1: "分支 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.logic,
            tooltip: "按值的形态逐条匹配, 内部放 分支 积木"
        },
        {
            type: "cn_case",
            message0: "分支 %1",
            args0: [{ type: "field_input", name: "PATTERN", text: "_" }],
            message1: "当 %1",
            args1: [{ type: "input_value", name: "GUARD" }],
            message2: "执行 %1",
            args2: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.logic,
            tooltip: "只能放在 匹配 积木内部, 模式可用 1、_ 或容器写法"
        },
        
        // 循环
        {
            type: "cn_while",
            message0: "循环当 %1 成立",
            args0: [{ type: "input_value", name: "COND" }],
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.loop,
            tooltip: "条件一直成立时反复执行内部积木"
        },
        {
            type: "cn_repeat",
            message0: "重复 %1 次",
            args0: [{ type: "input_value", name: "TIMES" }],
            message1: "计数变量 %1",
            args1: [{ type: "field_variable", name: "LOOPVAR", variable: "循环项" }],
            message2: "执行 %1",
            args2: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.loop,
            tooltip: "按指定次数重复执行内部积木"
        },
        {
            type: "cn_for_each",
            message0: "遍历 %1 在 %2 中",
            args0: [
                { type: "field_variable", name: "VAR", variable: "元素" },
                { type: "input_value", name: "ITERABLE" }
            ],
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.loop,
            tooltip: "逐个取出列表或区间中的元素并执行内部积木"
        },
        {
            type: "cn_break",
            message0: "跳出循环",
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.loop,
            tooltip: "立即结束当前循环"
        },
        {
            type: "cn_continue",
            message0: "跳过本次",
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.loop,
            tooltip: "跳过本次循环剩余的积木"
        },
        
        // 数据与对象
        {
            type: "cn_index",
            message0: "%1 的第 %2 项",
            args0: [
                { type: "input_value", name: "OBJ" },
                { type: "input_value", name: "INDEX" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.data,
            tooltip: "按下标或键取值, 生成 容器【下标】"
        },
        {
            type: "cn_slice",
            message0: "%1 的第 %2 到 %3 项",
            args0: [
                { type: "input_value", name: "OBJ" },
                { type: "input_value", name: "START" },
                { type: "input_value", name: "STOP" }
            ],
            message1: "步长 %1",
            args1: [{ type: "input_value", name: "STEP" }],
            inputsInline: true,
            output: null,
            colour: COLOUR.data,
            tooltip: "切片, 生成 容器【开始 : 结束 : 步长】, 空着的端点会被省略"
        },
        {
            type: "cn_set_item",
            message0: "设 %1 的第 %2 项 为 %3",
            args0: [
                { type: "input_value", name: "OBJ" },
                { type: "input_value", name: "INDEX" },
                { type: "input_value", name: "VALUE" }
            ],
            inputsInline: true,
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.data,
            tooltip: "修改容器中的某一项, 生成 容器【下标】 = 值; 字典把 第几项 换成键名"
        },
        {
            type: "cn_attr",
            message0: "%1 . %2",
            args0: [
                { type: "input_value", name: "OBJ" },
                { type: "field_input", name: "ATTR", text: "名称" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.data,
            tooltip: "读取对象的属性, 例如 自身.名称"
        },
        {
            type: "cn_method",
            message0: "%1 . %2 （%3，%4）",
            args0: [
                { type: "input_value", name: "OBJ" },
                { type: "field_dropdown", name: "METHOD", options: METHOD_OPTIONS },
                { type: "input_value", name: "A" },
                { type: "input_value", name: "B" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.data,
            tooltip: "调用对象方法, 空着的参数会被省略"
        },
        {
            type: "cn_list_comp",
            message0: "列表推导 值 %1",
            args0: [{ type: "input_value", name: "EXPR" }],
            message1: "遍历 %1 在 %2 中",
            args1: [
                { type: "field_variable", name: "VAR", variable: "元素" },
                { type: "input_value", name: "ITERABLE" }
            ],
            message2: "当 %1",
            args2: [{ type: "input_value", name: "COND" }],
            inputsInline: false,
            output: null,
            colour: COLOUR.data,
            tooltip: "列表推导式, 生成 【表达式 遍历 变量 在 容器 如果 条件】"
        },
        
        // 运算
        {
            type: "cn_math",
            message0: "%1 %2 %3",
            args0: [
                { type: "input_value", name: "A" },
                {
                    type: "field_dropdown",
                    name: "OP",
                    options: [
                        ["+", "ADD"],
                        ["-", "MINUS"],
                        ["×", "MULTIPLY"],
                        ["÷", "DIVIDE"],
                        ["整除", "FLOORDIV"],
                        ["取余", "MODULO"],
                        ["乘方", "POWER"]
                    ]
                },
                { type: "input_value", name: "B" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.math,
            tooltip: "加减乘除等算术运算"
        },
        {
            type: "cn_neg",
            message0: "取负 %1",
            args0: [{ type: "input_value", name: "VALUE" }],
            inputsInline: true,
            output: null,
            colour: COLOUR.math,
            tooltip: "取相反数, 生成 -值"
        },
        {
            type: "cn_bit",
            message0: "%1 %2 %3",
            args0: [
                { type: "input_value", name: "A" },
                {
                    type: "field_dropdown",
                    name: "OP",
                    options: [
                        ["按位与", "AND"],
                        ["按位或", "OR"],
                        ["按位异或", "XOR"],
                        ["左移", "LSHIFT"],
                        ["右移", "RSHIFT"]
                    ]
                },
                { type: "input_value", name: "B" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.math,
            tooltip: "二进制位运算, 生成 & | ^ << >>, 右移时右侧填位数"
        },
        {
            type: "cn_number",
            message0: "数字 %1",
            args0: [{ type: "field_number", name: "NUM", value: 0 }],
            output: null,
            colour: COLOUR.math,
            tooltip: "数字常量"
        },
        {
            type: "cn_text",
            message0: "文本 %1",
            args0: [{ type: "field_input", name: "TEXT", text: "你好" }],
            output: null,
            colour: COLOUR.math,
            tooltip: "字符串常量"
        },
        {
            type: "cn_lambda",
            message0: "匿名函数 参数 %1 : %2",
            args0: [
                { type: "field_input", name: "PARAMS", text: "x" },
                { type: "input_value", name: "BODY" }
            ],
            inputsInline: true,
            output: null,
            colour: COLOUR.math,
            tooltip: "匿名函数, 生成 匿名 x：表达式"
        },
        {
            type: "cn_await",
            message0: "等待 %1",
            args0: [{ type: "input_value", name: "VALUE" }],
            inputsInline: true,
            output: null,
            colour: COLOUR.math,
            tooltip: "等待异步任务完成, 只能在异步函数内使用"
        },
        
        // 函数与类
        {
            type: "cn_return",
            message0: "返回 %1",
            args0: [{ type: "input_value", name: "VALUE" }],
            previousStatement: null,
            colour: COLOUR.func,
            tooltip: "结束函数并返回结果"
        },
        {
            type: "cn_yield",
            message0: "产出 %1",
            args0: [{ type: "input_value", name: "VALUE" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.func,
            tooltip: "在生成器函数中逐个产出值"
        },
        {
            type: "cn_def_class",
            message0: "定义类 %1 继承 %2",
            args0: [
                { type: "field_input", name: "NAME", text: "新类" },
                { type: "field_input", name: "BASES", text: "" }
            ],
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.func,
            tooltip: "定义类, 继承留空表示不继承, 多个父类用逗号分隔"
        },
        {
            type: "cn_set_attr",
            message0: "设 %1 . %2 为 %3",
            args0: [
                { type: "field_input", name: "OBJ", text: "自身" },
                { type: "field_input", name: "ATTR", text: "属性名" },
                { type: "input_value", name: "VALUE" }
            ],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.func,
            tooltip: "给对象属性赋值, 类中常写作 设 自身.名字 为 名字"
        },
        {
            type: "cn_decorator",
            message0: "应用装饰 @%1",
            args0: [{ type: "field_input", name: "NAME", text: "property" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.func,
            tooltip: "紧接在被装饰的函数定义之前, 可填 property、staticmethod、classmethod 或自定义装饰函数"
        },
        
        // 异常处理
        {
            type: "cn_try",
            message0: "尝试",
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            message2: "捕获 %1",
            args2: [{ type: "field_dropdown", name: "EXC", options: EXC_OPTIONS }],
            message3: "简称 %1",
            args3: [{ type: "field_input", name: "ALIAS", text: "" }],
            message4: "执行 %1",
            args4: [{ type: "input_statement", name: "HANDLE" }],
            message5: "收尾 执行 %1",
            args5: [{ type: "input_statement", name: "FINALLY" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.error,
            tooltip: "捕获异常, 简称留空表示不接收异常对象; 生成的代码使用对应的 Python 异常类名"
        },
        {
            type: "cn_raise",
            message0: "抛出 %1",
            args0: [{ type: "field_dropdown", name: "EXC", options: EXC_OPTIONS.slice(1) }],
            message1: "说明 %1",
            args1: [{ type: "input_value", name: "MSG" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.error,
            tooltip: "主动抛出异常, 说明留空则不带提示文本; 生成的代码使用对应的 Python 异常类名"
        },
        {
            type: "cn_assert",
            message0: "断言 %1",
            args0: [{ type: "input_value", name: "COND" }],
            message1: "说明 %1",
            args1: [{ type: "input_value", name: "MSG" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.error,
            tooltip: "条件不成立时中断程序, 说明留空则使用默认提示"
        },
        
        // 模块与其它
        {
            type: "cn_with",
            message0: "使用 %1 简称 %2",
            args0: [
                { type: "input_value", name: "EXPR" },
                { type: "field_input", name: "ALIAS", text: "文件" }
            ],
            message1: "执行 %1",
            args1: [{ type: "input_statement", name: "DO" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.module,
            tooltip: "自动释放资源的写法, 例如 使用 打开*（\"a.txt\", \"r\"） 简称 文件"
        },
        {
            type: "cn_import",
            message0: "引入 %1 简称 %2",
            args0: [
                { type: "field_dropdown", name: "MODULE", options: MODULE_OPTIONS },
                { type: "field_input", name: "ALIAS", text: "" }
            ],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.module,
            tooltip: "引入整个模块, 简称留空则用模块原名; 生成的代码使用真实模块名"
        },
        {
            type: "cn_from_import",
            message0: "来自 %1 引入 %2",
            args0: [
                { type: "field_dropdown", name: "MODULE", options: MODULE_OPTIONS },
                { type: "field_input", name: "NAMES", text: "圆周率, 平方根" }
            ],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.module,
            tooltip: "引入模块中的指定成员, 多个名字用逗号分隔; 生成的代码使用真实模块名"
        },
        {
            type: "cn_import_custom",
            message0: "引入模块 %1 简称 %2",
            args0: [
                { type: "field_input", name: "MODULE", text: "工具" },
                { type: "field_input", name: "ALIAS", text: "" }
            ],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.module,
            tooltip: "引入自己写的模块文件, 例如同目录下的 工具.cn；简称留空则用模块原名"
        },
        {
            type: "cn_comment",
            message0: "注释 %1",
            args0: [{ type: "field_input", name: "TEXT", text: "说明" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.module,
            tooltip: "生成一行中文注释"
        },
        {
            type: "cn_pass",
            message0: "占位",
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.module,
            tooltip: "什么都不做, 用于占住语句块"
        },
        {
            type: "cn_expr",
            message0: "执行 %1",
            args0: [{ type: "input_value", name: "VALUE" }],
            previousStatement: null,
            nextStatement: null,
            colour: COLOUR.module,
            tooltip: "把有返回值的积木单独执行一遍, 返回值直接丢弃; 标准库的函数积木需要这样落到一行时用它"
        }
    ];
    
    // 注册全部中文积木
    Blockly.defineBlocksWithJsonArray(BLOCKS);
    
    // ------------------------------------------------------------------
    // 槽位可增减的积木: 列表项、字典键值对、函数形参、调用参数
    // 用 ＋/－ 图标按钮现场增减, 槽位数量写进 mutation, 保存后可原样恢复
    // ------------------------------------------------------------------
    
    // 单块积木最多的槽位行数, 防止误点把积木拉得过长
    const MAX_ROWS = 12;
    
    /**
     * 生成内联图标按钮的地址, 不依赖外部图片资源
     *
     * @param {string} glyph 图标内的图形片段
     * @returns {string} data URI
     */
    const iconUri = (glyph) => {
        const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">' +
            '<circle cx="8" cy="8" r="7.2" fill="#8C949F"/>' +
            `${glyph}</svg>`;
        return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
    };
    
    // ＋/－ 按钮图标
    const ICON_ADD = iconUri('<path d="M7.1 4h1.8v3.1H12v1.8H8.9V12H7.1V8.9H4V7.1h3.1z" fill="#FFFFFF"/>');
    const ICON_DROP = iconUri('<path d="M4 7.1h8v1.8H4z" fill="#FFFFFF"/>');
    
    /**
     * 生成一个图标按钮字段, 点击即执行回调
     *
     * @param {string} icon 图标地址
     * @param {string} tip 提示文字
     * @param {Function} onClick 点击回调
     * @returns {Blockly.FieldImage} 图标字段
     */
    const stepButton = (icon, tip, onClick) => {
        const field = new Blockly.FieldImage(icon, 17, 17, tip, onClick);
        field.setTooltip(tip);
        return field;
    };
    
    /**
     * 把 ＋/－ 两个按钮挂到同一行输入上
     *
     * @param {Blockly.Block} block 积木
     * @param {Blockly.Input} input 承载按钮的输入行
     * @param {string} addTip 增加按钮的提示
     * @param {string} dropTip 减少按钮的提示
     */
    const appendStepButtons = (block, input, addTip, dropTip) => {
        input.appendField(stepButton(ICON_ADD, addTip, () => block.growRows_(1)));
        input.appendField(stepButton(ICON_DROP, dropTip, () => block.growRows_(-1)));
    };
    
    /**
     * 收集工作区里定义过的函数积木
     *
     * @returns {Blockly.Block[]} 函数定义积木
     */
    const functionBlocks = () => {
        const workspace = Blockly.getMainWorkspace();
        if (!workspace) {
            return [];
        }
        return workspace
            .getAllBlocks(false)
            .filter((block) => block.type === "cn_def_func" || block.type === "cn_async_def");
    };
    
    /**
     * 读取函数定义积木上的形参名
     *
     * @param {Blockly.Block} defBlock 函数定义积木
     * @returns {string[]} 形参名列表
     */
    const parameterNamesOf = (defBlock) => {
        const names = [];
        for (let index = 1; index <= MAX_ROWS; index += 1) {
            const child = defBlock.getInputTargetBlock(`PARAM${index}`);
            if (!child) {
                continue;
            }
            const name = child.type === "cn_param_def" ? String(child.getFieldValue("NAME") || "").trim() : "";
            names.push(name || `参数${index}`);
        }
        return names;
    };
    
    /**
     * 按函数名取形参名, 供调用积木自动对齐槽位
     *
     * @param {string} name 函数名
     * @returns {string[]} 形参名列表
     */
    const parameterNamesOfFunction = (name) => {
        const target = functionBlocks().find((block) => String(block.getFieldValue("NAME") || "").trim() === name);
        return target ? parameterNamesOf(target) : [];
    };
    
    /**
     * 调用积木的下拉选项, 每次展开菜单时重新收集
     *
     * @returns {Array<[string, string]>} 选项列表
     */
    const functionOptions = () => {
        const names = [];
        for (const block of functionBlocks()) {
            const name = String(block.getFieldValue("NAME") || "").trim();
            if (name && !names.includes(name)) {
                names.push(name);
            }
        }
        return names.length > 0
            ? names.map((name) => [name, name])
            : [["（还没有定义函数）", "未定义函数"]];
    };
    
    /**
     * 形参引用积木的下拉选项, 汇总所有函数里的形参名
     *
     * @returns {Array<[string, string]>} 选项列表
     */
    const parameterOptions = () => {
        const names = [];
        for (const block of functionBlocks()) {
            for (const name of parameterNamesOf(block)) {
                if (!names.includes(name)) {
                    names.push(name);
                }
            }
        }
        return names.length > 0
            ? names.map((name) => [name, name])
            : [["（还没有形参）", "参数"]];
    };
    
    /**
     * 允许保存值暂时不在选项里的下拉字段
     *
     * 加载工作区时调用积木可能先于函数定义读进来, 这时选项还是空的;
     * 原生的下拉会把这个值判为非法并清掉, 这里放宽成原样保留
     */
    class TolerantDropdown extends Blockly.FieldDropdown {
        doClassValidation_(newValue) {
            return newValue == null ? null : String(newValue);
        }
    }
    
    /**
     * 注册一个槽位可增减的积木
     *
     * @param {string} type 积木类型
     * @param {object} spec 结构描述
     *        colour 颜色, tooltip 提示, output 值积木, statement 语句积木, inline 行内排列
     *        defaultRows / minRows / maxRows 行数范围
     *        head(block) 建表头, rows(index, block) 返回该行的端口名与标签
     *        tail(block) 建行尾, clearNames 每次重建前要清掉的额外端口
     */
    const registerGrowable = (type, spec) => {
        const maxRows = spec.maxRows || MAX_ROWS;
        const minRows = spec.minRows || 0;
        
        Blockly.Blocks[type] = {
            init() {
                this.rowCount_ = spec.defaultRows;
                this.setColour(spec.colour);
                this.setTooltip(spec.tooltip);
                if (spec.output) {
                    this.setOutput(true);
                }
                if (spec.statement) {
                    this.setPreviousStatement(true);
                    this.setNextStatement(true);
                }
                if (spec.inline) {
                    this.setInputsInline(true);
                }
                spec.head(this);
                this.rebuildRows_();
            },
            
            /**
             * 按当前行数重建槽位
             *
             * 已经接在行上的子积木会先摘下来, 重建完再接回原位, 保证点 ＋/－ 不会丢内容
             */
            rebuildRows_() {
                const kept = new Map();
                const remember = (name) => {
                    const child = this.getInputTargetBlock(name);
                    if (child && !child.isShadow()) {
                        kept.set(name, child);
                    }
                };
                for (let index = 1; index <= this.rowCount_; index += 1) {
                    for (const [name] of spec.rows(index, this)) {
                        remember(name);
                    }
                }
                for (const name of spec.clearNames || []) {
                    remember(name);
                }
                
                for (let index = maxRows; index >= 1; index -= 1) {
                    for (const [name] of spec.rows(index, this)) {
                        if (this.getInput(name)) {
                            this.removeInput(name);
                        }
                    }
                }
                for (const name of spec.clearNames || []) {
                    if (this.getInput(name)) {
                        this.removeInput(name);
                    }
                }
                for (let index = 1; index <= this.rowCount_; index += 1) {
                    for (const [name, label] of spec.rows(index, this)) {
                        const input = this.appendValueInput(name);
                        if (label) {
                            input.appendField(label);
                        }
                    }
                }
                spec.tail?.(this);
                
                for (const [name, child] of kept) {
                    const input = this.getInput(name);
                    const connection = child.outputConnection || child.previousConnection;
                    if (!input || !connection || typeof child.isDeadOrDying === "function" && child.isDeadOrDying()) {
                        continue;
                    }
                    input.connection.connect(connection);
                }
            },
            
            /**
             * 增加或减少槽位
             *
             * @param {number} delta 变化量, 1 为增加, -1 为减少
             */
            growRows_(delta) {
                const next = this.rowCount_ + delta;
                if (next < minRows || next > maxRows) {
                    return;
                }
                Blockly.Events.setGroup(true);
                this.rowCount_ = next;
                this.rebuildRows_();
                this.render();
                Blockly.Events.setGroup(false);
            },
            
            /**
             * XML 保存: 把行数写进 mutation 节点
             *
             * @returns {Element} mutation 节点
             */
            mutationToDom() {
                const dom = Blockly.utils.xml.createElement("mutation");
                dom.setAttribute("rows", String(this.rowCount_));
                return dom;
            },
            
            /**
             * XML 读取: 按 mutation 里的行数恢复槽位
             *
             * @param {Element} xml mutation 节点
             */
            domToMutation(xml) {
                const rows = Number(xml.getAttribute("rows"));
                this.rowCount_ = Number.isFinite(rows) ? Math.min(Math.max(rows, minRows), maxRows) : spec.defaultRows;
                this.rebuildRows_();
            },
            
            /**
             * JSON 序列化时的附加状态
             *
             * @returns {object} 行数
             */
            saveExtraState() {
                return { rows: this.rowCount_ };
            },
            
            /**
             * JSON 反序列化时恢复行数
             *
             * @param {object} state 附加状态
             */
            loadExtraState(state) {
                const rows = Number(state?.rows);
                this.rowCount_ = Number.isFinite(rows) ? Math.min(Math.max(rows, minRows), maxRows) : spec.defaultRows;
                this.rebuildRows_();
            }
        };
    };
    
    // 列表: 行内排列, 列表项可增减
    registerGrowable("cn_list", {
        colour: COLOUR.data,
        tooltip: "创建列表, 点右侧 ＋ 增加一项, － 减少一项, 空着的项会被忽略",
        output: true,
        inline: true,
        defaultRows: 3,
        head(block) {
            block.appendDummyInput("HEAD").appendField("列表 【");
        },
        rows(index) {
            return [[`ITEM${index}`, index > 1 ? "，" : ""]];
        },
        tail(block) {
            const tail = block.appendDummyInput("TAIL").appendField("】");
            appendStepButtons(block, tail, "增加一项", "减少一项");
        },
        clearNames: ["TAIL"]
    });
    
    // 字典: 每行一对键值, 键值对可增减
    registerGrowable("cn_dict", {
        colour: COLOUR.data,
        tooltip: "创建字典, 点右侧 ＋ 增加一对, － 减少一对, 键空着的那对会被忽略",
        output: true,
        inline: true,
        defaultRows: 2,
        maxRows: 8,
        head(block) {
            block.appendDummyInput("HEAD").appendField("字典 {");
        },
        rows(index) {
            return [
                [`KEY${index}`, index > 1 ? "，" : ""],
                [`VALUE${index}`, "："]
            ];
        },
        tail(block) {
            const tail = block.appendDummyInput("TAIL").appendField("}");
            appendStepButtons(block, tail, "增加一对", "减少一对");
        },
        clearNames: ["TAIL"]
    });
    
    // 通用调用: 按名字调用内置或自定义函数, 参数可增减
    registerGrowable("cn_call", {
        colour: COLOUR.data,
        tooltip: "调用内置或自定义函数, 例如 长度*、转文本*、区间*; 点 ＋ 增加参数",
        output: true,
        inline: true,
        defaultRows: 3,
        head(block) {
            const head = block.appendDummyInput("HEAD").appendField("调用");
            head.appendField(new Blockly.FieldTextInput("长度*"), "NAME");
            head.appendField("（");
        },
        rows(index) {
            return [[`ARG${index}`, index > 1 ? "，" : ""]];
        },
        tail(block) {
            const tail = block.appendDummyInput("TAIL").appendField("）");
            appendStepButtons(block, tail, "增加一个参数", "减少一个参数");
        },
        clearNames: ["TAIL"]
    });
    
    // 自定义函数调用: 下拉选函数, 自动按形参数量铺好参数槽
    registerGrowable("cn_func_call", {
        colour: COLOUR.func,
        tooltip: "调用自己定义的函数, 选好函数后会自动铺出对应数量的参数槽",
        output: true,
        inline: true,
        defaultRows: 2,
        head(block) {
            const head = block.appendDummyInput("HEAD").appendField("调用函数");
            const field = new TolerantDropdown(functionOptions);
            field.setValidator((value) => {
                // 结构变化要等字段自身更新完再做, 否则会打断下拉的收尾逻辑
                setTimeout(() => block.syncFromFunction_(value), 0);
                return value;
            });
            head.appendField(field, "NAME");
            head.appendField("（");
        },
        rows(index, block) {
            const names = parameterNamesOfFunction(String(block.getFieldValue("NAME") || "").trim());
            return [[`ARG${index}`, index > 1 ? "，" : (names[index - 1] || "")]];
        },
        tail(block) {
            const tail = block.appendDummyInput("TAIL").appendField("）");
            appendStepButtons(block, tail, "增加一个参数", "减少一个参数");
        },
        clearNames: ["TAIL"]
    });
    
    // 自定义方法调用: 方法名直接输入, 补上「调用方法」下拉里没有的自己写的方法
    registerGrowable("cn_method_any", {
        colour: COLOUR.data,
        tooltip: "调用对象上的任意方法, 方法名可直接输入, 例如 自身.打招呼（名字）",
        output: true,
        inline: true,
        defaultRows: 2,
        head(block) {
            block.appendValueInput("OBJ");
            const head = block.appendDummyInput("HEAD").appendField(".");
            head.appendField(new Blockly.FieldTextInput("方法"), "NAME");
            head.appendField("（");
        },
        rows(index) {
            return [[`ARG${index}`, index > 1 ? "，" : ""]];
        },
        tail(block) {
            const tail = block.appendDummyInput("TAIL").appendField("）");
            appendStepButtons(block, tail, "增加一个参数", "减少一个参数");
        },
        clearNames: ["TAIL"]
    });
    
    /**
     * 选中函数后对齐参数槽数量
     *
     * @param {string} name 函数名
     */
    Blockly.Blocks["cn_func_call"].syncFromFunction_ = function syncFromFunction_(name) {
        const names = parameterNamesOfFunction(name);
        if (names.length === 0) {
            return;
        }
        Blockly.Events.setGroup(true);
        this.rowCount_ = Math.min(names.length, MAX_ROWS);
        this.rebuildRows_();
        this.render();
        Blockly.Events.setGroup(false);
    };
    
    // 定义函数: 形参用积木填, 可增减, 支持带默认值的布尔/数字/文本等类型
    registerGrowable("cn_def_func", {
        colour: COLOUR.func,
        tooltip: "定义函数, 点 ＋ 加一个形参, 形参积木可以选类型并给默认值",
        statement: true,
        defaultRows: 2,
        head(block) {
            const head = block.appendDummyInput("HEAD").appendField("定义函数");
            head.appendField(new Blockly.FieldTextInput("新函数"), "NAME");
            appendStepButtons(block, head, "增加一个形参", "减少一个形参");
        },
        rows(index) {
            return [[`PARAM${index}`, `形参 ${index}`]];
        },
        tail(block) {
            block.appendStatementInput("DO").appendField("执行");
        },
        clearNames: ["DO"]
    });
    
    // 异步定义函数: 结构与普通函数一致
    registerGrowable("cn_async_def", {
        colour: COLOUR.func,
        tooltip: "定义异步函数, 形参用积木填, 可增减",
        statement: true,
        defaultRows: 2,
        head(block) {
            const head = block.appendDummyInput("HEAD").appendField("异步定义函数");
            head.appendField(new Blockly.FieldTextInput("新异步函数"), "NAME");
            appendStepButtons(block, head, "增加一个形参", "减少一个形参");
        },
        rows(index) {
            return [[`PARAM${index}`, `形参 ${index}`]];
        },
        tail(block) {
            block.appendStatementInput("DO").appendField("执行");
        },
        clearNames: ["DO"]
    });
    
    // 形参定义: 名称 + 类型, 类型决定默认值, 让参数可以直接当成对应类型的值使用
    const PARAM_TYPES = [
        ["普通（必填）", "PLAIN"],
        ["布尔（默认 假）", "BOOL"],
        ["数字（默认 0）", "NUMBER"],
        ["文本（默认 空文本）", "TEXT"],
        ["列表（默认 空列表）", "LIST"],
        ["字典（默认 空字典）", "DICT"],
        ["任意（默认 空）", "NONE"]
    ];
    
    // 各类型对应的代码默认值由 generator.js 的 PARAM_DEFAULTS 统一决定
    Blockly.Blocks["cn_param_def"] = {
        init() {
            this.setColour(COLOUR.func);
            this.setOutput(true);
            this.setInputsInline(true);
            this.setTooltip("函数形参, 类型不是普通的会带上对应默认值; 带默认值的形参请放在最后");
            this.appendDummyInput("HEAD")
                .appendField("参数")
                .appendField(new Blockly.FieldTextInput("a"), "NAME")
                .appendField("类型")
                .appendField(new Blockly.FieldDropdown(PARAM_TYPES), "TYPE");
        }
    };
    
    // 形参引用: 按名字取形参, 下拉里自动列出各函数定义过的形参
    Blockly.Blocks["cn_param"] = {
        init() {
            this.setColour(COLOUR.func);
            this.setOutput(true);
            this.setInputsInline(true);
            this.setTooltip("读取形参的值, 下拉里是各函数定义过的形参名");
            this.appendDummyInput("HEAD")
                .appendField("形参")
                .appendField(new TolerantDropdown(parameterOptions), "NAME");
        }
    };
    
    /**
     * 工作区加载完成后刷新调用积木的参数槽标签
     *
     * 调用积木可能比函数定义先读进来, 那时还拿不到形参名
     */
    const refreshFunctionCalls = () => {
        const workspace = Blockly.getMainWorkspace();
        if (!workspace) {
            return;
        }
        for (const block of workspace.getAllBlocks(false)) {
            if (block.type === "cn_func_call" && typeof block.rebuildRows_ === "function") {
                block.rebuildRows_();
            }
        }
    };
    
    // 供 bridge.js 在加载工作区后调用
    window.CN_BLOCK_API = { refreshFunctionCalls };
    
    // 工具箱, 影子积木为各类输入框提供默认值
    const shadowText = (text) => ({ shadow: { type: "cn_text", fields: { TEXT: text } } });
    const shadowNumber = (num) => ({ shadow: { type: "cn_number", fields: { NUM: num } } });
    const shadowVar = (name) => ({ shadow: { type: "cn_get_var", fields: { VAR: name } } });
    const shadowBool = (value) => ({ shadow: { type: "cn_bool", fields: { BOOL: value || "TRUE" } } });
    
    window.CN_TOOLBOX = {
        kind: "categoryToolbox",
        contents: [
            {
                kind: "category",
                name: "输出与输入",
                colour: String(COLOUR.io),
                contents: [
                    { kind: "block", type: "cn_print", inputs: { VALUE: shadowText("你好，世界！") } },
                    { kind: "block", type: "cn_input", inputs: { PROMPT: shadowText("请输入：") } },
                    { kind: "block", type: "cn_comment" }
                ]
            },
            {
                kind: "category",
                name: "变量",
                colour: String(COLOUR.variable),
                contents: [
                    { kind: "block", type: "cn_set_var", inputs: { VALUE: shadowNumber(0) } },
                    { kind: "block", type: "cn_change_var", inputs: { VALUE: shadowNumber(1) } },
                    { kind: "block", type: "cn_get_var" },
                    { kind: "block", type: "cn_none" },
                    { kind: "block", type: "cn_global" }
                ]
            },
            {
                kind: "category",
                name: "条件判断",
                colour: String(COLOUR.logic),
                contents: [
                    {
                        kind: "block",
                        type: "cn_if",
                        inputs: {
                            IF0: shadowBool("TRUE"),
                            DO0: { shadow: { type: "cn_print", inputs: { VALUE: shadowText("条件成立") } } }
                        }
                    },
                    { kind: "block", type: "cn_elif", inputs: { COND: shadowBool("TRUE") } },
                    { kind: "block", type: "cn_else" },
                    { kind: "block", type: "cn_if_else" },
                    { kind: "block", type: "cn_bool" },
                    { kind: "block", type: "cn_compare", inputs: { A: shadowNumber(0), B: shadowNumber(0) } },
                    {
                        kind: "block",
                        type: "cn_logic",
                        inputs: { A: shadowBool("TRUE"), B: shadowBool("FALSE") }
                    },
                    { kind: "block", type: "cn_not" },
                    {
                        kind: "block",
                        type: "cn_ternary",
                        inputs: {
                            COND: shadowBool("TRUE"),
                            THEN: shadowNumber(1),
                            ELSE: shadowNumber(0)
                        }
                    },
                    { kind: "block", type: "cn_in", inputs: { A: shadowNumber(0), B: shadowVar("列表") } },
                    {
                        kind: "block",
                        type: "cn_match",
                        inputs: { VALUE: shadowVar("变量") }
                    },
                    { kind: "block", type: "cn_case" }
                ]
            },
            {
                kind: "category",
                name: "循环",
                colour: String(COLOUR.loop),
                contents: [
                    { kind: "block", type: "cn_while", inputs: { COND: shadowBool("TRUE") } },
                    { kind: "block", type: "cn_repeat", inputs: { TIMES: shadowNumber(10) } },
                    { kind: "block", type: "cn_for_each", inputs: { ITERABLE: shadowVar("列表") } },
                    { kind: "block", type: "cn_break" },
                    { kind: "block", type: "cn_continue" },
                    {
                        kind: "block",
                        type: "cn_list_comp",
                        inputs: {
                            EXPR: shadowNumber(1),
                            ITERABLE: { shadow: { type: "cn_call", fields: { NAME: "区间*" } } }
                        }
                    }
                ]
            },
            {
                kind: "category",
                name: "数据与对象",
                colour: String(COLOUR.data),
                contents: [
                    {
                        kind: "block",
                        type: "cn_list",
                        inputs: { ITEM1: shadowNumber(1), ITEM2: shadowNumber(2), ITEM3: shadowNumber(3) }
                    },
                    {
                        kind: "block",
                        type: "cn_dict",
                        inputs: {
                            KEY1: shadowText("键1"),
                            VALUE1: shadowNumber(0),
                            KEY2: shadowText("键2"),
                            VALUE2: shadowNumber(0)
                        }
                    },
                    {
                        kind: "block",
                        type: "cn_index",
                        inputs: { OBJ: shadowVar("列表"), INDEX: shadowNumber(0) }
                    },
                    {
                        kind: "block",
                        type: "cn_set_item",
                        inputs: {
                            OBJ: shadowVar("列表"),
                            INDEX: shadowNumber(0),
                            VALUE: shadowNumber(0)
                        }
                    },
                    {
                        kind: "block",
                        type: "cn_slice",
                        inputs: { OBJ: shadowVar("列表"), START: shadowNumber(0), STOP: shadowNumber(3) }
                    },
                    { kind: "block", type: "cn_attr", inputs: { OBJ: shadowVar("自身") } },
                    { kind: "block", type: "cn_method", inputs: { OBJ: shadowVar("列表") } },
                    {
                        kind: "block",
                        type: "cn_method_any",
                        inputs: { OBJ: shadowVar("自身"), ARG1: shadowText("名字") }
                    },
                    { kind: "block", type: "cn_call" }
                ]
            },
            {
                kind: "category",
                name: "运算",
                colour: String(COLOUR.math),
                contents: [
                    { kind: "block", type: "cn_math", inputs: { A: shadowNumber(1), B: shadowNumber(1) } },
                    { kind: "block", type: "cn_neg", inputs: { VALUE: shadowNumber(1) } },
                    { kind: "block", type: "cn_bit", inputs: { A: shadowNumber(1), B: shadowNumber(1) } },
                    { kind: "block", type: "cn_bool" },
                    { kind: "block", type: "cn_none" },
                    { kind: "block", type: "cn_number" },
                    { kind: "block", type: "cn_text" },
                    { kind: "block", type: "cn_lambda", inputs: { BODY: shadowNumber(0) } },
                    { kind: "block", type: "cn_await" }
                ]
            },
            {
                kind: "category",
                name: "函数与类",
                colour: String(COLOUR.func),
                contents: [
                    {
                        kind: "block",
                        type: "cn_def_func",
                        inputs: {
                            PARAM1: { shadow: { type: "cn_param_def", fields: { NAME: "a", TYPE: "PLAIN" } } },
                            PARAM2: { shadow: { type: "cn_param_def", fields: { NAME: "b", TYPE: "BOOL" } } },
                            DO: { shadow: { type: "cn_print", inputs: { VALUE: shadowText("你好") } } }
                        }
                    },
                    {
                        kind: "block",
                        type: "cn_async_def",
                        inputs: {
                            PARAM1: { shadow: { type: "cn_param_def", fields: { NAME: "a", TYPE: "PLAIN" } } },
                            DO: { shadow: { type: "cn_pass" } }
                        }
                    },
                    { kind: "block", type: "cn_func_call" },
                    { kind: "block", type: "cn_param_def" },
                    { kind: "block", type: "cn_param" },
                    { kind: "block", type: "cn_return" },
                    { kind: "block", type: "cn_yield" },
                    { kind: "block", type: "cn_def_class" },
                    { kind: "block", type: "cn_set_attr", inputs: { VALUE: shadowNumber(0) } },
                    { kind: "block", type: "cn_decorator" }
                ]
            },
            {
                kind: "category",
                name: "异常处理",
                colour: String(COLOUR.error),
                contents: [
                    { kind: "block", type: "cn_try" },
                    { kind: "block", type: "cn_raise" },
                    { kind: "block", type: "cn_assert", inputs: { COND: shadowBool("TRUE") } }
                ]
            },
            {
                kind: "category",
                name: "模块与其它",
                colour: String(COLOUR.module),
                contents: [
                    {
                        kind: "block",
                        type: "cn_with",
                        inputs: { EXPR: { shadow: { type: "cn_call", fields: { NAME: "打开*" } } } }
                    },
                    { kind: "block", type: "cn_import" },
                    { kind: "block", type: "cn_from_import" },
                    { kind: "block", type: "cn_import_custom" },
                    { kind: "block", type: "cn_expr" },
                    { kind: "block", type: "cn_pass" }
                ]
            }
        ]
    };
    
    // 追加函数库与内置扩展库分类, 由 lib_blocks.js 生成
    if (window.CN_LIB_CATEGORIES) {
        window.CN_TOOLBOX.contents.push(...window.CN_LIB_CATEGORIES);
    }
})();
