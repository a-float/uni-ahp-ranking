class Node:
    """ parent class for AHP tree nodes """

    def __init__(self, node):           # node to słownik ???
        self.name = node.get('name')    # .get("key") -> value
        self.children = []              
        self.weight = 1
    
    def set_weight(self, x):
        self.weight = x
