from langgraph.graph import START,END,StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated,TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage,BaseMessage
from dotenv import load_dotenv

load_dotenv()

llm= ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.2)

class Chatstate(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]

def chat_node(state:Chatstate):
    messages=state["messages"]
    response=llm.invoke(messages)
    return {'messages':[response]}

graph = StateGraph(Chatstate)

# add nodes
graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile()
