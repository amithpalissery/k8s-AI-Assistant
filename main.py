import os
import asyncio
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from flask_cors import CORS
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Set up Flask app
app = Flask(__name__)

# CORS middleware for frontend communication
CORS(app)

# Define the request body format
class ChatRequest(BaseModel):
    question: str

# Import the LangGraph components from your core folder
from core.tools import list_pods, get_pod_details, get_pod_logs, list_deployments
from core.agent import agent_node, tool_node
from core.state import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

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

# Serve the static frontend files
@app.route("/")
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory('frontend', path)

@app.route("/chat", methods=["POST"])
def chat_with_assistant():
    """
    Endpoint to receive a user's natural language query and return a response.
    """
    try:
        data = request.get_json()
        question = data.get("question")
        
        # Validate input
        if not question:
            return jsonify({"response": "No question provided"}), 400
        
        print(f"DEBUG: Received question: {question}")
        print(f"DEBUG: Question type: {type(question)}")
        
        # The LangGraph ainvoke method expects a dictionary with messages and chat_history
        inputs = {
            "messages": [HumanMessage(content=question)], 
            "chat_history": []
        }
        
        print(f"DEBUG: Inputs to graph: {inputs}")
        
        # Invoke the LangGraph agent to process the query
        response = asyncio.run(full_graph.ainvoke(inputs))
        
        print(f"DEBUG: Graph response: {response}")
        
        # LangGraph returns a final state, extract the last message content
        final_response = response.get("messages", [])[-1].content
        
        return jsonify({"response": final_response})
    except Exception as e:
        # Catch and handle errors during graph execution
        print(f"Error during graph execution: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"response": f"An error occurred: {str(e)}"})

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)