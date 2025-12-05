"""OAuth authentication service for Google and GitHub."""

import logging
import certifi
from typing import Optional, Dict, Any
import httpx

from frankenagent.config.oauth import OAuthConfig, get_oauth_config
from frankenagent.config.environment import Environment

logger = logging.getLogger(__name__)


class OAuthService:
    """
    OAuth service for third-party authentication.
    
    Supports Google and GitHub OAuth 2.0 flows with environment-aware configuration.
    Uses OAuthConfig for provider-specific settings including SSL verification.
    """
    
    def __init__(self):
        """Initialize OAuth service with environment-aware configurations."""
        # Load OAuth configurations for supported providers
        # These will be None if credentials are not configured
        self._google_config: Optional[OAuthConfig] = None
        self._github_config: Optional[OAuthConfig] = None
        
        try:
            self._google_config = get_oauth_config("google")
            logger.info(f"Google OAuth configured for {self._google_config.environment.value}")
        except ValueError as e:
            logger.debug(f"Google OAuth not configured: {e}")
        
        try:
            self._github_config = get_oauth_config("github")
            logger.info(f"GitHub OAuth configured for {self._github_config.environment.value}")
        except ValueError as e:
            logger.debug(f"GitHub OAuth not configured: {e}")
    
    def _get_ssl_verify(self, config: OAuthConfig) -> bool | str:
        """Get SSL verification setting for HTTP client.
        
        Args:
            config: OAuth configuration with ssl_verify setting
            
        Returns:
            bool | str: False to disable, True to use default, or path to CA bundle
        """
        if not config.ssl_verify:
            # Log warning when SSL verification is disabled
            if config.environment == Environment.DEVELOPMENT:
                logger.warning(
                    f"SSL verification is DISABLED for {config.provider} OAuth in development. "
                    f"This allows localhost redirect URIs to work on macOS. "
                    f"SSL verification will be ENABLED in production."
                )
            else:
                logger.error(
                    f"SSL verification is DISABLED for {config.provider} OAuth in {config.environment.value}! "
                    f"This should NEVER happen in production."
                )
            return False
        
        # Use certifi CA bundle for proper SSL verification
        return certifi.where()
    
    async def exchange_google_code(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """
        Exchange Google authorization code for user info.
        
        Args:
            code: Authorization code from Google
            redirect_uri: Redirect URI used in the OAuth flow
            
        Returns:
            Dict with user info (email, name, picture) or None if failed
        """
        if not self._google_config:
            logger.error("Google OAuth credentials not configured")
            return None
        
        try:
            # Get SSL verification setting
            ssl_verify = self._get_ssl_verify(self._google_config)
            
            # Exchange code for access token
            async with httpx.AsyncClient(verify=ssl_verify) as client:
                token_response = await client.post(
                    self._google_config.get_token_url(),
                    data={
                        "code": code,
                        "client_id": self._google_config.client_id,
                        "client_secret": self._google_config.client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )
                
                if token_response.status_code != 200:
                    logger.error(f"Google token exchange failed: {token_response.text}")
                    return None
                
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                
                if not access_token:
                    logger.error("No access token in Google response")
                    return None
                
                # Get user info
                user_response = await client.get(
                    self._google_config.get_userinfo_url(),
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                
                if user_response.status_code != 200:
                    logger.error(f"Google user info failed: {user_response.text}")
                    return None
                
                user_data = user_response.json()
                
                return {
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "picture": user_data.get("picture"),
                    "provider": "google",
                    "provider_user_id": user_data.get("id"),
                }
        
        except Exception as e:
            logger.error(f"Google OAuth error: {e}", exc_info=True)
            return None
    
    async def exchange_github_code(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """
        Exchange GitHub authorization code for user info.
        
        Args:
            code: Authorization code from GitHub
            redirect_uri: Redirect URI used in the OAuth flow
            
        Returns:
            Dict with user info (email, name, avatar_url) or None if failed
        """
        if not self._github_config:
            logger.error("GitHub OAuth credentials not configured")
            return None
        
        try:
            # Get SSL verification setting
            ssl_verify = self._get_ssl_verify(self._github_config)
            
            # Exchange code for access token
            async with httpx.AsyncClient(verify=ssl_verify) as client:
                token_response = await client.post(
                    self._github_config.get_token_url(),
                    data={
                        "code": code,
                        "client_id": self._github_config.client_id,
                        "client_secret": self._github_config.client_secret,
                        "redirect_uri": redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                )
                
                if token_response.status_code != 200:
                    logger.error(f"GitHub token exchange failed: {token_response.text}")
                    return None
                
                token_data = token_response.json()
                access_token = token_data.get("access_token")
                
                if not access_token:
                    logger.error("No access token in GitHub response")
                    return None
                
                # Get user info
                user_response = await client.get(
                    self._github_config.get_userinfo_url(),
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                
                if user_response.status_code != 200:
                    logger.error(f"GitHub user info failed: {user_response.text}")
                    return None
                
                user_data = user_response.json()
                
                # Get primary email if not public
                email = user_data.get("email")
                if not email:
                    email_response = await client.get(
                        "https://api.github.com/user/emails",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/json",
                        },
                    )
                    
                    if email_response.status_code == 200:
                        emails = email_response.json()
                        primary_email = next(
                            (e for e in emails if e.get("primary") and e.get("verified")),
                            None
                        )
                        if primary_email:
                            email = primary_email.get("email")
                
                return {
                    "email": email,
                    "name": user_data.get("name") or user_data.get("login"),
                    "picture": user_data.get("avatar_url"),
                    "provider": "github",
                    "provider_user_id": str(user_data.get("id")),
                }
        
        except Exception as e:
            logger.error(f"GitHub OAuth error: {e}", exc_info=True)
            return None
    
    def get_google_auth_url(self, state: str) -> str:
        """
        Get Google OAuth authorization URL.
        
        Args:
            state: CSRF protection state parameter
            
        Returns:
            Authorization URL to redirect user to
            
        Raises:
            ValueError: If Google OAuth is not configured
        """
        if not self._google_config:
            raise ValueError(
                "Google OAuth not configured. "
                "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file."
            )
        
        return self._google_config.get_authorization_url(state)
    
    def get_github_auth_url(self, state: str) -> str:
        """
        Get GitHub OAuth authorization URL.
        
        Args:
            state: CSRF protection state parameter
            
        Returns:
            Authorization URL to redirect user to
            
        Raises:
            ValueError: If GitHub OAuth is not configured
        """
        if not self._github_config:
            raise ValueError(
                "GitHub OAuth not configured. "
                "Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in your .env file."
            )
        
        return self._github_config.get_authorization_url(state)
    
    @property
    def google_redirect_uri(self) -> Optional[str]:
        """Get the configured Google OAuth redirect URI."""
        return self._google_config.redirect_uri if self._google_config else None
    
    @property
    def github_redirect_uri(self) -> Optional[str]:
        """Get the configured GitHub OAuth redirect URI."""
        return self._github_config.redirect_uri if self._github_config else None
    
    def is_google_configured(self) -> bool:
        """Check if Google OAuth is configured."""
        return self._google_config is not None and self._google_config.is_configured()
    
    def is_github_configured(self) -> bool:
        """Check if GitHub OAuth is configured."""
        return self._github_config is not None and self._github_config.is_configured()
