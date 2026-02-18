from langgraph.graph import StateGraph, END
from app.nodes.read_excel_node import read_excel_node
from app.nodes.save_alerts_to_db_node import save_alerts_to_db_node
from app.nodes.classify_node import classify_node
from app.nodes.check_data_node import check_data_node

def build_graph():
    graph = StateGraph(dict)
    graph.add_node("read_excel", read_excel_node)
    graph.add_node("check_data",check_data_node)
    graph.add_node("save_to_db", save_alerts_to_db_node)
    graph.add_node("classify", classify_node)

    # graph.set_entry_point("read_excel")
    # graph.add_edge("read_excel", "check_data")
    # graph.add_conditional_edges(
    #     "check_data",
    #     lambda state: "no_data" if not state.get("alerts") else "has_data",  # check state
    #     {
    #         "no_data": END,          # end if no alerts
    #         "has_data": "save_to_db" # continue flow if alerts exist
    #     }
    # )
    #
    # graph.add_edge("save_to_db", "classify")
    graph.set_entry_point("classify")
    graph.add_edge("classify", END)
    return graph
