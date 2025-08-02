"""
Authentication management for website monitoring
"""

import asyncio
import aiohttp
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from utils.crypto import CryptoManager
from config.settings import config_manager


@dataclass
class AuthSession:
    """Authentication session data"""
    session_id: str
    auth_type: str
    expires_at: datetime
    session_data: Dict[str, Any]
    cookies: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None


class AuthenticationManager:
    """Manages authentication sessions for various auth types"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_authentication_config()
        self.crypto_manager = CryptoManager(self.config.encryption_key)
        
        # Active sessions
        self.sessions: Dict[str, AuthSession] = {}
        self.http_session: Optional[aiohttp.ClientSession] = None
    
    async def get_authenticated_session(self, auth_type: Optional[str], auth_config: Dict[str, Any]) -> aiohttp.ClientSession:
        """Get an authenticated HTTP session"""
        if self.http_session is None or self.http_session.closed:
            self.http_session = aiohttp.ClientSession()
        
        if not auth_type or auth_type == 'none':
            return self.http_session
        
        session_key = self._generate_session_key(auth_type, auth_config)
        
        # Check if we have a valid cached session
        if session_key in self.sessions:
            session = self.sessions[session_key]
            if session.expires_at > datetime.now():
                # Apply session data to HTTP session
                await self._apply_session_data(session)
                return self.http_session
            else:
                # Session expired, remove it
                del self.sessions[session_key]
        
        # Create new authenticated session
        session = await self._create_authenticated_session(auth_type, auth_config)
        if session:
            self.sessions[session_key] = session
            await self._apply_session_data(session)
        
        return self.http_session
    
    async def _create_authenticated_session(self, auth_type: str, auth_config: Dict[str, Any]) -> Optional[AuthSession]:
        """Create a new authenticated session"""
        try:
            if auth_type == 'basic':
                return await self._create_basic_auth_session(auth_config)
            elif auth_type == 'bearer':
                return await self._create_bearer_auth_session(auth_config)
            elif auth_type == 'form':
                return await self._create_form_auth_session(auth_config)
            else:
                self.logger.error(f"Unknown auth type: {auth_type}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to create {auth_type} auth session: {e}")
            return None
    
    async def _create_basic_auth_session(self, auth_config: Dict[str, Any]) -> AuthSession:
        """Create HTTP Basic authentication session"""
        username = auth_config.get('username', '')
        password = auth_config.get('password', '')
        
        if not username or not password:
            raise ValueError("Username and password required for basic auth")
        
        # Create basic auth header
        import base64
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers = {'Authorization': f'Basic {credentials}'}
        
        expires_at = datetime.now() + timedelta(seconds=self.config.session_timeout)
        
        return AuthSession(
            session_id=self._generate_session_id(),
            auth_type='basic',
            expires_at=expires_at,
            session_data=auth_config,
            headers=headers
        )
    
    async def _create_bearer_auth_session(self, auth_config: Dict[str, Any]) -> AuthSession:
        """Create Bearer token authentication session"""
        token = auth_config.get('token', '')
        
        if not token:
            raise ValueError("Token required for bearer auth")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        expires_at = datetime.now() + timedelta(seconds=self.config.session_timeout)
        
        return AuthSession(
            session_id=self._generate_session_id(),
            auth_type='bearer',
            expires_at=expires_at,
            session_data=auth_config,
            headers=headers
        )
    
    async def _create_form_auth_session(self, auth_config: Dict[str, Any]) -> AuthSession:
        """Create form-based authentication session"""
        login_url = auth_config.get('login_url', '')
        username = auth_config.get('username', '')
        password = auth_config.get('password', '')
        username_field = auth_config.get('username_field', 'username')
        password_field = auth_config.get('password_field', 'password')
        
        if not all([login_url, username, password]):
            raise ValueError("login_url, username, and password required for form auth")
        
        # Create temporary session for login
        temp_session = aiohttp.ClientSession()
        
        try:
            # Prepare login data
            login_data = {
                username_field: username,
                password_field: password
            }
            
            # Add any additional form fields
            additional_fields = auth_config.get('additional_fields', {})
            login_data.update(additional_fields)
            
            # Perform login
            async with temp_session.post(login_url, data=login_data) as response:
                if response.status not in [200, 302]:  # Accept redirects as success
                    raise ValueError(f"Login failed with status {response.status}")
                
                # Extract cookies
                cookies = {}
                for cookie in temp_session.cookie_jar:
                    cookies[cookie.key] = cookie.value
                
                expires_at = datetime.now() + timedelta(seconds=self.config.session_timeout)
                
                return AuthSession(
                    session_id=self._generate_session_id(),
                    auth_type='form',
                    expires_at=expires_at,
                    session_data=auth_config,
                    cookies=cookies
                )
        
        finally:
            await temp_session.close()
    
    async def _apply_session_data(self, session: AuthSession) -> None:
        """Apply session data to the HTTP session"""
        if session.headers:
            # Update session headers
            self.http_session.headers.update(session.headers)
        
        if session.cookies:
            # Update session cookies
            for name, value in session.cookies.items():
                self.http_session.cookie_jar.update_cookies({name: value})
    
    def _generate_session_key(self, auth_type: str, auth_config: Dict[str, Any]) -> str:
        """Generate a unique session key"""
        # Create a key based on auth type and critical config values
        key_data = {
            'auth_type': auth_type,
            'url': auth_config.get('login_url', ''),
            'username': auth_config.get('username', ''),
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"{auth_type}_{hash(key_string)}"
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def logout_session(self, session_key: str) -> None:
        """Logout and remove a session"""
        if session_key in self.sessions:
            session = self.sessions[session_key]
            
            # Perform logout if supported
            if session.auth_type == 'form':
                await self._perform_form_logout(session)
            
            del self.sessions[session_key]
            self.logger.info(f"Logged out session: {session_key}")
    
    async def _perform_form_logout(self, session: AuthSession) -> None:
        """Perform form-based logout"""
        try:
            logout_url = session.session_data.get('logout_url')
            if logout_url and self.http_session:
                async with self.http_session.get(logout_url) as response:
                    self.logger.info(f"Logout response: {response.status}")
        except Exception as e:
            self.logger.error(f"Error during logout: {e}")
    
    async def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        current_time = datetime.now()
        expired_keys = [
            key for key, session in self.sessions.items()
            if session.expires_at <= current_time
        ]
        
        for key in expired_keys:
            del self.sessions[key]
            self.logger.info(f"Removed expired session: {key}")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about active sessions"""
        return {
            'active_sessions': len(self.sessions),
            'sessions': [
                {
                    'session_id': session.session_id,
                    'auth_type': session.auth_type,
                    'expires_at': session.expires_at.isoformat(),
                    'time_remaining': (session.expires_at - datetime.now()).total_seconds()
                }
                for session in self.sessions.values()
            ]
        }
    
    async def close(self) -> None:
        """Close the authentication manager and cleanup resources"""
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
        
        self.sessions.clear()
        self.logger.info("Authentication manager closed")