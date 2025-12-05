"""OAuth configuration module for FrankenAgent Lab.

This module provides environment-aware OAuth configuration for different providers
(Google, GitHub) with support for environment-specific redirect URIs and SSL settings.

Key Features:
- Provider-specific configuration (Google, GitHub)
- Environment-aware redirect URIs
- SSL verification control per environment
- Clear error messages for missing credentials
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from frankenagent.config.environment import Environment, get_config

logger = logging.getLogger(__name__)


class OAuthProvider(Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"


@dataclass
class OAuthConfig:
    """OAuth configuration for a specific provider.
    
    This class encapsulates OAuth credentials and settings for a single provider,
    with environment-specific behavior for redirect URIs and SSL verification.
    
    Attributes:
        provider: OAuth provider name (google, github)
        client_id: OAuth client ID
        client_secret: OAuth client secret
        redirect_uri: OAuth callback URL
        ssl_verify: Whether to verify SSL certificates
        environment: Current environment (development, production, test)
    """
    
    provider: str
    client_id: str
    client_secret: str
    redirect_uri: str
    ssl_verify: bool
    environment: Environment
    
    @classmethod
    def for_environment(
        cls,
        provider: str,
        environment: Optional[Environment] = None
    ) -> "OAuthConfig":
        """Get OAuth configuration for a provider in the current environment.
        
        This method loads OAuth credentials from environment variables and
        configures provider-specific settings based on the environment.
        
        Args:
            provider: OAuth provider name ("google" or "github")
            environment: Environment to configure for (defaults to current)
            
        Returns:
            OAuthConfig: Configured OAuth settings for the provider
            
        Raises:
            ValueError: If provider is invalid or credentials are missing
        """
        # Validate provider
        try:
            provider_enum = OAuthProvider(provider.lower())
        except ValueError:
            raise ValueError(
                f"Invalid OAuth provider: '{provider}'. "
                f"Must be one of: {', '.join([p.value for p in OAuthProvider])}"
            )
        
        # Get environment config
        if environment is None:
            env_config = get_config()
            environment = env_config.environment
        else:
            env_config = get_config()
        
        # Get provider-specific credentials
        if provider_enum == OAuthProvider.GOOGLE:
            client_id = env_config.google_client_id
            client_secret = env_config.google_client_secret
        elif provider_enum == OAuthProvider.GITHUB:
            client_id = env_config.github_client_id
            client_secret = env_config.github_client_secret
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Validate credentials
        if not client_id or not client_secret:
            raise ValueError(
                f"OAuth credentials not configured for {provider}. "
                f"Please set {provider.upper()}_CLIENT_ID and "
                f"{provider.upper()}_CLIENT_SECRET in your .env file.\n\n"
                f"Get credentials at:\n"
                f"  Google: https://console.cloud.google.com/apis/credentials\n"
                f"  GitHub: https://github.com/settings/developers"
            )
        
        # Get redirect URI (environment-specific)
        redirect_uri = env_config.oauth_redirect_uri
        if not redirect_uri:
            # Construct default based on environment
            if environment == Environment.DEVELOPMENT:
                redirect_uri = "http://localhost:8000/api/auth/callback"
            elif environment == Environment.PRODUCTION:
                # In production, this should be explicitly set
                raise ValueError(
                    "OAUTH_REDIRECT_URI must be explicitly set in production. "
                    "Example: https://yourdomain.com/api/auth/callback"
                )
            else:
                redirect_uri = "http://localhost:8000/api/auth/callback"
        
        # Get SSL verification setting
        ssl_verify = env_config.ssl_verify
        
        # Log warning if SSL verification is disabled
        if not ssl_verify and environment != Environment.TEST:
            logger.warning(
                f"SSL verification is DISABLED for {provider} OAuth. "
                f"This is acceptable in development but should NEVER be used in production."
            )
        
        return cls(
            provider=provider_enum.value,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            ssl_verify=ssl_verify,
            environment=environment
        )
    
    @classmethod
    def for_google(cls, environment: Optional[Environment] = None) -> "OAuthConfig":
        """Get Google OAuth configuration for the current environment.
        
        Convenience method for getting Google OAuth config.
        
        Args:
            environment: Environment to configure for (defaults to current)
            
        Returns:
            OAuthConfig: Google OAuth configuration
        """
        return cls.for_environment("google", environment)
    
    @classmethod
    def for_github(cls, environment: Optional[Environment] = None) -> "OAuthConfig":
        """Get GitHub OAuth configuration for the current environment.
        
        Convenience method for getting GitHub OAuth config.
        
        Args:
            environment: Environment to configure for (defaults to current)
            
        Returns:
            OAuthConfig: GitHub OAuth configuration
        """
        return cls.for_environment("github", environment)
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get the OAuth authorization URL for this provider.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL to redirect user to
        """
        if self.provider == "google":
            base_url = "https://accounts.google.com/o/oauth2/v2/auth"
            scope = "openid email profile"
            params = [
                f"client_id={self.client_id}",
                f"redirect_uri={self.redirect_uri}",
                "response_type=code",
                f"scope={scope}",
            ]
            if state:
                params.append(f"state={state}")
            return f"{base_url}?{'&'.join(params)}"
        
        elif self.provider == "github":
            base_url = "https://github.com/login/oauth/authorize"
            scope = "read:user user:email"
            params = [
                f"client_id={self.client_id}",
                f"redirect_uri={self.redirect_uri}",
                f"scope={scope}",
            ]
            if state:
                params.append(f"state={state}")
            return f"{base_url}?{'&'.join(params)}"
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def get_token_url(self) -> str:
        """Get the OAuth token exchange URL for this provider.
        
        Returns:
            str: Token exchange URL
        """
        if self.provider == "google":
            return "https://oauth2.googleapis.com/token"
        elif self.provider == "github":
            return "https://github.com/login/oauth/access_token"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def get_userinfo_url(self) -> str:
        """Get the user info URL for this provider.
        
        Returns:
            str: User info URL
        """
        if self.provider == "google":
            return "https://www.googleapis.com/oauth2/v2/userinfo"
        elif self.provider == "github":
            return "https://api.github.com/user"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def is_configured(self) -> bool:
        """Check if OAuth is properly configured for this provider.
        
        Returns:
            bool: True if client_id and client_secret are set
        """
        return bool(self.client_id and self.client_secret)
    
    def validate(self) -> list[str]:
        """Validate OAuth configuration.
        
        Returns:
            list[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.client_id:
            errors.append(f"{self.provider.upper()}_CLIENT_ID is required")
        
        if not self.client_secret:
            errors.append(f"{self.provider.upper()}_CLIENT_SECRET is required")
        
        if not self.redirect_uri:
            errors.append("OAUTH_REDIRECT_URI is required")
        
        # Production-specific validation
        if self.environment == Environment.PRODUCTION:
            if not self.redirect_uri.startswith("https://"):
                errors.append(
                    f"OAuth redirect URI must use HTTPS in production. "
                    f"Got: {self.redirect_uri}"
                )
            
            if not self.ssl_verify:
                errors.append(
                    "SSL verification must be enabled in production for OAuth"
                )
        
        return errors


def get_oauth_config(provider: str) -> OAuthConfig:
    """Get OAuth configuration for a provider.
    
    Convenience function for getting OAuth config.
    
    Args:
        provider: OAuth provider name ("google" or "github")
        
    Returns:
        OAuthConfig: OAuth configuration for the provider
    """
    return OAuthConfig.for_environment(provider)


def is_oauth_configured(provider: str) -> bool:
    """Check if OAuth is configured for a provider.
    
    Args:
        provider: OAuth provider name ("google" or "github")
        
    Returns:
        bool: True if OAuth is configured, False otherwise
    """
    try:
        config = get_oauth_config(provider)
        return config.is_configured()
    except ValueError:
        return False
