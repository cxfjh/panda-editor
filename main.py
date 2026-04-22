import sys
import asyncio
from src.utils.config import init_config
from src.views.main_win import MainWindowUI
from PySide6.QtWidgets import QApplication, QMainWindow


# 异步执行初始化窗口配置
async def main():
    # 异步执行初始化文件配置
    await asyncio.to_thread(init_config)

    # 创建应用程序对象
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    MainWindowUI().setup_ui(main_window)

    # 显示主窗口
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    asyncio.run(main())
