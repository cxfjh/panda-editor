(() => {
  'use strict';

  // 按元数据生成 Blockly 积木定义, 与内置扩展库保持同一种形状
  const definitionOf = (meta) => {
    const slots = Number(meta.slots) || 0;
    const labels = meta.labels || [];
    const args = [];
    const piece = [];

    for (let i = 0; i < slots; i += 1) {
      if (i > 0) {
        piece.push(i % 3 === 0 ? '\n' : '，');
      }
      piece.push((labels[i] ? labels[i] + ' ' : '') + '%' + (i + 1));
      args.push({ type: 'input_value', name: 'A' + (i + 1) });
    }

    const definition = {
      type: meta.type,
      message0: slots > 0 ? meta.label + '（' + piece.join('') + '）' : meta.label,
      colour: Number(meta.colour),
      tooltip: meta.tip,
      inputsInline: true
    };

    if (args.length > 0) {
      definition.args0 = args;
    }

    if (meta.shape === 'statement') {
      definition.previousStatement = null;
      definition.nextStatement = null;
    } else {
      definition.output = null;
    }
    return definition;
  };

  /**
   * 注册插件积木并重建工具箱
   *
   * 定义写进 CN_LIB_META 后可直接复用现有生成器, 无需额外的代码生成规则
   *
   * @param {object} payload 分类与积木元数据
   * @returns {number} 实际注册的积木数量
   */
  const addBlocks = (payload) => {
    if (!payload || !Array.isArray(payload.categories) || payload.categories.length === 0) {
      return 0;
    }

    window.CN_LIB_META = window.CN_LIB_META || {};
    window.CN_LIB_CATEGORIES = window.CN_LIB_CATEGORIES || [];

    let count = 0;
    for (const group of payload.categories) {
      const definitions = [];
      for (const meta of group.metas || []) {
        if (!meta || !meta.type || Blockly.Blocks[meta.type]) {
          continue;
        }
        window.CN_LIB_META[meta.type] = meta;
        definitions.push(definitionOf(meta));
        count += 1;
      }
      if (definitions.length > 0) {
        Blockly.defineBlocksWithJsonArray(definitions);
      }
      // 重新加载时同一分类已经存在, 只补新积木, 不重复插入分类
      const exists = (window.CN_TOOLBOX.contents || []).some((item) => item.name === (group.category || {}).name);
      if (group.category && !exists) {
        window.CN_LIB_CATEGORIES.push(group.category);
        window.CN_TOOLBOX.contents.push(group.category);
      }
    }

    // 工具箱是启动时注入的, 新增分类后要重建才能看到
    const workspace = Blockly.getMainWorkspace();
    if (workspace && window.CN_TOOLBOX) {
      workspace.updateToolbox(window.CN_TOOLBOX);
    }
    return count;
  };

  /**
   * 让页面上的插件积木与最新载荷保持一致
   *
   * 新增的补进来, 已被删除的插件连同分类一起摘掉, 工作区里的残留块只统计不删除
   *
   * @param {object} payload 分类与积木元数据
   * @returns {{added: number, removed: number, orphans: number}} 新增 移除与残留数量
   */
  const syncBlocks = (payload) => {
    const groups = (payload && payload.categories) || [];
    const types = new Set();
    const names = new Set();
    for (const group of groups) {
      if (group.category) {
        names.add(group.category.name);
      }
      for (const meta of group.metas || []) {
        types.add(meta.type);
      }
    }

    window.CN_TOOLBOX = window.CN_TOOLBOX || { kind: 'categoryToolbox', contents: [] };
    window.CN_LIB_META = window.CN_LIB_META || {};
    window.CN_LIB_CATEGORIES = window.CN_LIB_CATEGORIES || [];

    let removed = 0;
    const stale = (window.CN_TOOLBOX.contents || []).filter(
      (item) => typeof item.name === 'string' && item.name.indexOf('扩展·') === 0 && !names.has(item.name)
    );
    for (const item of stale) {
      window.CN_TOOLBOX.contents = window.CN_TOOLBOX.contents.filter((entry) => entry !== item);
      window.CN_LIB_CATEGORIES = window.CN_LIB_CATEGORIES.filter((entry) => entry !== item);
      for (const entry of item.contents || []) {
        if (entry.type && Blockly.Blocks[entry.type]) {
          delete Blockly.Blocks[entry.type];
          delete window.CN_LIB_META[entry.type];
          removed += 1;
        }
      }
    }

    const added = addBlocks(payload);
    const workspace = Blockly.getMainWorkspace();
    if (workspace && window.CN_TOOLBOX) {
      workspace.updateToolbox(window.CN_TOOLBOX);
    }

    let orphans = 0;
    if (workspace) {
      orphans = workspace
        .getAllBlocks(false)
        .filter((block) => block.type.indexOf('cn_op_plugin_') === 0 && !types.has(block.type)).length;
    }
    // 返回 JSON 文本, 跨语言传递对象在不同绑定下的转换结果不一致
    return JSON.stringify({ added, removed, orphans });
  };

  window.CN_PLUGIN_API = { addBlocks, syncBlocks };
})();
