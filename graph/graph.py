from graph.state import State
from langgraph.graph import END, START, StateGraph
from graph.nodes import answer, quizz, plan, route
from graph.edges import task_selector

def graph():
    graph_builder = StateGraph(State)
    graph_builder.add_node("router", route)
    graph_builder.add_node("planner", plan)
    graph_builder.add_node("generate_quiz", quizz)
    graph_builder.add_node("Q&A", answer)
    #graph_builder.add_node("Evaluate", evaluate_answer)

    graph_builder.add_edge(START, "router")
    graph_builder.add_conditional_edges("router", task_selector)