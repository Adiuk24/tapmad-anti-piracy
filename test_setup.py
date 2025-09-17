#!/usr/bin/env python3
"""
Test script to verify Tapmad Anti-Piracy platform setup
Run this after setup to ensure everything is working correctly
"""

import sys
import subprocess
import requests
import time
import signal
import os
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import fastapi
        import uvicorn
        import pydantic
        import sqlalchemy
        import redis
        import yt_dlp
        import cv2
        import numpy
        print("✅ All core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_import():
    """Test that the FastAPI app can be imported"""
    print("🧪 Testing FastAPI app import...")
    
    try:
        from src.api.app import app
        print("✅ FastAPI app imported successfully")
        return True
    except Exception as e:
        print(f"❌ App import error: {e}")
        return False

def test_server_startup():
    """Test that the server can start up"""
    print("🧪 Testing server startup...")
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.api.app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ Server started and health check passed")
                success = True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                success = False
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check error: {e}")
            success = False
        
        # Kill server
        process.terminate()
        process.wait()
        
        return success
        
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("🧪 Testing environment...")
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  .env file not found (this is okay for development)")
    
    # Check if virtual environment is activated
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is activated")
    else:
        print("⚠️  Virtual environment not detected")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Tapmad Anti-Piracy Platform - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("App Import", test_app_import),
        ("Server Startup", test_server_startup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} Test:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is working correctly.")
        print("\nNext steps:")
        print("1. Run: ./start_dev.sh")
        print("2. Open: http://localhost:8000/docs")
        print("3. Start developing!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure virtual environment is activated: source venv/bin/activate")
        print("2. Reinstall dependencies: pip install -r requirements-dev.txt")
        print("3. Check Python version: python3 --version (should be 3.11+)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
