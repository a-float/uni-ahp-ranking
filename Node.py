class Node:
    """ parent class for AHP tree nodes """

    def __init__(self, name, parent):
        self.name = name
        self.children = []              
        self.weight = 1
        self.parent = parent
    
    def set_weight(self, x):
        self.weight = x
