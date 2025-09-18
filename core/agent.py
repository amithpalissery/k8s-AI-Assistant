import os
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage, ToolMessage
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
            """You are a Kubernetes assistant.

- If the user asks to list pods, namespaces, or deployments:
  - Return only their names in plain text (one per line).
- If the user asks for logs:
  - Return only a short summary of the logs, not the full content.
- If the user asks for something you do not have a tool for:
  - Reply that you cannot perform that action instead of retrying.
Do not add explanations or summaries unless explicitly requested."""
        ),
        ("placeholder", "{messages}"),
    ]
)

# Create the agent by binding the tools to the LLM
agent = prompt | llm.bind_tools(tools)

# Define the nodes for the graph
def agent_node(state: AgentState):
    """
    This node represents the agent's thought process.
    It takes the state (conversation history) and decides what to do next.
    """
    # Extract messages from state and pass to the agent
    messages = state["messages"]
    result = agent.invoke({"messages": messages})
    return {"messages": [result]}


def tool_node(state: AgentState):
    """
    This node executes the tool calls identified by the agent.
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If the last message contains tool calls, execute them
    if not last_message.tool_calls:
        raise ValueError("No tool calls found in the last message.")

    # Create a list of tool messages to add to the state
    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        # Find the tool by name
        found_tool = None
        for t in tools:
            if t.name == tool_name:
                found_tool = t
                break

        if found_tool:
            try:
                # Execute the tool and create a ToolMessage
                result = found_tool.invoke(tool_args)
                tool_message = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_id
                )
                tool_messages.append(tool_message)
                print(f"Tool {tool_name} executed with result: {result}")
            except Exception as e:
                error_message = ToolMessage(
                    content=f"Error executing tool {tool_name}: {str(e)}",
                    tool_call_id=tool_id
                )
                tool_messages.append(error_message)
                print(f"Error executing tool {tool_name}: {e}")
        else:
            error_message = ToolMessage(
                content=f"Tool {tool_name} not found.",
                tool_call_id=tool_id
            )
            tool_messages.append(error_message)
            print(f"Tool {tool_name} not found.")

    # Return the tool messages to be added to the state
    return {"messages": tool_messages}
