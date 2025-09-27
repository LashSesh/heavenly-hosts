
def fragment_message(msg: str, size: int):
    return [msg[i:i + size] for i in range(0, len(msg), size)]


def transmit_fragments(dag, fragments):
    recipients = {}
    for idx, frag in enumerate(fragments):
        frag_recipients = []
        for node_id, data in dag.graph.nodes(data=True):
            score = data['cell'].resonance(data['cell'].vector)
            if score > 0.7:
                frag_recipients.append(node_id)
        recipients[f"frag_{idx}"] = frag_recipients
    return recipients
