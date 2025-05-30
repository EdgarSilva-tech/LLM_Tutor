from graph.state import State
from langgraph.graph import END, START, StateGraph
from graph.edges import task_selector


def graph():
    graph_builder = StateGraph(State)
    graph_builder.add_node()