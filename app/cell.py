import numpy as np


class GabrielCell:
    def __init__(self, signal_vector):
        self.vector = np.array(signal_vector)

    def resonance(self, incoming_vector):
        v1 = self.vector / (np.linalg.norm(self.vector) + 1e-8)
        v2 = incoming_vector / (np.linalg.norm(incoming_vector) + 1e-8)
        return float(np.dot(v1, v2))
