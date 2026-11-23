(() => {
    "use strict";
    
    /** 对话框节点, 首次 openDialog 时创建 */
    const nodes = {
        mask: null, // 遮罩层, 同时作为对话框根节点
        title: null,
        message: null,
        input: null,
        ok: null,
        cancel: null
    };
    
    let mode = "prompt"; // 当前对话框类型: prompt/confirm/alert
    let doneCallback = null; // 关闭时回调
    let lastFocus = null; // 打开前的焦点元素, 关闭后归还
    
    /**
     * 首次调用时创建对话框 DOM
     */
    const ensureBuilt = () => {
        if (nodes.mask) {
            return;
        }
        
        const mask = document.createElement("div");
        mask.className = "cn-dialog-mask";
        mask.hidden = true;
        mask.innerHTML = `
      <div class="cn-dialog" role="dialog" aria-modal="true">
        <div class="cn-dialog-title"></div>
        <div class="cn-dialog-message"></div>
        <input class="cn-dialog-input" type="text" spellcheck="false">
        <div class="cn-dialog-buttons">
          <button type="button" class="cn-dialog-button primary" data-role="ok">确定</button>
          <button type="button" class="cn-dialog-button" data-role="cancel">取消</button>
        </div>
      </div>`;
        document.body.appendChild(mask);
        
        nodes.mask = mask;
        nodes.title = mask.querySelector(".cn-dialog-title");
        nodes.message = mask.querySelector(".cn-dialog-message");
        nodes.input = mask.querySelector(".cn-dialog-input");
        nodes.ok = mask.querySelector("[data-role=\"ok\"]");
        nodes.cancel = mask.querySelector("[data-role=\"cancel\"]");
        
        nodes.ok.addEventListener("click", () => {
            closeDialog(resultOf(true));
        });
        nodes.cancel.addEventListener("click", () => {
            closeDialog(resultOf(false));
        });
        // 点击遮罩空白处等同于取消
        mask.addEventListener("mousedown", (event) => {
            if (event.target === mask) {
                closeDialog(resultOf(false));
            }
        });
        mask.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                closeDialog(resultOf(true));
            } else if (event.key === "Escape") {
                event.preventDefault();
                closeDialog(resultOf(false));
            }
        });
    };
    
    /**
     * 根据对话框类型生成回调参数
     *
     * @param {boolean} accepted 是否点了确定
     * @returns {string|boolean|null} prompt 返回文本, confirm 返回布尔, alert 返回 undefined
     */
    const resultOf = (accepted) => {
        if (mode === "prompt") {
            return accepted ? nodes.input.value : null;
        }
        if (mode === "confirm") {
            return accepted;
        }
        return undefined;
    };
    
    /**
     * 关闭对话框并回调结果
     *
     * @param {string|boolean|null} value 结果值
     */
    const closeDialog = (value) => {
        if (!nodes.mask || nodes.mask.hidden) {
            return;
        }
        nodes.mask.hidden = true;
        const callback = doneCallback;
        doneCallback = null;
        if (typeof lastFocus?.focus === "function") {
            lastFocus.focus();
        }
        lastFocus = null;
        if (typeof callback === "function") {
            callback(value);
        }
    };
    
    /**
     * 打开浮层
     *
     * @param {Object} options 配置项
     * @param {string} options.type 类型: prompt/confirm/alert
     * @param {string} options.title 标题
     * @param {string} options.message 提示文本
     * @param {string} options.value 输入框默认值
     * @param {Function} options.done 关闭回调
     */
    const openDialog = (options) => {
        ensureBuilt();
        
        mode = options.type || "prompt";
        lastFocus = document.activeElement;
        doneCallback = options.done || null;
        
        nodes.title.textContent = options.title || "";
        nodes.title.hidden = !options.title;
        
        nodes.message.textContent = options.message || "";
        nodes.message.hidden = !options.message;
        
        nodes.input.hidden = mode !== "prompt";
        nodes.input.value = options.value || "";
        nodes.cancel.hidden = mode === "alert";
        
        nodes.mask.hidden = false;
        
        // 等一帧再聚焦, 否则输入框会被浮动层自身的显示过程抢走焦点
        setTimeout(() => {
            if (mode === "prompt") {
                nodes.input.focus();
                nodes.input.select();
            } else {
                nodes.ok.focus();
            }
        }, 0);
    };
    
    window.CnDialog = {
        /**
         * 替代原生 prompt
         *
         * @param {string} title 标题
         * @param {string} message 提示文本
         * @param {string} defaultValue 默认值
         * @param {Function} done 回调, 取消时为 null
         */
        prompt: (title, message, defaultValue, done) => {
            openDialog({ type: "prompt", title, message, value: defaultValue, done });
        },
        
        /**
         * 替代原生 confirm
         *
         * @param {string} title 标题
         * @param {string} message 提示文本
         * @param {Function} done 回调, 参数为是否确认
         */
        confirm: (title, message, done) => {
            openDialog({ type: "confirm", title, message, done });
        },
        
        /**
         * 替代原生 alert
         *
         * @param {string} title 标题
         * @param {string} message 提示文本
         * @param {Function} done 关闭回调
         */
        alert: (title, message, done) => {
            openDialog({ type: "alert", title, message, done });
        }
    };
    
    /**
     * 接管 Blockly 的对话框, 变量重命名/删除确认走页面内浮层
     */
    const hookBlocklyDialog = () => {
        if (!window.Blockly || !Blockly.dialog) {
            return;
        }
        
        Blockly.dialog.setAlert((message, done) => {
            window.CnDialog.alert("提示", message, () => {
                if (typeof done === "function") {
                    done();
                }
            });
        });
        
        Blockly.dialog.setConfirm((message, done) => {
            window.CnDialog.confirm("确认操作", message, (accepted) => {
                if (typeof done === "function") {
                    done(accepted);
                }
            });
        });
        
        Blockly.dialog.setPrompt((message, defaultValue, done) => {
            // 重命名/新建变量的提示里带「变量」二字, 标题据此区分
            const title = /变量/.test(message || "") ? "变量名称" : "请输入";
            let text = defaultValue || "";
            if (!text) {
                // 重命名提示形如「将所有的“计数”变量重命名为：」, 取出旧名作为默认值省得重敲
                text = /“([^”]+)”/.exec(message || "")?.[1] ?? "";
            }
            window.CnDialog.prompt(title, message, text, (value) => {
                if (typeof done === "function") {
                    done(value);
                }
            });
        });
    };
    
    hookBlocklyDialog();
})();
