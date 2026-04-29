#!/usr/bin/env python
"""
Telegram Setup Validation Script
Verifies that all components are correctly configured for Telegram integration
"""

import sys
import os
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")


def check_python_version():
    """Check if Python version is 3.13+"""
    print_header("1. Python Version Check")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 13:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} - Need 3.13+")
        return False


def check_env_file():
    """Check if .env file exists and has required Telegram settings"""
    print_header("2. Environment Configuration")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_error(".env file not found")
        print_info("Create .env from .env.example: cp .env.example .env")
        return False
    
    print_success(".env file found")
    
    # Check required keys
    required_keys = [
        "TELEGRAM_BOT_TOKEN",
        "MESSAGING_PLATFORM",
        "LLM_API_KEY",
    ]
    
    with open(env_path) as f:
        env_content = f.read()
    
    all_found = True
    for key in required_keys:
        if key in env_content:
            print_success(f"{key} configured")
        else:
            print_error(f"{key} missing from .env")
            all_found = False
    
    # Check values
    if "TELEGRAM_BOT_TOKEN=YOUR" in env_content:
        print_error("TELEGRAM_BOT_TOKEN not set - still has placeholder value")
        all_found = False
    elif "TELEGRAM_BOT_TOKEN=" in env_content:
        print_success("TELEGRAM_BOT_TOKEN has a value")
    
    if "MESSAGING_PLATFORM=telegram" in env_content:
        print_success("MESSAGING_PLATFORM set to 'telegram'")
    else:
        print_warning("MESSAGING_PLATFORM might not be set to 'telegram'")
    
    return all_found


def check_dependencies():
    """Check if all required Python packages are installed"""
    print_header("3. Python Dependencies")
    
    required_packages = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "SQLAlchemy"),
        ("httpx", "HTTPX"),
        ("langgraph", "LangGraph"),
        ("langchain", "LangChain"),
        ("pydantic", "Pydantic"),
    ]
    
    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print_success(f"{name} installed")
        except ImportError:
            print_error(f"{name} not installed - run: pip install -r requirements.txt")
            all_installed = False
    
    return all_installed


def check_project_structure():
    """Check if all required files exist"""
    print_header("4. Project Structure")
    
    required_files = [
        "app/services/telegram.py",
        "app/services/telegram_formatter.py",
        "app/api/endpoints/webhook.py",
        "app/config.py",
        "requirements.txt",
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} NOT FOUND")
            all_exist = False
    
    return all_exist


def check_imports():
    """Test if key modules can be imported"""
    print_header("5. Module Imports")
    
    try:
        from app.config import get_settings
        print_success("Config module imports correctly")
    except Exception as e:
        print_error(f"Config import failed: {e}")
        return False
    
    try:
        from app.services.telegram import TelegramService
        print_success("Telegram service imports correctly")
    except Exception as e:
        print_error(f"Telegram service import failed: {e}")
        return False
    
    try:
        from app.services.telegram_formatter import TelegramFormatter
        print_success("Telegram formatter imports correctly")
    except Exception as e:
        print_error(f"Telegram formatter import failed: {e}")
        return False
    
    return True


def check_telegram_token():
    """Validate Telegram bot token format"""
    print_header("6. Telegram Bot Token Validation")
    
    try:
        from app.config import get_settings
        settings = get_settings()
        
        token = settings.telegram_bot_token
        if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or token.startswith("YOUR"):
            print_error("TELEGRAM_BOT_TOKEN not set or has placeholder value")
            print_info("Get your token from @BotFather on Telegram")
            return False
        
        # Check format: should be digits:string
        parts = token.split(":")
        if len(parts) == 2 and parts[0].isdigit():
            print_success(f"Token format looks valid (ID: {parts[0]}...)")
            return True
        else:
            print_error("Token format doesn't match Telegram pattern")
            return False
    
    except Exception as e:
        print_error(f"Token validation failed: {e}")
        return False


def check_messaging_platform():
    """Verify MESSAGING_PLATFORM is set correctly"""
    print_header("7. Messaging Platform Configuration")
    
    try:
        from app.config import get_settings
        settings = get_settings()
        
        platform = settings.messaging_platform
        print_success(f"MESSAGING_PLATFORM = '{platform}'")
        
        if platform == "telegram":
            print_success("Platform correctly set to Telegram")
            return True
        else:
            print_warning(f"Platform is '{platform}' (expected 'telegram')")
            return True  # Don't fail, just warn
    
    except Exception as e:
        print_error(f"Platform check failed: {e}")
        return False


def check_webhook_endpoints():
    """Verify webhook endpoints are registered"""
    print_header("8. Webhook Endpoints Check")
    
    try:
        from app.api.endpoints import webhook
        
        # Check for required routes
        if hasattr(webhook, "router"):
            print_success("Webhook router found")
            # Try to inspect routes
            routes = [route.path for route in webhook.router.routes]
            for route in routes:
                print_success(f"Route registered: {route}")
            return True
        else:
            print_error("Webhook router not found")
            return False
    
    except Exception as e:
        print_error(f"Webhook endpoint check failed: {e}")
        return False


def main():
    """Run all checks"""
    print(f"\n{BLUE}🤖 TaskPilot Telegram Setup Validator{RESET}\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Module Imports", check_imports),
        ("Telegram Token", check_telegram_token),
        ("Messaging Platform", check_messaging_platform),
        ("Webhook Endpoints", check_webhook_endpoints),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Check failed with exception: {e}")
            results[name] = False
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {name}")
    
    print(f"\n{BLUE}Result: {passed}/{total} checks passed{RESET}\n")
    
    if passed == total:
        print_success("All checks passed! Ready to start the server.")
        print_info("Run: python run.py server")
        return 0
    else:
        print_error(f"{total - passed} checks failed. See above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
