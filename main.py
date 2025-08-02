#!/usr/bin/env python3
"""
Website Monitoring and Reporting System
Main entry point for the application
"""

import sys
import asyncio
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from gui.main_window import MainWindow
from utils.logger import setup_logging


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Create PyQt5 application
    app = QApplication(sys.argv)
    app.setApplicationName("网站巡检系统")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    logger.info("Application started successfully")
    
    # Start the event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()