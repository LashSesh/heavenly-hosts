

class Storage:
    def __init__(self):
        self.data = {}

    def add(self, node_id, cell):
        self.data[node_id] = cell

    def get_all(self):
        return self.data


storage = Storage()
