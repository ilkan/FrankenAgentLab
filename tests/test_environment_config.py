"""Tests for environment configuration module.

This module tests the environment configuration loading, validation,
and error handling functionality.
"""

import os
import pytest
from pathlib import Path
from frankenagent.config.environment import (
    Environment,
    EnvironmentConfig,
    get_config,
    reload_config,
)


class TestEnvironmentEnum:
    """Tests for Environment enum."""
    
    def test_environment_values(self):
        """Test that Environment enum has expected values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TEST.value == "test"


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig class."""
    
    def test_load_with_development_environment(self, monkeypatch, tmp_path):
        """Test loading configuration with ENVIRONMENT=development."""
        # Change to temp directory to avoid loading actual .env files
        monkeypatch.chdir(tmp_path)
        
        # Set environment variable
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("LOCAL_DATABASE_URL", "sqlite:///./tmp/test.db")
        monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
        monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")
        monkeypatch.setenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback")
        
        # Load config
        config = EnvironmentConfig.load()
        
        # Verify
        assert config.environment == Environment.DEVELOPMENT
        assert config.database_url == "sqlite:///./tmp/test.db"
        assert config.frontend_url == "http://localhost:3000"
        assert config.backend_url == "http://localhost:8000"
        assert config.ssl_verify is False  # Disabled in development
    
    def test_load_with_production_environment(self, monkeypatch, tmp_path):
        """Test loading configuration with ENVIRONMENT=production."""
        # Change to temp directory to avoid loading actual .env files
        monkeypatch.chdir(tmp_path)
        
        # Set environment variables
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("PRODUCTION_DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("FRONTEND_URL", "https://example.com")
        monkeypatch.setenv("BACKEND_URL", "https://api.example.com")
        monkeypatch.setenv("OAUTH_REDIRECT_URI", "https://example.com/callback")
        monkeypatch.setenv("JWT_SECRET_KEY", "production-secret-key")
        
        # Load config
        config = EnvironmentConfig.load()
        
        # Verify
        assert config.environment == Environment.PRODUCTION
        assert config.ssl_verify is True  # Enabled in production
        assert config.database_url == "postgresql://localhost/db"
    
    def test_load_with_invalid_environment(self, monkeypatch):
        """Test that invalid ENVIRONMENT value raises ValueError."""
        monkeypatch.setenv("ENVIRONMENT", "invalid")
        
        with pytest.raises(ValueError) as exc_info:
            EnvironmentConfig.load()
        
        assert "Invalid ENVIRONMENT value" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)
    
    def test_load_defaults_to_development(self, monkeypatch):
        """Test that missing ENVIRONMENT defaults to development."""
        # Remove ENVIRONMENT variable
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("LOCAL_DATABASE_URL", "sqlite:///./tmp/test.db")
        monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
        monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")
        monkeypatch.setenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback")
        
        # Load config
        config = EnvironmentConfig.load()
        
        # Verify defaults to development
        assert config.environment == Environment.DEVELOPMENT
    
    def test_ssl_verify_override(self, monkeypatch):
        """Test that SSL_VERIFY environment variable overrides default."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("SSL_VERIFY", "false")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("PRODUCTION_DATABASE_URL", "postgresql://localhost/db")
        monkeypatch.setenv("FRONTEND_URL", "https://example.com")
        monkeypatch.setenv("BACKEND_URL", "https://api.example.com")
        monkeypatch.setenv("OAUTH_REDIRECT_URI", "https://example.com/callback")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-key")
        
        config = EnvironmentConfig.load()
        
        # SSL should be disabled even in production
        assert config.ssl_verify is False


class TestConfigValidation:
    """Tests for configuration validation."""
    
    def test_validate_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        config = EnvironmentConfig(
            environment=Environment.DEVELOPMENT,
            database_url="",  # Missing
            frontend_url="",  # Missing
            backend_url="",  # Missing
            oauth_redirect_uri="",  # Missing
            ssl_verify=False,
        )
        
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("DATABASE_URL" in error for error in errors)
        assert any("FRONTEND_URL" in error for error in errors)
        assert any("BACKEND_URL" in error for error in errors)
        assert any("OAUTH_REDIRECT_URI" in error for error in errors)
    
    def test_validate_production_requires_https(self):
        """Test that production requires HTTPS URLs."""
        config = EnvironmentConfig(
            environment=Environment.PRODUCTION,
            database_url="postgresql://localhost/db",
            frontend_url="http://example.com",  # HTTP not allowed
            backend_url="http://api.example.com",  # HTTP not allowed
            oauth_redirect_uri="http://example.com/callback",  # HTTP not allowed
            ssl_verify=True,
            jwt_secret_key="production-key",
        )
        
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("HTTPS" in error and "FRONTEND_URL" in error for error in errors)
        assert any("HTTPS" in error and "BACKEND_URL" in error for error in errors)
        assert any("HTTPS" in error and "OAUTH_REDIRECT_URI" in error for error in errors)
    
    def test_validate_production_requires_database_configuration(self):
        """Test that production requires a database connection string."""
        config = EnvironmentConfig(
            environment=Environment.PRODUCTION,
            database_url="",
            frontend_url="https://example.com",
            backend_url="https://api.example.com",
            oauth_redirect_uri="https://example.com/callback",
            ssl_verify=True,
            jwt_secret_key="production-key",
        )
        
        errors = config.validate()
        
        assert any("Production database is not configured" in error for error in errors)
    
    def test_validate_production_rejects_default_jwt_secret(self):
        """Test that production rejects default JWT secret."""
        config = EnvironmentConfig(
            environment=Environment.PRODUCTION,
            database_url="postgresql://localhost/db",
            frontend_url="https://example.com",
            backend_url="https://api.example.com",
            oauth_redirect_uri="https://example.com/callback",
            ssl_verify=True,
            jwt_secret_key="dev-secret-key-change-me",  # Default not allowed
        )
        
        errors = config.validate()
        
        assert len(errors) > 0
        assert any("JWT_SECRET_KEY" in error and "default" in error for error in errors)
    
    def test_validate_development_allows_http(self):
        """Test that development allows HTTP URLs."""
        config = EnvironmentConfig(
            environment=Environment.DEVELOPMENT,
            database_url="sqlite:///./tmp/test.db",
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
            oauth_redirect_uri="http://localhost:8000/callback",
            ssl_verify=False,
        )
        
        errors = config.validate()
        
        # Should not have HTTPS errors
        assert not any("HTTPS" in error for error in errors)
    
    def test_fail_fast_if_invalid_raises_exception(self):
        """Test that fail_fast_if_invalid raises ValueError on errors."""
        config = EnvironmentConfig(
            environment=Environment.DEVELOPMENT,
            database_url="",  # Missing
            frontend_url="",  # Missing
            backend_url="",  # Missing
            oauth_redirect_uri="",  # Missing
            ssl_verify=False,
        )
        
        with pytest.raises(ValueError) as exc_info:
            config.fail_fast_if_invalid()
        
        error_msg = str(exc_info.value)
        assert "CONFIGURATION ERROR" in error_msg or "VALIDATION FAILED" in error_msg
    
    def test_fail_fast_if_valid_does_not_raise(self):
        """Test that fail_fast_if_invalid does not raise on valid config."""
        config = EnvironmentConfig(
            environment=Environment.DEVELOPMENT,
            database_url="sqlite:///./tmp/test.db",
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
            oauth_redirect_uri="http://localhost:8000/callback",
            ssl_verify=False,
        )
        
        # Should not raise
        config.fail_fast_if_invalid()


class TestConfigHelpers:
    """Tests for configuration helper methods."""
    
    def test_is_development(self):
        """Test is_development() method."""
        config = EnvironmentConfig(
            environment=Environment.DEVELOPMENT,
            database_url="sqlite:///./tmp/test.db",
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
            oauth_redirect_uri="http://localhost:8000/callback",
            ssl_verify=False,
        )
        
        assert config.is_development() is True
        assert config.is_production() is False
        assert config.is_test() is False
    
    def test_is_production(self):
        """Test is_production() method."""
        config = EnvironmentConfig(
            environment=Environment.PRODUCTION,
            database_url="postgresql://localhost/db",
            frontend_url="https://example.com",
            backend_url="https://api.example.com",
            oauth_redirect_uri="https://example.com/callback",
            ssl_verify=True,
            jwt_secret_key="production-key",
        )
        
        assert config.is_development() is False
        assert config.is_production() is True
        assert config.is_test() is False
    
    def test_is_test(self):
        """Test is_test() method."""
        config = EnvironmentConfig(
            environment=Environment.TEST,
            database_url="sqlite:///:memory:",
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
            oauth_redirect_uri="http://localhost:8000/callback",
            ssl_verify=False,
        )
        
        assert config.is_development() is False
        assert config.is_production() is False
        assert config.is_test() is True


class TestGlobalConfig:
    """Tests for global configuration functions."""
    
    def test_get_config_returns_same_instance(self, monkeypatch):
        """Test that get_config() returns cached instance."""
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("LOCAL_DATABASE_URL", "sqlite:///./tmp/test.db")
        monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
        monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")
        monkeypatch.setenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback")
        
        # Force reload to clear cache
        config1 = reload_config()
        config2 = get_config()
        
        # Should be same instance
        assert config1 is config2
    
    def test_reload_config_creates_new_instance(self, monkeypatch, tmp_path):
        """Test that reload_config() creates new instance."""
        # Change to temp directory to avoid loading actual .env files
        monkeypatch.chdir(tmp_path)
        
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("LOCAL_DATABASE_URL", "sqlite:///./tmp/test.db")
        monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
        monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")
        monkeypatch.setenv("OAUTH_REDIRECT_URI", "http://localhost:8000/callback")
        
        config1 = reload_config()
        
        # Change environment
        monkeypatch.setenv("LOCAL_DATABASE_URL", "sqlite:///./tmp/test2.db")
        
        config2 = reload_config()
        
        # Should have different database URLs
        assert config1.database_url != config2.database_url
