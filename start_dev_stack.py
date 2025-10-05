#!/usr/bin/env python3
"""
Development stack startup script
Starts both backend API server and frontend development server
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

def print_banner():
    print("=" * 80)
    print("🚀 AI Media Platform - Development Stack")
    print("=" * 80)
    print("Starting backend API server and frontend development server...")
    print()

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check if frontend directory exists
    frontend_dir = Path("frontend-v2")
    if not frontend_dir.exists():
        print("❌ Frontend directory 'frontend-v2' not found")
        return False
    
    # Check if package.json exists
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json not found in frontend-v2")
        return False
    
    print("✅ All dependencies found (using existing virtual environment)")
    print()
    return True

def start_backend():
    """Start the backend API server"""
    print("🔧 Starting backend API server...")
    
    # Use current Python (should be in virtual environment)
    python_cmd = sys.executable
    print("✅ Using current Python environment")
    
    try:
        backend_process = subprocess.Popen(
            [python_cmd, "backend_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        if backend_process.poll() is None:
            print("✅ Backend API server started on http://localhost:8000")
            print("📚 API docs available at http://localhost:8000/docs")
        else:
            print("❌ Backend server failed to start")
            return None
            
        return backend_process
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the frontend development server"""
    print("🎨 Starting frontend development server...")
    
    frontend_dir = Path("frontend-v2")
    
    try:
        # Check if node_modules exists, if not run npm install
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            install_process = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            if install_process.returncode != 0:
                print("❌ Failed to install frontend dependencies")
                print(install_process.stderr)
                return None
            
            print("✅ Frontend dependencies installed")
        
        # Start the development server
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Wait for the server to start
        time.sleep(3)
        
        if frontend_process.poll() is None:
            print("✅ Frontend development server started on http://localhost:5173")
        else:
            print("❌ Frontend server failed to start")
            return None
            
        return frontend_process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def monitor_process(process, name):
    """Monitor a process and print its output"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{name}] {line.strip()}")
    except Exception:
        pass

def main():
    print_banner()
    
    if not check_dependencies():
        print("❌ Dependency check failed. Please install missing dependencies.")
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend
        backend_process = start_backend()
        if backend_process:
            processes.append(("Backend", backend_process))
            
            # Start monitoring backend output in a separate thread
            backend_thread = threading.Thread(
                target=monitor_process, 
                args=(backend_process, "Backend"),
                daemon=True
            )
            backend_thread.start()
        else:
            print("❌ Failed to start backend server")
            sys.exit(1)
        
        # Wait a moment before starting frontend
        time.sleep(2)
        
        # Start frontend
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(("Frontend", frontend_process))
            
            # Start monitoring frontend output in a separate thread
            frontend_thread = threading.Thread(
                target=monitor_process, 
                args=(frontend_process, "Frontend"),
                daemon=True
            )
            frontend_thread.start()
        else:
            print("❌ Failed to start frontend server")
            # Kill backend if frontend fails
            if backend_process:
                backend_process.terminate()
            sys.exit(1)
        
        print()
        print("=" * 80)
        print("🎉 Development stack is running!")
        print("=" * 80)
        print("🔧 Backend API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("🎨 Frontend: http://localhost:5173")
        print()
        print("💡 Login credentials for testing:")
        print("   Email: dev@example.com")
        print("   Password: password")
        print()
        print("Press Ctrl+C to stop all servers")
        print("=" * 80)
        print()
        
        # Wait for processes to finish or be interrupted
        try:
            while True:
                # Check if any process has died
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"❌ {name} process has stopped unexpectedly")
                        raise KeyboardInterrupt
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down development stack...")
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down development stack...")
    
    finally:
        # Clean up processes
        for name, process in processes:
            if process.poll() is None:
                print(f"🔄 Stopping {name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                    print(f"✅ {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  Force killing {name}...")
                    process.kill()
                    process.wait()
                    print(f"✅ {name} force stopped")
        
        print("👋 Development stack stopped")

if __name__ == "__main__":
    main()