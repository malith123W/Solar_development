#!/usr/bin/env python3
"""
Electrical Data Analyzer - Backend API Server
This script starts the Flask API backend server.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing backend dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Backend dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def start_backend():
    """Start the Flask API backend"""
    print("Starting Electrical Data Analyzer Backend API...")
    print("Backend API will be available at: http://localhost:5000")
    print("API Documentation: http://localhost:5000/api/health")
    print("Press Ctrl+C to stop the backend server")
    print()
    
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        print("Make sure all dependencies are installed and app.py exists.")
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped by user.")
    except Exception as e:
        print(f"❌ Error starting backend server: {e}")

def main():
    print("⚡ Electrical Data Analyzer - Backend API")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        print("Please make sure you're in the backend directory.")
        return
    
    # Check if app.py exists
    if not os.path.exists("app.py"):
        print("❌ app.py not found!")
        print("Please make sure you're in the backend directory.")
        return
    
    # Install requirements
    if install_requirements():
        start_backend()
    else:
        print("❌ Failed to install dependencies. Please check your Python environment.")

if __name__ == "__main__":
    main()
