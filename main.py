import os
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import asyncio

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static frontend files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


# Import the LangGraph components from your core folder
from core.tools import list_pods, get_pod_details, get_pod_logs, list_deployments
from core.agent import agent_node, tool_node, agent_executor
from core.state import AgentState

# Define the LangGraph workflow
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tool", tool_node)

# Add conditional edges
graph.add_edge(START, "agent")
graph.add_edge("tool", "agent")

def route_next_step(state: AgentState):
    """
    Routes the workflow based on whether a tool call is needed.
    """
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        # If there are no tool calls, the agent's response is the final answer
        return END
    else:
        # If tool calls are present, execute the tool node next
        return "tool"

graph.add_conditional_edges(
    "agent",
    route_next_step,
    {"tool": "tool", END: END}
)

# Compile the graph
full_graph = graph.compile()


@app.post("/chat")
async def chat_with_assistant(question: str):
    """
    Endpoint to receive a user's natural language query and return a response.
    """
    try:
        inputs = {"input": question, "chat_history": []}
        
        # Invoke the LangGraph agent to process the query
        response = await full_graph.ainvoke(inputs)
        
        # LangGraph returns a final state, extract the last message content
        final_response = response.get("messages", [])[-1].content
        
        return {"response": final_response}
    except Exception as e:
        # Catch and handle errors during graph execution
        print(f"Error during graph execution: {e}")
        return {"response": f"An error occurred: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
