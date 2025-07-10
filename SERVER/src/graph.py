from typing import Optional, Literal
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, ToolMessage
from .entities.agent_state import AgentState
from src.tools import ToolKit
from langchain_openai import ChatOpenAI

load_dotenv()

llm = None
memory = None
llm_with_tools = None

class Agent:

    @staticmethod
    def load_initial_config():
        global llm, memory, llm_with_tools
        llm = ChatOpenAI(
            model="gpt-4o"
        )
        memory = MemorySaver()
        llm_with_tools = llm.bind_tools([ToolKit.search, ToolKit.get_current_date_time])

    async def model(state: AgentState) -> AgentState:
        res = await llm_with_tools.ainvoke(state["messages"])
        return {
            "messages": [res]
        }
    
    async def router(state: AgentState) -> Literal["stop", "tool_calling"]:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
            return "tool_calling"
        return "stop"


    async def tool_node(state: AgentState) -> AgentState:
        tool_calls = state["messages"][-1].tool_calls

        tool_messages = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_id = tool_call["id"]

            if tool_name == "search":
                tool_args = tool_call["args"]
                tool_res = await ToolKit.search.ainvoke(tool_args)
            elif tool_name == "get_current_date_time":
                tool_args = {} # Assuming the tool_args is a dictionary with 'format' key
                tool_res = await ToolKit.get_current_date_time.ainvoke(tool_args)

            tool_message = ToolMessage(
                content=str(tool_res),
                tool_call_id=tool_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
        
        return {
            "messages": tool_messages
        }
    
    def graph_builder():
        Agent.load_initial_config()
        graph = StateGraph(AgentState)
        graph.add_node("model", Agent.model)
        graph.add_node("tool_node", Agent.tool_node)
        graph.set_entry_point("model")
        graph.add_conditional_edges(
            "model",
            Agent.router,
            {
                "tool_calling": "tool_node",
                "stop": END
            }
        )
        graph.add_edge("tool_node", "model")
        graph_app = graph.compile(checkpointer=memory)
        return graph_app
    
    def stream_output(message: str, graph_app, config: Optional[dict] = None):
        events = graph_app.astream_events({
            "messages": [HumanMessage(content=message)]
        }, config=config, version='v2')
        return events
