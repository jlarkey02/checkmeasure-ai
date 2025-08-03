#!/usr/bin/env python3
"""Minimal backend to test if basic FastAPI works"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Minimal Test Backend")

@app.get("/")
def root():
    return {"message": "Minimal backend is working"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting minimal backend on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)