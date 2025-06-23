from graph.state import State
from langgraph.graph import END, START, StateGraph
from graph.nodes import answer, quizz, plan, router, eval
from graph.edges import task_selector
from langgraph.checkpoint.postgres import PostgresSaver
from settings import settings
from psycopg import Connection

postgres_url = f"postgresql://postgres:{settings.password}@localhost:{settings.port}/{settings.dbname}?sslmode=disable"

def graph():

    conn = Connection.connect(postgres_url, autocommit=True)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()

    graph_builder = StateGraph(State)
    graph_builder.add_node("router", router)
    graph_builder.add_node("task_selector", task_selector)
    graph_builder.add_node("planner", plan)
    graph_builder.add_node("generate_quizz", quizz)
    graph_builder.add_node("Q&A", answer)
    graph_builder.add_node("evaluate", eval)

    graph_builder.add_edge(START, "router")
    graph_builder.add_conditional_edges("router", task_selector)
    graph_builder.add_edge("task_selector", "planner")
    graph_builder.add_edge("planner", "generate_quizz")
    graph_builder.add_edge("generate_quizz", "evaluate")
    #graph_builder.add_edge("Q&A", "router")
    graph_builder.add_edge("Q&A", END)
    graph_builder.add_edge("evaluate", END)

    return graph_builder.compile(checkpointer=checkpointer)