import time


def dissolve(dag, lifetime=60.0):
    now = time.time()
    to_remove = []
    for node_id, data in dag.graph.nodes(data=True):
        if now - data['timestamp'] > lifetime:
            to_remove.append(node_id)
    for node in to_remove:
        dag.graph.remove_node(node)
    return to_remove
