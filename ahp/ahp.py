import xml.etree.ElementTree as ET
from . import Criterion


class AHP:
    """Acts as an interface for interacting with the AHP tree """

    def __init__(self, filename):
        try:
            self.tree = ET.parse(filename)
            root = self.tree.getroot()
        except (FileNotFoundError, ET.ParseError) as e:
            raise ValueError("Exception while creating AHP object:" + str(e))
        self.filename = filename
        self.alternatives = []  # alist of alternatives' names
        # the actual root of the tree
        self.root_criterion = Criterion(root.find('./criterion'), root, None)  # root criterion has no parent
        for alt_node in root.find('alternatives'):
            self.alternatives.append(alt_node.get('name'))

    def save_to_file(self, filename):
        self.root_criterion._save_decision_matrices(self.tree.find('data'))
        ET.indent(self.tree, space="\t", level=0)
        with open(filename, 'wb') as f:
            self.tree.write(f)

    def set_all_calc_weight_method(self, new_method):
        self.root_criterion.set_all_calc_weight_method(new_method)

    def find_criterion(self, name):
        return self.root_criterion.find_criterion(name)

    def add_alternative(self, alt_name):
        alternatives_node = self.tree.find('alternatives')
        new_node = ET.SubElement(alternatives_node, 'alternative')
        new_node.set('name', alt_name)
        self.alternatives.append(alt_name)
        self.root_criterion.add_alternative(alt_name)
        return True

    def remove_alternative(self, name):
        alternatives_node = self.tree.find('alternatives')
        for node in alternatives_node:
            if node.get('name') == name:
                self.alternatives.remove(name)
                alternatives_node.remove(node)
                self.root_criterion.remove_alternative(name)
                return True
        else:
            return False

    def __repr__(self):
        res = f"AHP object {self.__str__()} />"
        return res

    def __str__(self):
        return "Criteria:\n" + self.root_criterion.recursive_repr() + '\n' + f'Alternatives = {self.alternatives}'
