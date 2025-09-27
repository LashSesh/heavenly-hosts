import matplotlib.pyplot as plt
import networkx as nx


def plot_dag(dag, filename="dag.png"):
    plt.figure(figsize=(6, 6))
    pos = nx.spring_layout(dag.graph)
    nx.draw(dag.graph, pos, with_labels=True, node_size=500, node_color="skyblue")
    plt.savefig(filename)
    return filename
