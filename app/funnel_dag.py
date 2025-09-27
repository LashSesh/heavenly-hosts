import networkx as nx
import numpy as np
from app.cell import GabrielCell


class FunnelDAG:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_cell(self, cell: GabrielCell, timestamp: float, semantic_tag: str):
        node_id = f"N{len(self.graph.nodes)}"
        self.graph.add_node(
            node_id,
            cell=cell,
            timestamp=timestamp,
            semantic=semantic_tag,
        )
        for prev in self.graph.nodes:
            if prev != node_id:
                weight = cell.resonance(self.graph.nodes[prev]["cell"].vector)
                if weight > 0.5:
                    self.graph.add_edge(prev, node_id, weight=weight)
        return node_id

    def query(self, signal_vector, threshold: float):
        incoming = np.array(signal_vector)
        results = []
        for node_id, data in self.graph.nodes(data=True):
            score = data["cell"].resonance(incoming)
            if score >= threshold:
                results.append({
                    "node": node_id,
                    "semantic": data["semantic"],
                    "score": score,
                })
        return sorted(results, key=lambda x: -x["score"])
