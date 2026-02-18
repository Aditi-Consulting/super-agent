import pandas as pd

def read_excel_node(state):
    df = pd.read_excel("data/sample_it_tickets.xlsx")
    state["alerts"] = df.to_dict(orient="records")
    # print(state["alerts"])
    return state
