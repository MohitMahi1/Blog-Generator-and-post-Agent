from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from langgraph.types import Send
from app.graph.state import State
from app.graph.nodes.router import router_node, route_next
from app.graph.nodes.research import research_node
from app.graph.nodes.orchestrator import orchestrator_node
from app.graph.nodes.worker import worker_node
from app.graph.nodes.reducer import merge_content, decide_images, generate_and_place_images

"""
    Here we build our graph and it's node and it's edges or connections.
"""

# fanout() -: It divide the worker as per the section
def fanout(state : State):
    assert state["plan"] is not None
    return [
        Send(
            
            "worker",
            {
                "task": task.model_dump(),
                "topic": state["topic"],
                "mode": state["mode"],
                "as_of": state["as_of"],
                "recency_days": state["recency_days"],
                "plan": state["plan"].model_dump(),
                "evidence": [e.model_dump() for e in state.get("evidence", [])],
            }
        )
        for task in state["plan"].tasks
    ]
    
def build_graph():
    
    # Reducer subgraph
    reducer_graph = StateGraph(State)
    
    # Reducer subgraph nodes
    reducer_graph.add_node("merge_content", merge_content)
    reducer_graph.add_node("decide_images", decide_images)
    reducer_graph.add_node("generate_and_place_images", generate_and_place_images)
    
    # Reducer subgraph edges or connections
    reducer_graph.add_edge(START, "merge_content")
    reducer_graph.add_edge("merge_content", "decide_images")
    reducer_graph.add_edge("decide_images", "generate_and_place_images")
    reducer_graph.add_edge("generate_and_place_images", END)
    
    # Reducer subgraph compile
    reducer_subgraph = reducer_graph.compile()
    
    
    # MAIN GRAPH or MAIN WORKFLOW
    g = StateGraph(State)
    
    # main graph nodes
    g.add_node("router", router_node)
    g.add_node("research", research_node)
    g.add_node("orchestrator", orchestrator_node)
    g.add_node("worker", worker_node)
    g.add_node("reducer", reducer_subgraph)
    
    # main graph edges
    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router",
        route_next,
        {
            "research": "research", 
            "orchestrator": "orchestrator"
        }
    )
    g.add_edge("research", "orchestrator")
    g.add_conditional_edges(
        "orchestrator",
        fanout,
        ["worker"]
    )
    g.add_edge("worker", "reducer")
    g.add_edge("reducer", END)
    
    # main graph compilation
    return g.compile()

# call
app_graph = build_graph()