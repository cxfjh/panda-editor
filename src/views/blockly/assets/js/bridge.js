(() => {
    "use strict";
    
    // 与 Python 侧 registerObject 注册名保持一致
    const OBJECT_NAME = "blockly_bridge";
    
    let workspace = null;
    let bridge = null;
    let statusTimer = null;
    // 最近一次选中的分类下标, 收起后按原分类重新展开
    let lastCategoryIndex = 0;
    
    // 工作区为空时浮动在画布中央的引导文字
    const emptyHint = document.getElementById("cn-empty-hint");
    
    /**
     * 按积木数量显示或隐藏空工作区提示
     *
     * @param {number} count 当前积木数量
     */
    const syncEmptyHint = (count) => {
        if (emptyHint) {
            emptyHint.hidden = count > 0;
        }
    };
    
    /**
     * 让空工作区提示只在画布范围内居中, 避开左侧分类栏
     */
    const alignEmptyHint = () => {
        const toolbox = document.querySelector(".blocklyToolboxDiv");
        if (emptyHint && toolbox) {
            emptyHint.style.left = `${Math.round(toolbox.getBoundingClientRect().width)}px`;
        }
    };
    
    // 需要在其上方画出模块分隔线的分类名, 顺序与工具箱一致
    const DIVIDER_LABELS = ["内置函数", "内置·文件库"];
    
    /**
     * 给分类栏里的模块首项打上标记, 由样式画出分隔线
     */
    const decorateToolbox = () => {
        const toolbox = document.querySelector(".blocklyToolboxDiv");
        if (!toolbox) {
            return;
        }
        for (const category of toolbox.querySelectorAll(".blocklyToolboxCategory")) {
            const label = category.querySelector(".blocklyTreeLabel");
            const isDivider = DIVIDER_LABELS.includes(label?.textContent.trim());
            category.classList.toggle("cn-toolbox-divider", isDivider);
            const previous = category.previousElementSibling?.querySelector(".blocklyTreeLabel");
            if (!isDivider || !label || !previous) {
                continue;
            }
            // 按上一行与当前行的文字位置取中点, 换字号或缩放后线依然居中
            const box = category.getBoundingClientRect();
            const middle = (previous.getBoundingClientRect().bottom + label.getBoundingClientRect().top) / 2;
            category.style.setProperty("--cn-divider-top", `${Math.round(middle - box.top)}px`);
        }
    };
    
    /**
     * 初始化后标记一次, 并在 Blockly 重建分类栏时补回
     */
    const watchToolbox = () => {
        decorateToolbox();
        const toolbox = document.querySelector(".blocklyToolboxDiv");
        if (!toolbox || typeof MutationObserver === "undefined") {
            return;
        }
        new MutationObserver(decorateToolbox).observe(toolbox, { childList: true, subtree: true });
    };
    
    // 深色与浅色主题, 配色取自编辑器主题
    const DARK_THEME = Blockly.Theme.defineTheme("pandaDark", {
        base: Blockly.Themes.Classic,
        componentStyles: {
            workspaceBackgroundColour: "#1e1f22",
            toolboxBackgroundColour: "#2b2d30",
            toolboxForegroundColour: "#E8E8E8",
            flyoutBackgroundColour: "#252526",
            flyoutForegroundColour: "#A9B7C6",
            flyoutOpacity: 1,
            scrollbarColour: "#565A60",
            scrollbarOpacity: 0.45,
            insertionMarkerColour: "#569CDE",
            insertionMarkerOpacity: 0.4,
            markerColour: "#569CDE",
            cursorColour: "#569CDE"
        },
        fontStyle: { family: "Microsoft YaHei", size: 12 }
    });
    
    const LIGHT_THEME = Blockly.Theme.defineTheme("pandaLight", {
        base: Blockly.Themes.Classic,
        componentStyles: {
            workspaceBackgroundColour: "#FFFFFF",
            toolboxBackgroundColour: "#F0F0F0",
            toolboxForegroundColour: "#000000",
            flyoutBackgroundColour: "#F7F7F7",
            flyoutForegroundColour: "#000000",
            flyoutOpacity: 1,
            scrollbarColour: "#C0C0C0",
            scrollbarOpacity: 0.5,
            insertionMarkerColour: "#1E50B4",
            insertionMarkerOpacity: 0.4,
            markerColour: "#1E50B4",
            cursorColour: "#1E50B4"
        },
        fontStyle: { family: "Microsoft YaHei", size: 12 }
    });
    
    /**
     * 创建 Blockly 工作区
     */
    const createWorkspace = () => {
        if (Blockly.config) {
            Blockly.config.snapRadius = Math.max(Blockly.config.snapRadius || 0, 96);
            Blockly.config.connectingSnapRadius = Math.max(Blockly.config.connectingSnapRadius || 0, 96);
        }
        
        workspace = Blockly.inject("blockly_div", {
            toolbox: window.CN_TOOLBOX,
            renderer: "zelos",
            theme: DARK_THEME,
            media: "blockly/media",
            grid: { spacing: 24, length: 2, colour: "#3A3D43", snap: true },
            zoom: { controls: true, wheel: true, startScale: 0.9, maxScale: 2, minScale: 0.4, scaleSpeed: 1.1 },
            move: { scrollbars: true, drag: true, wheel: true },
            trashcan: true,
            sounds: false
        });
        
        // 积木变化时向 Python 汇报数量, 合并连续事件避免频繁刷新状态栏
        workspace.addChangeListener(() => {
            const count = workspace.getAllBlocks(false).length;
            syncEmptyHint(count);
            if (!bridge) return;
            if (statusTimer) clearTimeout(statusTimer);
            statusTimer = setTimeout(() => {
                statusTimer = null;
                bridge.report_status(count > 0 ? `当前积木数 ${count}` : "工作区为空");
            }, 300);
        });
        
        // 点分类时记住选中项, 固定模式重新展开时按原分类恢复
        const syncFromCategory = (event) => {
            const target = event.target instanceof Element ? event.target.closest(".blocklyToolboxCategory") : null;
            if (!target) {
                return;
            }
            setTimeout(rememberCategory, 50);
        };
        document.addEventListener("pointerdown", syncFromCategory, true);
        document.addEventListener("click", syncFromCategory, true);
        
        // 分类栏宽度会随分类名变化, 跟着调整空状态提示的位置
        alignEmptyHint();
        watchToolbox();
        const toolboxNode = document.querySelector(".blocklyToolboxDiv");
        if (toolboxNode && typeof ResizeObserver !== "undefined") {
            new ResizeObserver(alignEmptyHint).observe(toolboxNode);
        }
        window.addEventListener("resize", alignEmptyHint);
    };
    
    /**
     * 切换工作区主题
     *
     * @param {boolean} dark 是否深色
     */
    const applyTheme = (dark) => {
        document.body.classList.toggle("light-theme", !dark);
        if (workspace) {
            workspace.setTheme(dark ? DARK_THEME : LIGHT_THEME);
            Blockly.svgResize(workspace);
        }
    };
    
    /**
     * 记住当前选中的分类, 收起后按原分类展开
     */
    const rememberCategory = () => {
        const toolbox = workspace ? workspace.getToolbox() : null;
        const selected = toolbox ? toolbox.getSelectedItem() : null;
        if (!toolbox || !selected) {
            return;
        }
        const items = toolbox.getToolboxItems();
        const index = items.findIndex((item) => item.getId() === selected.getId());
        if (index >= 0) {
            lastCategoryIndex = index;
        }
    };
    
    /**
     * 设置积木展示区为固定或默认模式
     *
     * @param {boolean} pinned True 为固定显示, False 为拖出积木后自动收起
     */
    const setPalettePinned = (pinned) => {
        const flyout = workspace ? workspace.getFlyout() : null;
        const toolbox = workspace ? workspace.getToolbox() : null;
        if (!flyout || !toolbox) {
            return;
        }
        // 自动收起时展示区浮在画布上方不占位, 固定时并排显示, 由 Blockly 自己挤占画布
        flyout.setAutoClose(!pinned);
        if (pinned) {
            if (!flyout.isVisible()) {
                // 已选中的分类不会重复展开, 先清掉选中态再按原分类展开
                toolbox.clearSelection();
                toolbox.selectItemByPosition(lastCategoryIndex);
            }
        } else {
            if (flyout.isVisible()) {
                rememberCategory();
                flyout.hide();
            }
            // 收起后要清掉选中态, 否则再点同一个分类不会重新展开
            toolbox.clearSelection();
        }
        Blockly.svgResize(workspace);
    };
    
    /**
     * 导出 Blockly 原生 XML 文本
     *
     * @returns {string} 格式化后的 XML
     */
    const serializeWorkspace = () => {
        return Blockly.Xml.domToPrettyText(Blockly.Xml.workspaceToDom(workspace));
    };
    
    /**
     * 把旧版函数积木的"参数"文本框迁移成形参积木
     *
     * 旧版本用一段文本记录参数, 新版本每个形参都是独立积木
     *
     * @param {string} xml 工作区 XML
     * @returns {string} 迁移后的 XML
     */
    const migrateLegacyParams = (xml) => {
        if (!xml.includes("PARAMS")) {
            return xml;
        }
        const dom = Blockly.utils.xml.textToDom(xml);
        let changed = false;
        for (const block of Array.from(dom.getElementsByTagName("block"))) {
            const type = block.getAttribute("type");
            if (type !== "cn_def_func" && type !== "cn_async_def") {
                continue;
            }
            const field = Array.from(block.children).find(
                (node) => node.tagName === "field" && node.getAttribute("name") === "PARAMS"
            );
            if (!field) {
                continue;
            }
            const names = String(field.textContent || "")
                .split(/[,，]/)
                .map((item) => item.trim())
                .filter(Boolean);
            block.removeChild(field);
            changed = true;
            // 行数写进 mutation, 形参按顺序补成形参积木
            const mutation = Blockly.utils.xml.createElement("mutation");
            mutation.setAttribute("rows", String(names.length));
            block.insertBefore(mutation, block.firstChild);
            names.forEach((name, index) => {
                const value = Blockly.utils.xml.createElement("value");
                value.setAttribute("name", `PARAM${index + 1}`);
                const paramBlock = Blockly.utils.xml.createElement("block");
                paramBlock.setAttribute("type", "cn_param_def");
                const nameField = Blockly.utils.xml.createElement("field");
                nameField.setAttribute("name", "NAME");
                nameField.textContent = name;
                paramBlock.appendChild(nameField);
                value.appendChild(paramBlock);
                block.appendChild(value);
            });
        }
        return changed ? Blockly.utils.xml.domToText(dom) : xml;
    };
    
    /**
     * 取节点的元素子节点, 跳过空白文本
     *
     * @param {Element} node 父节点
     * @returns {Element[]} 元素子节点列表
     */
    const elementChildren = (node) => {
        return Array.from(node.childNodes).filter((child) => child.nodeType === 1);
    };
    
    /**
     * 剔除工作区 XML 里已经不存在于当前版本的积木
     *
     * 直接交给 Blockly 会抛异常, 只加载出半截积木, 所以先把这些节点摘掉;
     * 输入被摘空、自身也没别的语句的积木会跟着删掉, 免得留下空壳
     *
     * @param {Element} dom 工作区 XML 根节点
     * @returns {number} 被剔除的积木数量
     */
    const dropMissingBlocks = (dom) => {
        let missing = 0;
        const emptied = new Set();
        for (const node of Array.from(dom.getElementsByTagName("block"))) {
            const type = node.getAttribute("type");
            if (!type || Blockly.Blocks[type]) {
                continue;
            }
            missing += 1;
            const slot = node.parentNode;
            const owner = slot ? slot.parentNode : null;
            if (slot && slot.nodeName === "value" && owner && owner.nodeName === "block") {
                emptied.add(owner);
            }
            if (slot) {
                slot.removeChild(node);
            }
        }
        for (const owner of emptied) {
            const children = elementChildren(owner);
            const values = children.filter((child) => child.nodeName === "value");
            const hasContent = values.some((value) => elementChildren(value).length > 0);
            const hasStatements = children.some((child) => child.nodeName === "statement" || child.nodeName === "next");
            if (values.length > 0 && !hasContent && !hasStatements && owner.parentNode) {
                owner.parentNode.removeChild(owner);
            }
        }
        return missing;
    };
    
    /**
     * 用 Blockly 原生 XML 文本覆盖当前工作区
     *
     * @param {string} xml 工作区 XML
     */
    const loadWorkspace = (xml) => {
        workspace.clear();
        workspace.clearUndo();
        if (!xml?.trim()) {
            return;
        }
        try {
            // Blockly 11 起 XML 解析移至 Blockly.utils.xml
            const dom = Blockly.utils.xml.textToDom(migrateLegacyParams(xml));
            const missing = dropMissingBlocks(dom);
            Blockly.Xml.domToWorkspace(dom, workspace);
            // 调用积木可能比函数定义先读进来, 加载完成后补一次形参标签
            window.CN_BLOCK_API?.refreshFunctionCalls();
            workspace.clearUndo();
            workspace.scrollCenter();
            if (missing > 0) {
                bridge?.report_notice(`有 ${missing} 个积木来自已移除的功能, 无法恢复, 因此变空的积木已一并移除`);
            }
        } catch (error) {
            bridge?.report_status(`积木文件解析失败：${error.message}`);
        }
    };
    
    /**
     * 生成 CnLang 代码并回传 Python
     */
    const generateCode = () => {
        let code = "";
        try {
            code = window.CnLangGenerator.generate(workspace);
        } catch (error) {
            bridge?.report_status(`生成代码失败：${error.message}`);
            return;
        }
        bridge?.submit_code(code);
    };
    
    /**
     * 包装页面侧的指令处理函数, 单个指令出错不阻断后续通信
     *
     * @param {string} label 指令名称, 用于错误提示
     * @param {Function} handler 实际处理逻辑
     * @returns {Function} 包装后的处理函数
     */
    const guard = (label, handler) => {
        return (payload) => {
            try {
                handler(payload);
            } catch (error) {
                console.error(label, error);
                bridge?.report_status(`${label}失败：${error.message}`);
            }
        };
    };
    
    /**
     * 绑定 Python 侧信号
     */
    const bindBridge = () => {
        bridge.load_workspace_requested.connect(guard("加载积木", (xml) => {
            loadWorkspace(xml);
        }));
        bridge.clear_workspace_requested.connect(guard("清空工作区", () => {
            workspace.clear();
            workspace.clearUndo();
        }));
        bridge.workspace_requested.connect(guard("导出积木", () => {
            bridge.submit_workspace_xml(serializeWorkspace());
        }));
        bridge.theme_changed.connect(guard("切换主题", (dark) => {
            applyTheme(Boolean(dark));
        }));
        bridge.generate_requested.connect(guard("生成代码", () => {
            generateCode();
        }));
        bridge.palette_pinned_changed.connect(guard("设置积木展示区", (pinned) => {
            setPalettePinned(Boolean(pinned));
        }));
        
        // 通知 Python 页面已就绪, 之后方可下发指令
        bridge.notify_ready();
    };
    
    /**
     * 建立 QWebChannel 连接
     */
    const initChannel = () => {
        if (typeof QWebChannel === "undefined" || typeof qt === "undefined" || !qt.webChannelTransport) {
            // 脱离编辑器单独打开页面时退化为纯前端模式, 仅控制台提示
            console.warn("未检测到 QWebChannel, 积木编辑器将以独立模式运行");
            return;
        }
        new QWebChannel(qt.webChannelTransport, (channel) => {
            bridge = channel.objects[OBJECT_NAME];
            if (!bridge) {
                console.warn(`未注册 ${OBJECT_NAME} 通信对象`);
                return;
            }
            bindBridge();
        });
    };
    
    createWorkspace();
    initChannel();
})();
