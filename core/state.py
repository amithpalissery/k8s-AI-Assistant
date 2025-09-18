from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Represents the state of our agent's conversation.
    It contains a list of all messages exchanged.
    """
    messages: Annotated[List[BaseMessage], add_messages]