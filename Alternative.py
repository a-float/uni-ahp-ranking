from Node import Node

class Alternative(Node):
    """ represents an alternative node - basically a name holder atm """

    def __init__(self, node, parent_criterion):
        super().__init__(node)
        self.criterion = parent_criterion

    def __repr__(self):
        return f"{self.name}: {round(self.weight, 3)} from {self.criterion.name}"

