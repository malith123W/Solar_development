#!/usr/bin/env python3
"""
Electrical Data Analyzer - Startup Script
This script installs dependencies and starts the Flask application.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def start_app():
    """Start the Flask application"""
    print("Starting Electrical Data Analyzer...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the application")
    print()
    
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        print("Make sure all dependencies are installed and app.py exists.")
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user.")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

def main():
    print("⚡ Electrical Data Analyzer")
    print("=" * 40)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        print("Please make sure you're in the correct directory.")
        return
    
    # Check if app.py exists
    if not os.path.exists("app.py"):
        print("❌ app.py not found!")
        print("Please make sure you're in the correct directory.")
        return
    
    # Install requirements
    if install_requirements():
        start_app()
    else:
        print("❌ Failed to install dependencies. Please check your Python environment.")

if __name__ == "__main__":
    main()
