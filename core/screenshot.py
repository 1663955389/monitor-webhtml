"""
Screenshot capture functionality using Selenium
"""

import asyncio
import logging
import io
from pathlib import Path
from typing import Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

from config.settings import config_manager
from utils.helpers import sanitize_filename, ensure_directory


class ScreenshotCapture:
    """Handles website screenshot capture"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_monitoring_config()
        self.directories_config = config_manager.get_directories_config()
        
        # Setup screenshot directory
        self.screenshot_dir = ensure_directory(self.directories_config.screenshots)
        
        self._driver = None
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver for screenshots"""
        if self._driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            chrome_options.add_argument(f'--window-size={self.config.screenshot_width},{self.config.screenshot_height}')
            
            # Install and setup ChromeDriver
            try:
                service = Service(ChromeDriverManager().install())
                self._driver = webdriver.Chrome(service=service, options=chrome_options)
                self._driver.set_window_size(self.config.screenshot_width, self.config.screenshot_height)
            except Exception as e:
                self.logger.error(f"Failed to setup Chrome driver: {e}")
                raise
        
        return self._driver
    
    async def capture_screenshot(self, url: str, website_name: str) -> Optional[str]:
        """Capture screenshot of a website"""
        try:
            # Run screenshot capture in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            screenshot_path = await loop.run_in_executor(
                None, self._capture_screenshot_sync, url, website_name
            )
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot for {url}: {e}")
            return None
    
    def _capture_screenshot_sync(self, url: str, website_name: str) -> str:
        """Synchronous screenshot capture"""
        driver = self._setup_driver()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitize_filename(website_name)}_{timestamp}.png"
        screenshot_path = self.screenshot_dir / filename
        
        try:
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            driver.implicitly_wait(10)
            
            # Take screenshot
            driver.save_screenshot(str(screenshot_path))
            
            # Optimize screenshot if needed
            if self.config.screenshot_quality < 100:
                self._optimize_screenshot(screenshot_path)
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Error capturing screenshot: {e}")
            raise
    
    def _optimize_screenshot(self, screenshot_path: Path) -> None:
        """Optimize screenshot file size"""
        try:
            with Image.open(screenshot_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save with optimization
                img.save(
                    screenshot_path,
                    'PNG',
                    optimize=True,
                    quality=self.config.screenshot_quality
                )
        except Exception as e:
            self.logger.error(f"Failed to optimize screenshot: {e}")
    
    async def capture_element_screenshot(self, url: str, website_name: str, element_selector: str) -> Optional[str]:
        """Capture screenshot of a specific element"""
        try:
            loop = asyncio.get_event_loop()
            screenshot_path = await loop.run_in_executor(
                None, self._capture_element_screenshot_sync, url, website_name, element_selector
            )
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to capture element screenshot for {url}: {e}")
            return None
    
    def _capture_element_screenshot_sync(self, url: str, website_name: str, element_selector: str) -> str:
        """Synchronous element screenshot capture"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        driver = self._setup_driver()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitize_filename(website_name)}_element_{timestamp}.png"
        screenshot_path = self.screenshot_dir / filename
        
        try:
            # Navigate to URL
            driver.get(url)
            
            # Wait for element to be present
            wait = WebDriverWait(driver, 10)
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, element_selector)))
            
            # Take element screenshot
            element.screenshot(str(screenshot_path))
            
            # Optimize screenshot if needed
            if self.config.screenshot_quality < 100:
                self._optimize_screenshot(screenshot_path)
            
            self.logger.info(f"Element screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Error capturing element screenshot: {e}")
            raise
    
    async def capture_full_page_screenshot(self, url: str, website_name: str) -> Optional[str]:
        """Capture full page screenshot (scrollable content)"""
        try:
            loop = asyncio.get_event_loop()
            screenshot_path = await loop.run_in_executor(
                None, self._capture_full_page_screenshot_sync, url, website_name
            )
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to capture full page screenshot for {url}: {e}")
            return None
    
    def _capture_full_page_screenshot_sync(self, url: str, website_name: str) -> str:
        """Synchronous full page screenshot capture"""
        driver = self._setup_driver()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitize_filename(website_name)}_fullpage_{timestamp}.png"
        screenshot_path = self.screenshot_dir / filename
        
        try:
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            driver.implicitly_wait(10)
            
            # Get page dimensions
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            
            # Take screenshots in chunks and stitch them together
            screenshots = []
            current_position = 0
            
            while current_position < total_height:
                # Scroll to current position
                driver.execute_script(f"window.scrollTo(0, {current_position})")
                
                # Wait for scroll to complete
                driver.implicitly_wait(1)
                
                # Take screenshot
                screenshot = driver.get_screenshot_as_png()
                screenshots.append(Image.open(io.BytesIO(screenshot)))
                
                current_position += viewport_height
            
            # Stitch screenshots together
            if screenshots:
                total_width = screenshots[0].width
                total_height = sum(img.height for img in screenshots)
                
                combined_image = Image.new('RGB', (total_width, total_height))
                
                y_offset = 0
                for img in screenshots:
                    combined_image.paste(img, (0, y_offset))
                    y_offset += img.height
                
                # Save combined image
                combined_image.save(screenshot_path, 'PNG')
                
                # Clean up individual screenshots
                for img in screenshots:
                    img.close()
            
            self.logger.info(f"Full page screenshot saved: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Error capturing full page screenshot: {e}")
            raise
    
    def cleanup_old_screenshots(self, days: int = 30) -> None:
        """Remove screenshots older than specified days"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 3600)
        
        for screenshot_file in self.screenshot_dir.glob("*.png"):
            if screenshot_file.is_file():
                file_time = screenshot_file.stat().st_mtime
                if file_time < cutoff_time:
                    try:
                        screenshot_file.unlink()
                        self.logger.info(f"Deleted old screenshot: {screenshot_file}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete screenshot {screenshot_file}: {e}")
    
    def close(self) -> None:
        """Close the WebDriver"""
        if self._driver:
            try:
                self._driver.quit()
                self._driver = None
                self.logger.info("Screenshot driver closed")
            except Exception as e:
                self.logger.error(f"Error closing screenshot driver: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()