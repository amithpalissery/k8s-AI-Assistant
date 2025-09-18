import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import asyncio
import time

# Load environment variables
load_dotenv()

# Set up FastAPI app
app = FastAPI(
    title="Kubernetes AI Assistant",
    description="A read-only AI assistant for Kubernetes clusters.",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For testing the frontend, let's create a simple mock endpoint.
@app.post("/chat")
async def chat_with_assistant(question: str):
    """
    A temporary endpoint to simulate the backend response for frontend testing.
    """
    await asyncio.sleep(1) # Simulate a delay to show the "loading" state
    
    # You can customize these mock responses
    if "pod" in question.lower():
        response = "Mock response: The pods are all running."
    elif "node" in question.lower():
        response = "Mock response: There are 5 nodes in the cluster."
    else:
        response = f"Mock response: I received your query: '{question}'."

    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)