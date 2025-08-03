#!/usr/bin/env python3
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/test")
def test():
    return {"message": "Test server working"}

if __name__ == "__main__":
    print("Starting test server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)