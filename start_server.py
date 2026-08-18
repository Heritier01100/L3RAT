#!/usr/bin/env python3
"""
Android Remote Control Tool - Server Launcher
"""

import os
import sys
import subprocess
import time
import webbrowser
import threading

def main():
    print("="*60)
    print("📱 Android Remote Control Tool a tool made by Heritier01100 ")
    print("="*60)
    print("Starting server...\n")
    
    # Determine Python command
    python_cmd = 'python3'
    try:
        subprocess.run([python_cmd, '--version'], capture_output=True, check=True)
    except:
        python_cmd = 'python'
    
    print(f"✅ Using Python: {python_cmd}")
    
    # Check if server directory exists
    if not os.path.exists('server/app.py'):
        print("❌ Error: server/app.py not found")
        print("Please make sure you're in the correct directory")
        sys.exit(1)
    
    # Install requirements
    print("\n📦 Installing required packages...")
    try:
        subprocess.run([python_cmd, '-m', 'pip', 'install', '-q', '-r', 'server/requirements.txt'], check=True)
        print("✅ Packages installed successfully /n For educational purposes only. Illegal use wont affect the owner")
    except subprocess.CalledProcessError:
        print("⚠️ Failed to install packages automatically")
        print("Please run manually:")
        print(f"  {python_cmd} -m pip install -r server/requirements.txt")
    
    # Change to server directory
    os.chdir('server')
    
    # Open browser after delay
    def open_browser():
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("\n🚀 Starting server at http://localhost:5000")
    print("🔐 Credentials will appear in the terminal")
    print("="*60 + "\n")
    
    try:
        subprocess.run([python_cmd, 'app.py'])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
