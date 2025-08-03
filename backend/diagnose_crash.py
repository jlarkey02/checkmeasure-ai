#!/usr/bin/env python3
"""Diagnose backend crash issue"""

import sys
import os
import time
import subprocess
import signal
import threading

def monitor_process(pid):
    """Monitor a process and report when it dies"""
    print(f"Monitoring process {pid}...")
    while True:
        try:
            # Check if process exists
            os.kill(pid, 0)
            time.sleep(0.1)
        except ProcessLookupError:
            print(f"\n[MONITOR] Process {pid} has died!")
            # Try to get exit status
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                if str(pid) not in result.stdout:
                    print("[MONITOR] Process no longer in process list")
            except:
                pass
            break

def start_backend():
    """Start the backend with monitoring"""
    print("Starting backend with monitoring...")
    
    # Start uvicorn in subprocess
    cmd = [
        sys.executable, '-m', 'uvicorn', 'main:app',
        '--host', '127.0.0.1',
        '--port', '8000',
        '--timeout-keep-alive', '0',
        '--timeout-graceful-shutdown', '0',
        '--workers', '1',
        '--loop', 'asyncio',
        '--log-level', 'info'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor_process, args=(proc.pid,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Read output
    try:
        for line in proc.stdout:
            print(line.rstrip())
            if "Uvicorn running on" in line:
                print("\n[DIAGNOSE] Backend started successfully, waiting 5 seconds...")
                time.sleep(5)
                
                # Test if it's still alive
                print("[DIAGNOSE] Testing if backend is accessible...")
                try:
                    import requests
                    response = requests.get('http://localhost:8000/health', timeout=2)
                    print(f"[DIAGNOSE] Health check response: {response.status_code}")
                except Exception as e:
                    print(f"[DIAGNOSE] Health check failed: {e}")
                
                # Check process
                if proc.poll() is None:
                    print("[DIAGNOSE] Process is still running")
                else:
                    print(f"[DIAGNOSE] Process died with exit code: {proc.poll()}")
                    
    except KeyboardInterrupt:
        print("\n[DIAGNOSE] Interrupted by user")
    finally:
        if proc.poll() is None:
            print("[DIAGNOSE] Terminating backend...")
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    start_backend()