def check_data_node(state):
    # Here we just return state unchanged
    print(f"Alerts found: {len(state.get('alerts', []))}")
    return state
