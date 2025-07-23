#!/usr/bin/env python3
"""
TalentScout AI Hiring Assistant - Automated Runner
This script automatically sets up and runs the hiring assistant application.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_streamlit():
    """Check if Streamlit is properly installed"""
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
        return True
    except ImportError:
        print("❌ Streamlit not found")
        return False

def run_application():
    """Run the Streamlit application"""
    print("🚀 Starting TalentScout AI Hiring Assistant...")
    print("📱 The application will open in your default browser")
    print("🔗 URL: http://localhost:8501")
    print("\n" + "="*50)
    print("🎯 TALENTSCOUT AI HIRING ASSISTANT")
    print("="*50)
    print("Ready to screen candidates!")
    print("Press Ctrl+C to stop the application")
    print("="*50 + "\n")
    
    try:
        # Run streamlit with the app
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "false"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

def main():
    """Main execution function"""
    print("🎯 TalentScout AI Hiring Assistant - Setup & Run")
    print("=" * 50)
    
    # Check current directory
    if not Path("app.py").exists():
        print("❌ app.py not found in current directory")
        print("Please run this script from the project root directory")
        return
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Check Streamlit installation
    if not check_streamlit():
        return
    
    # Run the application
    run_application()

if __name__ == "__main__":
    main()
