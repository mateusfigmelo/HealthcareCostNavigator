#!/usr/bin/env python3
"""Simple test runner for Healthcare Cost Navigator."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))


async def test_basic_functionality():
    """Test basic application functionality."""
    print("🧪 Testing Healthcare Cost Navigator MVP...")

    try:
        # Test imports
        print("✓ Testing imports...")
        from app.config import settings
        from app.main import app

        print("✓ All imports successful")

        # Test configuration
        print("✓ Testing configuration...")
        assert hasattr(settings, "database_url"), "Database URL not configured"
        assert hasattr(settings, "openai_api_key"), "OpenAI API key not configured"
        print("✓ Configuration valid")

        # Test FastAPI app
        print("✓ Testing FastAPI app...")
        assert app.title == "Healthcare Cost Navigator", "App title mismatch"
        print("✓ FastAPI app configured correctly")

        print("\n🎉 All basic tests passed!")
        print("\nNext steps:")
        print("1. Set your OPENAI_API_KEY environment variable")
        print("2. Download sample_prices_ny.csv to the project root")
        print("3. Run: docker compose up --build")
        print("4. Access the API at: http://localhost:8000/docs")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: poetry install")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1)
