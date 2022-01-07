import xml.etree.ElementTree as ET
from Criterion import Criterion


class AHP:
    """ acts as an interface for interacting with the AHP tree """

    def __init__(self, filename):
        try:
            self.tree = ET.parse(filename)
            root = self.tree.getroot()
        except (FileNotFoundError, ET.ParseError) as e:
            raise ValueError("Exception while creating AHP object:" + str(e))
        self.alternatives = []
        # the actual root of the tree
        self.root_criterion = Criterion(root.find('./criterion'), root)
        for alt_node in root.find('alternatives'):
            self.alternatives.append(alt_node.get('name'))

    def save_decisions(self, filename):
        self.root_criterion.save_decision_matrices(self.tree.find('data'))
        ET.indent(self.tree, space="\t", level=0)
        self.tree.write(filename)

    def find_criterion(self, name):
        return self.root_criterion.find_criterion(name)

    def __repr__(self):
        res = f"AHP object {self.__str__()} />"
        return res

    def __str__(self):
        return "Criteria:\n" + self.root_criterion.recursive_repr() + '\n' + f'Alternatives = {self.alternatives}'
