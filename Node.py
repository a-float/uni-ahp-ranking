class Node:
    """ parent class for AHP tree nodes """

    def __init__(self, node):           
        self.name = node.get('name')
        self.children = []              
        self.weight = 1
    
    def set_weight(self, x):
        self.weight = x
