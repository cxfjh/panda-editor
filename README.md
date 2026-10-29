#  熊猫编辑器（PandaEditor）

> 一个专为 CnLang 编程语言打造的中文集成开发环境 (IDE)

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.11-blue.svg)
![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## 项目简介

熊猫编辑器是一款面向 CnLang 编程语言的轻量级 IDE，采用全中文界面设计，提供代码编辑、语法高亮、智能补全、代码编译、内嵌终端等一站式开发体验。

## 快速开始

### 环境要求

| 项目     | 要求            |
|----------|-----------------|
| Python   | 3.12 及以上版本 |
| 操作系统 | Windows         |

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/cxfjh/panda-editor.git
cd panda-editor

# 安装依赖二选一
pip install -r requirements.txt
uv sync

# 安装运行时依赖
cd Environment
python.exe -m pip install -r requirements.txt

# 启动程序
cd ..
python main.py
```

## 项目结构

```
panda-editor/
├── main.py               # 程序入口
├── src/
│   ├── module/           # 语法映射表与库源码常量
│   ├── static/           # 静态资源
│   ├── utils/            # 工具模块
│   └── views/            # UI 界面
├── docs/                 # 使用教程与更新日志
├── Environment/          # Python 运行时
└── pyproject.toml        # 项目配置与依赖声明
```

## 核心功能

| 功能         | 说明                                                                                         |
|--------------|----------------------------------------------------------------------------------------------|
| **代码编辑** | 语法高亮、智能代码补全、中文输入法支持                                                       |
| **文件管理** | 文件树浏览、打开/保存/另存为/导入扩展                                                        |
| **代码执行** | 一键运行和编译 CN 代码                                                                       |
| **内嵌终端** | 命令行终端，支持命令历史和目录切换                                                           |
| **积木编程** | 9 类基础语法、12 类函数库与 9 类内置扩展库，共 424 块中文积木，一键生成代码到指定的 .cn 文件 |
| **主题切换** | 暗夜/浅色模式，自定义字体大小                                                                |

## 使用教程

详细的使用说明请参见 [使用教程](docs/USAGE.md)。

## 下载可执行文件

- PandaEditor-Setup-x.x.x-Online.exe 在线版本需要网络安装运行时依赖
- PandaEditor-Setup-x.x.x-Offline.exe 离线版本无需网络安装运行时依赖
- [release](https://github.com/cxfjh/panda-editor/releases)
- [123云盘](https://1825984093.share.123pan.cn/123pan/IzrNjv-xto5A)

## 官方网站

- [PandaEditor](https://cxfjh.github.io)

## 更新日志

查看 [CHANGELOG](docs/CHANGELOG.md) 了解最新版本变化。

## 贡献指南

欢迎为熊猫编辑器贡献力量！你可以通过以下方式参与：

1. **提交 Bug** - 在 [Issues](https://github.com/cxfjh/panda-editor/issues) 页面报告问题
2. **功能建议** - 提交 Feature Request
3. **代码贡献** - 提交 Pull Request
4. **文档改进** - 完善使用教程和文档

修改代码时请参考 [`docs/CODE_STYLE.md`](docs/CODE_STYLE.md) 里面的规范文档。

## 许可证

本项目采用 [GPL v3](./LICENSE) 开源许可证。

## 支持与反馈

遇到问题或有建议？

- 邮件联系：2449579731@qq.com
- [提交 Issue](https://github.com/cxfjh/panda-editor/issues)
- [讨论区](https://github.com/cxfjh/panda-editor/discussions)

## 致谢

感谢所有为熊猫编辑器做出贡献的开发者和用户！