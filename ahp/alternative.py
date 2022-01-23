from . import Node


class Alternative(Node):
    """ represents an alternative node - basically a name holder atm """

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def __repr__(self):
        return f"{self.name}: {round(self.weight, 3)} from {self.parent.name}"
