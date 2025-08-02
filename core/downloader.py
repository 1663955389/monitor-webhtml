"""
File download functionality
"""

import asyncio
import aiohttp
import aiofiles
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse

from config.settings import config_manager
from utils.helpers import sanitize_filename, ensure_directory, get_file_extension, parse_size


class FileDownloader:
    """Handles file downloads from URLs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_downloads_config()
        self.directories_config = config_manager.get_directories_config()
        
        # Setup download directory
        self.download_dir = ensure_directory(self.directories_config.downloads)
        
        # Parse max file size
        self.max_file_size = parse_size(self.config.max_file_size)
    
    async def download_file(self, url: str, website_name: str, custom_filename: Optional[str] = None) -> Optional[str]:
        """Download a file from URL"""
        try:
            # Generate filename
            if custom_filename:
                filename = sanitize_filename(custom_filename)
            else:
                filename = self._generate_filename(url, website_name)
            
            file_path = self.download_dir / filename
            
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to download {url}: HTTP {response.status}")
                        return None
                    
                    # Check content length
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        size = int(content_length)
                        if size > self.max_file_size:
                            self.logger.error(f"File too large: {size} bytes > {self.max_file_size} bytes")
                            return None
                    
                    # Download file
                    async with aiofiles.open(file_path, 'wb') as f:
                        downloaded_size = 0
                        async for chunk in response.content.iter_chunked(8192):
                            downloaded_size += len(chunk)
                            
                            # Check size limit during download
                            if downloaded_size > self.max_file_size:
                                self.logger.error(f"File too large during download: {downloaded_size} bytes")
                                # Remove partial file
                                try:
                                    file_path.unlink()
                                except:
                                    pass
                                return None
                            
                            await f.write(chunk)
            
            self.logger.info(f"Downloaded file: {file_path} ({downloaded_size} bytes)")
            return str(file_path)
            
        except asyncio.TimeoutError:
            self.logger.error(f"Download timeout for {url}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")
            return None
    
    def _generate_filename(self, url: str, website_name: str) -> str:
        """Generate filename for downloaded file"""
        parsed_url = urlparse(url)
        
        # Try to get filename from URL path
        path = Path(parsed_url.path)
        if path.name and '.' in path.name:
            filename = path.name
        else:
            # Generate filename based on URL and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = get_file_extension(url) or '.bin'
            filename = f"{sanitize_filename(website_name)}_download_{timestamp}{extension}"
        
        return sanitize_filename(filename)
    
    async def download_multiple_files(self, urls: list, website_name: str) -> list:
        """Download multiple files concurrently"""
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.download_file(url, website_name))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        successful_downloads = []
        for result in results:
            if isinstance(result, str):  # Successful download returns file path
                successful_downloads.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Download failed with exception: {result}")
        
        return successful_downloads
    
    def cleanup_old_downloads(self, days: int = 30) -> None:
        """Remove downloaded files older than specified days"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 3600)
        
        for download_file in self.download_dir.rglob("*"):
            if download_file.is_file():
                file_time = download_file.stat().st_mtime
                if file_time < cutoff_time:
                    try:
                        download_file.unlink()
                        self.logger.info(f"Deleted old download: {download_file}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete download {download_file}: {e}")
    
    def get_download_info(self, file_path: str) -> dict:
        """Get information about a downloaded file"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {'exists': False}
            
            stat = path.stat()
            return {
                'exists': True,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': path.suffix,
                'filename': path.name
            }
        except Exception as e:
            self.logger.error(f"Failed to get file info for {file_path}: {e}")
            return {'exists': False, 'error': str(e)}