#!/usr/bin/env python3
"""Simple test server to check if it's a general Python/FastAPI issue"""

from fastapi import FastAPI
import uvicorn
import time
import signal
import sys
import os

print("Starting simple test server...")

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Test server is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

def signal_handler(sig, frame):
    print(f"\nReceived signal: {sig}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print(f"PID: {os.getpid()}")
    print("Starting on http://127.0.0.1:8001")
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8001)
    except Exception as e:
        print(f"Error: {e}")