from langchain_ollama import ChatOllama
from .schema import State

llm = ChatOllama(
    model="llama3.2",  # llama3.2 supports tools/function calling
    temperature=0.2,
)

def chatbot(state: State):
    resp = llm.invoke(state["messages"])
    return {"messages": [resp]}