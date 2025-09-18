import os
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage
from typing import Annotated
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import tool

from core.state import AgentState
from core.tools import list_pods, get_pod_details, get_pod_logs, list_deployments

# Get the AWS region from environment variables
aws_region = os.getenv("AWS_REGION", "us-east-1")

# The Bedrock model used by the agent
llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs={"temperature": 0.0},
    region_name=aws_region
)

# List of all available read-only tools
tools = [list_pods, get_pod_details, get_pod_logs, list_deployments]

# This is the prompt template that guides the LLM
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful Kubernetes assistant. Your task is to answer questions about the state of a Kubernetes cluster in natural language."
            "You have access to the following tools to get information:"
            "{tools}"
            "You are a read-only assistant and are strictly forbidden from performing any destructive actions like deleting resources. "
            "If a user asks you to perform a destructive action, you must decline and explain that you can only perform read-only operations."
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Create the agent by binding the tools to the LLM
# This is the modern and correct way to use tool calling in LangChain
agent = llm.bind_tools(tools)

# Define the nodes for the graph
def agent_node(state: AgentState):
    """
    This node represents the agent's thought process.
    It takes the state (conversation history) and decides what to do next.
    """
    return agent.invoke(state)

def tool_node(state: AgentState):
    """
    This node executes the tool calls identified by the agent.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the last message contains tool calls, execute them
    if not last_message.tool_calls:
        raise ValueError("No tool calls found in the last message.")
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.name
        tool_args = tool_call.args
        
        # Look up the tool by name and execute it
        found_tool = next((t for t in tools if t.name == tool_name), None)
        if found_tool:
            result = found_tool.invoke(tool_args)
            # You might want to handle the output here
            print(f"Tool {tool_name} executed with result: {result}")
        else:
            print(f"Tool {tool_name} not found.")

    return state