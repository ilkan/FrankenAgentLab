#!/usr/bin/env python3
"""Demo script showing environment configuration usage.

This script demonstrates how to use the environment configuration module
to load and validate configuration for different environments.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from frankenagent.config.environment import (
    Environment,
    EnvironmentConfig,
    get_config,
    reload_config,
)


def demo_basic_usage():
    """Demonstrate basic configuration loading."""
    print("=" * 80)
    print("DEMO: Basic Configuration Loading")
    print("=" * 80)
    
    # Load configuration (uses ENVIRONMENT variable or defaults to development)
    config = get_config()
    
    print(f"\n✅ Configuration loaded successfully!")
    print(f"   Environment: {config.environment.value}")
    print(f"   Database URL: {config.database_url}")
    print(f"   Frontend URL: {config.frontend_url}")
    print(f"   Backend URL: {config.backend_url}")
    print(f"   SSL Verify: {config.ssl_verify}")
    print(f"   Log Level: {config.log_level}")
    print(f"   Agno Debug: {config.agno_debug}")
    
    # Check environment type
    if config.is_development():
        print(f"\n📝 Running in DEVELOPMENT mode")
        print(f"   - SSL verification is disabled")
        print(f"   - Using local developer database")
        print(f"   - Debug logging enabled")
    elif config.is_production():
        print(f"\n🚀 Running in PRODUCTION mode")
        print(f"   - SSL verification is enabled")
        print(f"   - Using Google Cloud SQL (PostgreSQL)")
        print(f"   - Production logging")
    
    print()


def demo_validation():
    """Demonstrate configuration validation."""
    print("=" * 80)
    print("DEMO: Configuration Validation")
    print("=" * 80)
    
    config = get_config()
    
    # Validate configuration
    errors = config.validate()
    
    if errors:
        print(f"\n❌ Configuration has {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
    else:
        print(f"\n✅ Configuration is valid!")
    
    print()


def demo_environment_specific_config():
    """Demonstrate environment-specific configuration."""
    print("=" * 80)
    print("DEMO: Environment-Specific Configuration")
    print("=" * 80)
    
    config = get_config()
    
    print(f"\nCurrent environment: {config.environment.value}")
    print(f"\nConfiguration details:")
    
    if config.is_development():
        print(f"   Development-specific settings:")
        print(f"   - Database: Local PostgreSQL/SQLite")
        print(f"   - URLs: localhost")
        print(f"   - SSL: Disabled (with warning)")
        print(f"   - OAuth: Development credentials")
        
        if not config.openai_api_key or config.openai_api_key.startswith("sk-your"):
            print(f"\n⚠️  Warning: OpenAI API key not configured")
            print(f"   Get your key at: https://platform.openai.com/api-keys")
        
        if not config.google_client_id or config.google_client_id.startswith("your-"):
            print(f"\n⚠️  Warning: Google OAuth not configured")
            print(f"   Configure at: https://console.cloud.google.com/apis/credentials")
    
    elif config.is_production():
        print(f"   Production-specific settings:")
        print(f"   - Database: Cloud SQL (Unix socket or private IP)")
        print(f"   - URLs: HTTPS required")
        print(f"   - SSL: Enabled (enforced)")
        print(f"   - OAuth: Production credentials")
        print(f"   - Cloud SQL Instance: {config.cloud_sql_instance or 'not configured'}")
    
    print()


def demo_fail_fast():
    """Demonstrate fail-fast validation."""
    print("=" * 80)
    print("DEMO: Fail-Fast Validation")
    print("=" * 80)
    
    print("\nAttempting to validate configuration...")
    
    try:
        config = get_config()
        config.fail_fast_if_invalid()
        print("✅ Configuration is valid - application can start")
    except ValueError as e:
        print("❌ Configuration validation failed:")
        print(str(e))
    
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Environment Configuration Demo" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        demo_basic_usage()
        demo_validation()
        demo_environment_specific_config()
        demo_fail_fast()
        
        print("=" * 80)
        print("✅ All demos completed successfully!")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
