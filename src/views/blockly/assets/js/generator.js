(() => {
    "use strict";
    
    // 缩进单位, 与编辑器默认的 4 空格保持一致
    const INDENT_UNIT = "    ";
    
    // 二元运算积木, 作为子表达式时需要补括号保留原有优先级
    const BINARY_BLOCKS = ["cn_math", "cn_compare", "cn_logic", "cn_in", "cn_bit", "cn_ternary"];
    
    // 由 lib_blocks.js 生成的积木类型前缀: cn_lib_ 为标准库与内置函数, cn_op_ 为内置扩展库
    const LIB_PREFIXES = ["cn_lib_", "cn_op_"];
    
    // 比较运算与算术运算的关键字映射
    const COMPARE_OPS = {
        EQ: "==",
        NEQ: "!=",
        LT: "<",
        LTE: "<=",
        GT: ">",
        GTE: ">=",
        IS: "是"
    };
    
    // 位运算符号, CnLang 没有对应的中文关键字, 直接输出半角符号
    const BIT_OPS = {
        AND: "&",
        OR: "|",
        XOR: "^",
        LSHIFT: "<<",
        RSHIFT: ">>"
    };
    
    const MATH_OPS = {
        ADD: "+",
        MINUS: "-",
        MULTIPLY: "*",
        DIVIDE: "/",
        FLOORDIV: "//",
        MODULO: "%",
        POWER: "**"
    };
    
    const LOGIC_OPS = {
        AND: "且",
        OR: "或"
    };
    
    /**
     * 判断积木是否来自 lib_blocks.js
     *
     * @param {string} type 积木类型
     * @returns {boolean} 是则返回 true
     */
    const isLibBlock = (type) => LIB_PREFIXES.some((prefix) => type.startsWith(prefix));
    
    /**
     * 生成指定层级的缩进
     *
     * @param {number} level 层级
     * @returns {string} 缩进文本
     */
    const indentOf = (level) => INDENT_UNIT.repeat(level);
    
    /**
     * 生成字符串字面量, 优先使用双引号
     *
     * @param {string} text 原始文本
     * @returns {string} CnLang 字符串字面量
     */
    const quote = (text) => {
        const content = String(text ?? "");
        if (!content.includes("\"")) {
            return `"${content}"`;
        }
        if (!content.includes("'")) {
            return `'${content}'`;
        }
        return `"${content.replace(/"/g, "\\\"")}"`;
    };
    
    /**
     * 生成单引号字符串字面量
     *
     * 内置扩展库的操作名要作为第一个实参传入, 统一用单引号与 CnLang 文档一致
     *
     * @param {string} text 原始文本
     * @returns {string} 单引号字面量
     */
    const singleQuote = (text) => {
        return `'${String(text ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'")}'`;
    };
    
    /**
     * 读取数字字段并去掉无意义的小数位
     *
     * @param {number} value 字段值
     * @returns {string} 数字文本
     */
    const formatNumber = (value) => {
        const num = Number(value);
        if (!Number.isFinite(num)) {
            return "0";
        }
        return String(num);
    };
    
    /**
     * 读取文本字段并去掉首尾空白
     *
     * @param {Blockly.Block} block 积木
     * @param {string} name 字段名
     * @returns {string} 字段文本
     */
    const fieldText = (block, name) => {
        const value = block.getFieldValue(name);
        return value == null ? "" : String(value).trim();
    };
    
    /**
     * 读取变量字段的名字
     *
     * 变量字段的 getValue 返回内部 ID, 显示文本才是代码里要用的变量名
     *
     * @param {Blockly.Block} block 积木
     * @param {string} name 字段名
     * @returns {string} 变量名
     */
    const variableName = (block, name) => {
        const field = block.getField(name);
        if (!field) {
            return "变量";
        }
        if (typeof field.getVariable === "function") {
            const variable = field.getVariable();
            if (variable?.name) {
                return variable.name;
            }
        }
        if (typeof field.getText === "function") {
            const text = field.getText();
            if (text) {
                return String(text);
            }
        }
        const value = field.getValue();
        return value ? String(value) : "变量";
    };
    
    /**
     * 取输入端口上挂着的值积木
     *
     * @param {Blockly.Block} block 父积木
     * @param {string} name 输入端口名
     * @returns {Blockly.Block|null} 值积木
     */
    const inputBlock = (block, name) => block.getInputTargetBlock(name) || null;
    
    /**
     * 生成子表达式文本
     *
     * @param {Blockly.Block} block 父积木
     * @param {string} name 输入端口名
     * @returns {string} 表达式文本
     */
    const childExpression = (block, name) => {
        const child = inputBlock(block, name);
        return child ? expressionOf(child) : "空";
    };
    
    /**
     * 生成参与二元运算的子表达式, 二元运算补括号以保留原有优先级
     *
     * @param {Blockly.Block} block 父积木
     * @param {string} name 输入端口名
     * @returns {string} 表达式文本
     */
    const atomExpression = (block, name) => {
        const child = inputBlock(block, name);
        if (!child) {
            return "空";
        }
        const text = expressionOf(child);
        return BINARY_BLOCKS.includes(child.type) ? `（${text}）` : text;
    };
    
    /**
     * 收集若干个输入端口上的表达式, 空端口直接跳过
     *
     * @param {Blockly.Block} block 父积木
     * @param {string[]} names 输入端口名列表
     * @returns {string[]} 表达式文本列表
     */
    const argumentList = (block, names) => {
        return names
            .map((name) => inputBlock(block, name))
            .filter(Boolean)
            .map((child) => expressionOf(child));
    };
    
    /**
     * 生成函数或方法调用的参数列表
     *
     * @param {Blockly.Block} block 父积木
     * @param {string[]} names 输入端口名列表
     * @returns {string} 括号内的参数文本
     */
    const callArguments = (block, names) => argumentList(block, names).join("，");
    
    /**
     * 取出可变槽位积木上的端口名, 按编号从小到大排序
     *
     * @param {Blockly.Block} block 积木
     * @param {string} prefix 端口名前缀, 例如 ITEM
     * @returns {string[]} 端口名列表
     */
    const slotNames = (block, prefix) => {
        return block.inputList
            .map((input) => input.name)
            .filter((name) => typeof name === "string" && name.startsWith(prefix) && /^\d+$/.test(name.slice(prefix.length)))
            .sort((left, right) => Number(left.slice(prefix.length)) - Number(right.slice(prefix.length)));
    };
    
    /**
     * 取出可变槽位上挂着的值积木
     *
     * @param {Blockly.Block} block 积木
     * @param {string} prefix 端口名前缀
     * @returns {Blockly.Block[]} 值积木列表
     */
    const slotChildren = (block, prefix) => {
        return slotNames(block, prefix)
            .map((name) => inputBlock(block, name))
            .filter(Boolean);
    };
    
    // 形参类型对应的默认值, 普通类型不带默认值
    const PARAM_DEFAULTS = {
        PLAIN: null,
        BOOL: "假",
        NUMBER: "0",
        TEXT: "\"\"",
        LIST: "【】",
        DICT: "{}",
        NONE: "空"
    };
    
    /**
     * 收集函数形参文本
     *
     * Python 要求带默认值的形参排在最后, 顺序违规时给前面的必填形参补默认值, 保证代码能跑
     *
     * @param {Blockly.Block} block 函数定义积木
     * @returns {string} 形参列表文本
     */
    const parameterList = (block) => {
        const texts = slotChildren(block, "PARAM")
            .map((child) => expressionOf(child).trim())
            .filter(Boolean);
        const result = [];
        let hasOptional = false;
        for (const text of texts) {
            const optional = text.includes("=");
            if (optional) {
                hasOptional = true;
            }
            result.push(!optional && hasOptional ? `${text} = 空` : text);
        }
        return result.join("，");
    };
    
    // 本次生成累积的模块依赖, 键是真实模块名, 值是中文库名, 例如 math -> 数学库
    // 键用于去重, 值用于生成 "引入 数学库"; 每次 generate 前清空
    let imports = {};
    
    // 本次生成累积的内置扩展库指令, 例如 @文件库, 每次 generate 前清空
    let libraries = {};
    
    /**
     * 取积木的调用名
     *
     * 优先用中文名, 转译层会按关键字表换成真实成员名;
     * 没有中文名时退回目标名, 保证老数据也能生成
     *
     * @param {object} meta 积木元数据
     * @returns {string} 调用名, 调用类可能带模块前缀
     */
    const libNameOf = (meta) => meta.cn || meta.target;
    
    /**
     * 生成标准库或内置函数积木的表达式
     *
     * 参数槽按顺序取值, 遇到空槽即停止, 避免位置参数错位
     *
     * @param {Blockly.Block} block 积木
     * @returns {string} 表达式文本
     */
    const libExpression = (block) => {
        const meta = window.CN_LIB_META?.[block.type] ?? null;
        if (!meta) {
            return "空";
        }
        
        const slots = Number(meta.slots) || 0;
        const values = [];
        for (let index = 1; index <= slots; index += 1) {
            const child = inputBlock(block, `A${index}`);
            if (!child) {
                break;
            }
            values.push(expressionOf(child));
        }
        
        // 常量与直接调用都要补 import, 记下中文库名, 生成 "引入 数学库"
        if (meta.module && (meta.kind === "call" || meta.kind === "attr")) {
            imports[meta.module] = meta.lib || meta.module;
        }
        
        // 指令积木不产出值, 由 statementOf 直接写成一行指令
        if (meta.kind === "statement") {
            return "空";
        }
        
        // 内置扩展库: 补 @库 指令, 生成 入口（'操作名'，参数…）
        if (meta.kind === "op") {
            libraries[meta.decorator] = true;
            return `${meta.entry}（${[singleQuote(meta.op), ...values].join("，")}）`;
        }
        
        if (meta.kind === "attr") {
            return libNameOf(meta);
        }
        
        // 接收者可能需要按库包一层, 例如把路径文本包成 路径库.路径对象
        // wrap 是中文调用名, import 用真实模块名, 两者不能混用
        const receiverOf = (value) => {
            if (!meta.wrap) {
                return value;
            }
            if (meta.module) {
                imports[meta.module] = meta.lib || meta.module;
            }
            return `${meta.wrap}（${value}）`;
        };
        
        if (meta.kind === "attr_method") {
            return `${receiverOf(values[0] || "对象")}.${libNameOf(meta)}`;
        }
        
        const args = [...values];
        if (meta.kind === "method") {
            const receiver = receiverOf(args.shift() || "对象");
            if (meta.extra) {
                args.push(meta.extra);
            }
            return `${receiver}.${libNameOf(meta)}（${args.join("，")}）`;
        }
        
        if (meta.extra) {
            args.push(meta.extra);
        }
        return `${libNameOf(meta)}（${args.join("，")}）`;
    };
    
    /**
     * 生成值积木的表达式文本
     *
     * @param {Blockly.Block} block 值积木
     * @returns {string} 表达式文本
     */
    const expressionOf = (block) => {
        // 标准库、内置函数与内置扩展库积木
        if (isLibBlock(block.type)) {
            return libExpression(block);
        }
        
        switch (block.type) {
            case "cn_text":
                return quote(block.getFieldValue("TEXT"));
            case "cn_number":
                return formatNumber(block.getFieldValue("NUM"));
            case "cn_bool":
                return block.getFieldValue("BOOL") === "TRUE" ? "真" : "假";
            case "cn_none":
                return "空";
            case "cn_get_var":
                return variableName(block, "VAR");
            case "cn_input":
                return `输入*（${childExpression(block, "PROMPT")}）`;
            case "cn_compare": {
                const operator = block.getFieldValue("OP");
                const symbol = COMPARE_OPS[operator === "IS_NOT" ? "IS" : operator] || "==";
                const inner = `${atomExpression(block, "A")} ${symbol} ` +
                    `${atomExpression(block, "B")}`;
                // 不是 没有对应的中文关键字, 用 非 包一层得到 not (a is b)
                return operator === "IS_NOT" ? `非 （${inner}）` : inner;
            }
            case "cn_math":
                return `${atomExpression(block, "A")} ${MATH_OPS[block.getFieldValue("OP")] || "+"} ` +
                    `${atomExpression(block, "B")}`;
            case "cn_neg":
                return `-${atomExpression(block, "VALUE")}`;
            case "cn_bit":
                return `${atomExpression(block, "A")} ${BIT_OPS[block.getFieldValue("OP")] || "&"} ` +
                    `${atomExpression(block, "B")}`;
            case "cn_ternary":
                return `${childExpression(block, "THEN")} 如果 ${childExpression(block, "COND")} ` +
                    `否则 ${childExpression(block, "ELSE")}`;
            case "cn_logic":
                return `${atomExpression(block, "A")} ${LOGIC_OPS[block.getFieldValue("OP")] || "且"} ` +
                    `${atomExpression(block, "B")}`;
            case "cn_not":
                return `非 ${atomExpression(block, "A")}`;
            case "cn_in": {
                const inner = `${atomExpression(block, "A")} 在 ${atomExpression(block, "B")}`;
                return block.getFieldValue("OP") === "NOT_IN" ? `非 （${inner}）` : inner;
            }
            
            // 数据与对象
            case "cn_list":
                return `【${slotChildren(block, "ITEM").map((child) => expressionOf(child)).join("，")}】`;
            case "cn_dict": {
                const pairs = [];
                for (const name of slotNames(block, "KEY")) {
                    const key = inputBlock(block, name);
                    if (key) {
                        pairs.push(`${expressionOf(key)}：${childExpression(block, `VALUE${name.slice(3)}`)}`);
                    }
                }
                // 花括号在 CnLang 中不参与全角替换, 直接用半角才能得到合法字典
                return `{${pairs.join("，")}}`;
            }
            case "cn_index":
                return `${atomExpression(block, "OBJ")}【${atomExpression(block, "INDEX")}】`;
            case "cn_slice": {
                const start = inputBlock(block, "START");
                const stop = inputBlock(block, "STOP");
                const step = inputBlock(block, "STEP");
                const head = atomExpression(block, "OBJ");
                const body = `${start ? expressionOf(start) : ""} : ${stop ? expressionOf(stop) : ""}`;
                return `${head}【${body}${step ? ` : ${expressionOf(step)}` : ""}】`;
            }
            case "cn_attr":
                return `${atomExpression(block, "OBJ")}.${fieldText(block, "ATTR") || "属性"}`;
            case "cn_method":
                return `${atomExpression(block, "OBJ")}.${fieldText(block, "METHOD")}` +
                    `（${callArguments(block, ["A", "B"])}）`;
            case "cn_method_any":
                return `${atomExpression(block, "OBJ")}.${fieldText(block, "NAME") || "方法"}` +
                    `（${callArguments(block, slotNames(block, "ARG"))}）`;
            case "cn_call":
                return `${fieldText(block, "NAME") || "函数"}（${callArguments(block, slotNames(block, "ARG"))}）`;
            case "cn_func_call":
                return `${fieldText(block, "NAME") || "函数"}（${callArguments(block, slotNames(block, "ARG"))}）`;
            case "cn_param_def": {
                const name = fieldText(block, "NAME") || "参数";
                const fallback = PARAM_DEFAULTS[block.getFieldValue("TYPE")] ?? null;
                return fallback == null ? name : `${name} = ${fallback}`;
            }
            case "cn_param":
                return fieldText(block, "NAME") || "参数";
            case "cn_list_comp": {
                const guard = inputBlock(block, "COND");
                const item = childExpression(block, "EXPR");
                const iterator = childExpression(block, "ITERABLE");
                const name = variableName(block, "VAR");
                return `【${item} 遍历 ${name} 在 ${iterator}${guard ? ` 如果 ${expressionOf(guard)}` : ""}】`;
            }
            
            // 运算与函数式
            case "cn_lambda":
                return `匿名 ${fieldText(block, "PARAMS") || "x"}：${childExpression(block, "BODY")}`;
            case "cn_await":
                return `等待 ${atomExpression(block, "VALUE")}`;
            
            default:
                // 未知的值积木输出占位, 保证整体代码仍可运行
                return "空";
        }
    };
    
    /**
     * 生成语句积木内部执行的代码行, 空语句块补 占位
     *
     * @param {Blockly.Block} block 语句积木
     * @param {string} name 语句输入端口名
     * @param {number} level 缩进层级
     * @returns {string[]} 代码行列表
     */
    const bodyLines = (block, name, level) => {
        const first = inputBlock(block, name);
        const lines = first ? statementLines(first, level) : [];
        return lines.length > 0 ? lines : [`${indentOf(level)}占位`];
    };
    
    /**
     * 生成单个语句积木的代码行
     *
     * @param {Blockly.Block} block 语句积木
     * @param {number} level 缩进层级
     * @returns {string[]} 代码行列表
     */
    const statementOf = (block, level) => {
        const indent = indentOf(level);
        
        // 库积木: 指令项写一行指令, 没有返回值的操作按表达式单独占一行
        if (isLibBlock(block.type)) {
            const meta = window.CN_LIB_META?.[block.type] ?? null;
            if (meta?.kind === "statement") {
                return [indent + meta.directive];
            }
            return [indent + libExpression(block)];
        }
        
        switch (block.type) {
            case "cn_print":
                return [`${indent}输出*（${childExpression(block, "VALUE")}）`];
            
            case "cn_set_var":
                return [`${indent}${variableName(block, "VAR")} = ${childExpression(block, "VALUE")}`];
            
            case "cn_change_var": {
                const name = variableName(block, "VAR");
                return [`${indent}${name} = ${name} + ${childExpression(block, "VALUE")}`];
            }
            
            case "cn_global":
                return [`${indent}${block.getFieldValue("SCOPE")} ${fieldText(block, "NAMES") || "变量"}`];
            
            // 条件判断
            case "cn_if":
                return [`${indent}如果 ${childExpression(block, "IF0")}：`, ...bodyLines(block, "DO0", level + 1)];
            
            case "cn_elif":
                return [`${indent}另如 ${childExpression(block, "COND")}：`, ...bodyLines(block, "DO", level + 1)];
            
            case "cn_else":
                return [`${indent}否则：`, ...bodyLines(block, "DO", level + 1)];
            
            case "cn_if_else":
                return [
                    `${indent}如果 ${childExpression(block, "IF0")}：`,
                    ...bodyLines(block, "DO0", level + 1),
                    `${indent}否则：`,
                    ...bodyLines(block, "ELSE", level + 1)
                ];
            
            case "cn_match":
                return [`${indent}匹配 ${childExpression(block, "VALUE")}：`, ...bodyLines(block, "DO", level + 1)];
            
            case "cn_case": {
                const guard = inputBlock(block, "GUARD");
                const pattern = fieldText(block, "PATTERN") || "_";
                const head = guard
                    ? `${indent}分支 ${pattern} 如果 ${expressionOf(guard)}`
                    : `${indent}分支 ${pattern}`;
                return [`${head}：`, ...bodyLines(block, "DO", level + 1)];
            }
            
            // 循环
            case "cn_while":
                return [`${indent}循环当 ${childExpression(block, "COND")}：`, ...bodyLines(block, "DO", level + 1)];
            
            case "cn_repeat": {
                const loopVar = variableName(block, "LOOPVAR");
                const times = childExpression(block, "TIMES");
                return [`${indent}遍历 ${loopVar} 在 区间*（${times}）：`, ...bodyLines(block, "DO", level + 1)];
            }
            
            case "cn_for_each": {
                const item = variableName(block, "VAR");
                const iterable = childExpression(block, "ITERABLE");
                return [`${indent}遍历 ${item} 在 ${iterable}：`, ...bodyLines(block, "DO", level + 1)];
            }
            
            case "cn_break":
                return [`${indent}跳出`];
            
            case "cn_continue":
                return [`${indent}跳过`];
            
            // 函数与类
            case "cn_return": {
                const hasValue = Boolean(inputBlock(block, "VALUE"));
                return [`${indent}${hasValue ? `返回 ${childExpression(block, "VALUE")}` : "返回"}`];
            }
            
            case "cn_yield": {
                const hasValue = Boolean(inputBlock(block, "VALUE"));
                return [`${indent}${hasValue ? `产出 ${childExpression(block, "VALUE")}` : "产出"}`];
            }
            
            case "cn_def_func": {
                const name = fieldText(block, "NAME") || "新函数";
                return [`${indent}定义 ${name}（${parameterList(block)}）：`, ...bodyLines(block, "DO", level + 1)];
            }
            
            case "cn_async_def": {
                const name = fieldText(block, "NAME") || "新异步函数";
                return [`${indent}异步 定义 ${name}（${parameterList(block)}）：`, ...bodyLines(block, "DO", level + 1)];
            }
            
            case "cn_def_class": {
                const name = fieldText(block, "NAME") || "新类";
                const bases = fieldText(block, "BASES");
                const head = `${indent}类 ${name}${bases ? `（${bases}）` : ""}`;
                return [`${head}：`, ...bodyLines(block, "DO", level + 1)];
            }
            
            case "cn_set_item":
                return [`${indent}${atomExpression(block, "OBJ")}【${atomExpression(block, "INDEX")}】 = ${childExpression(block, "VALUE")}`];
            
            case "cn_set_attr": {
                const target = fieldText(block, "OBJ") || "自身";
                const attr = fieldText(block, "ATTR") || "属性";
                return [`${indent}${target}.${attr} = ${childExpression(block, "VALUE")}`];
            }
            
            case "cn_decorator":
                return [`${indent}@${fieldText(block, "NAME") || "property"}`];
            
            // 异常处理
            case "cn_try": {
                const exc = block.getFieldValue("EXC");
                const alias = fieldText(block, "ALIAS");
                let catchHead = `${indent}捕获`;
                if (exc && exc !== "ALL") {
                    catchHead += ` ${exc}`;
                }
                if (alias) {
                    catchHead += ` 简称 ${alias}`;
                }
                const lines = [
                    `${indent}尝试：`,
                    ...bodyLines(block, "DO", level + 1),
                    `${catchHead}：`,
                    ...bodyLines(block, "HANDLE", level + 1)
                ];
                if (inputBlock(block, "FINALLY")) {
                    lines.push(`${indent}收尾：`, ...bodyLines(block, "FINALLY", level + 1));
                }
                return lines;
            }
            
            case "cn_raise": {
                const message = inputBlock(block, "MSG");
                return [`${indent}抛出 ${block.getFieldValue("EXC")}${message ? `（${expressionOf(message)}）` : ""}`];
            }
            
            case "cn_assert": {
                const reason = inputBlock(block, "MSG");
                const cond = childExpression(block, "COND");
                return [`${indent}断言 ${cond}${reason ? `， ${expressionOf(reason)}` : ""}`];
            }
            
            // 模块与其它
            case "cn_with": {
                const alias = fieldText(block, "ALIAS");
                const head = `${indent}使用 ${childExpression(block, "EXPR")}${alias ? ` 简称 ${alias}` : ""}`;
                return [`${head}：`, ...bodyLines(block, "DO", level + 1)];
            }
            
            case "cn_import": {
                const alias = fieldText(block, "ALIAS");
                const module = block.getFieldValue("MODULE");
                return [`${indent}引入 ${module}${alias ? ` 简称 ${alias}` : ""}`];
            }
            
            case "cn_from_import": {
                const module = block.getFieldValue("MODULE");
                const names = fieldText(block, "NAMES") || "圆周率";
                return [`${indent}来自 ${module} 引入 ${names}`];
            }
            
            case "cn_import_custom": {
                const module = fieldText(block, "MODULE") || "工具";
                const alias = fieldText(block, "ALIAS");
                return [`${indent}引入 ${module}${alias ? ` 简称 ${alias}` : ""}`];
            }
            
            case "cn_comment":
                return [`${indent}# ${fieldText(block, "TEXT")}`];
            
            case "cn_pass":
                return [`${indent}占位`];
            
            // 把有返回值的积木单独跑一遍, 返回值丢弃
            case "cn_expr":
                return [`${indent}${childExpression(block, "VALUE")}`];
            
            default:
                return [`${indent}# 暂不支持的积木: ${block.type}`];
        }
    };
    
    /**
     * 生成一串首尾相连的语句积木代码行
     *
     * @param {Blockly.Block} block 起始语句积木
     * @param {number} level 缩进层级
     * @returns {string[]} 代码行列表
     */
    const statementLines = (block, level) => {
        const lines = [];
        let current = block;
        while (current) {
            lines.push(...statementOf(current, level));
            current = current.getNextBlock();
        }
        return lines;
    };
    
    /**
     * 由工作区生成完整的 CnLang 代码
     *
     * @param {Blockly.Workspace} workspace Blockly 工作区
     * @returns {string} CnLang 代码, 工作区为空时返回空字符串
     */
    const generate = (workspace) => {
        imports = {};
        libraries = {};
        
        // 只处理语句积木, 游离的值积木不参与代码生成
        const blocks = workspace.getTopBlocks(true).filter((block) => {
            if (block.outputConnection) {
                return false;
            }
            const enabled = typeof block.isEnabled === "function" ? block.isEnabled() : true;
            return enabled;
        });
        
        if (blocks.length === 0) {
            return "";
        }
        
        const lines = [];
        blocks.forEach((block, index) => {
            if (index > 0) {
                lines.push(""); // 顶层积木之间留一个空行
            }
            lines.push(...statementLines(block, 0));
        });
        
        const body = lines.join("\n");
        let header = [];
        
        // 内置扩展库的 @库 指令必须写在文件最前面, 库源码会在此处展开
        for (const directive of Object.keys(libraries).sort()) {
            header.push(directive);
        }
        if (header.length > 0) {
            header.push("");
        }
        
        // 把标准库调用需要的引入语句补到文件开头, 已手写的不重复
        // 手写的可能是 "引入 math", 也可能是 "引入 数学库", 两种都要认
        const importLines = Object.entries(imports)
            .sort((left, right) => left[0].localeCompare(right[0]))
            .filter(([module, cn]) => [cn, module].every(
                (name) => !body.includes(`引入 ${name}\n`) && !body.includes(`引入 ${name} `),
            ))
            .map(([, cn]) => `引入 ${cn}`);
        if (importLines.length > 0) {
            header = [...header, ...importLines, ""];
        }
        return `${header.join("\n")}${body}\n`;
    };
    
    window.CnLangGenerator = {
        generate
    };
})();
