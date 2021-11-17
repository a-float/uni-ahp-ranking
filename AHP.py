import xml.etree.ElementTree as ET
import numpy as np


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

    # not necessary rn
    # def get_all_scores(self):
    #     return self.root_criterion.get_all_scores()
    #
    # def get_scores_for(self, indices):
    #     return self.root_criterion.get_scores_for(indices)

    def save_decisions(self, filename):
        self.root_criterion.save_decision_matrix(self.tree.find('data'))
        ET.indent(self.tree, space="\t", level=0)
        self.tree.write(filename)

    def find_criterion(self, name):
        return self.root_criterion.find_criterion(name)

    def __repr__(self):
        res = f"AHP object {self.__str__()} />"
        return res

    def __str__(self):
        return "Criteria:\n" + self.root_criterion.recursive_repr() + '\n' + f'Alternatives = {self.alternatives}'


def calculate_weights(matrix):
    """ finds the orthogonal vector of the decision matrix with maximum length """
    eigenvalues, eigenvector = map(np.real, np.linalg.eig(matrix))
    max_index = np.argmax(eigenvalues)
    weights = eigenvector[:, max_index]
    return weights / np.sum(weights)


class Node:
    """ parent class for AHP tree nodes """

    def __init__(self, node):
        self.name = node.get('name')
        self.children = []
        self.weight = 1


class Alternative(Node):
    """ represents an alternative node - basically a name holder atm """

    def __init__(self, node, parent_criterion):
        super().__init__(node)
        self.criterion = parent_criterion

    def __repr__(self):
        return f"{self.name}: {round(self.weight, 3)} from {self.criterion.name}"


class Criterion(Node):
    """ represents a criterion node. Manages weights for its children using the decision matrix """

    def __init__(self, node, root, ):
        super().__init__(node)
        self.is_final_criterion = False  # True if it's children all are Alternatives
        self.has_custom_matrix = False  # True if the matrix is specified by the user, False if autogenerated (np.ones)
        for cat_node in node:
            self.children.append(Criterion(cat_node, root))
        if not self.children:
            self.is_final_criterion = True
            for alt_node in root.find('alternatives'):
                self.children.append(Alternative(alt_node, self))

        # try to load the matrix. If not specified, create a default one
        loaded_matrix = self.load_matrix(root)
        if loaded_matrix is not None:
            self.matrix = loaded_matrix
            self.has_custom_matrix = True
        else:
            self.reset_matrix()
        # set the children weights
        self.update_weights()

    def __repr__(self):
        return f"{self.name}: {'✓' if self.has_custom_matrix else '?'} {round(self.weight, 3)}"

    def recursive_repr(self, depth=0):
        """ used for printing the AHP tree status """
        res = self.__repr__() + '\n'
        if self.children and not self.is_final_criterion:
            criteria = list(map(lambda x: x.recursive_repr(depth + 1), self.children))
            sep = '---' * (depth + 1) + '> '
            res += sep + sep.join(criteria)
        return res

    def update_weights(self):
        weights = calculate_weights(self.matrix)
        for i, w in enumerate(weights):
            self.children[i].weight = w

    def get_all_scores(self):
        # get the alternative count, needed for the range
        node = self
        while not node.is_final_criterion:
            node = node.children[0]
        alt_count = len(node.children)
        # run the actual calculations
        return self.get_scores_for(list(range(alt_count)))

    def get_scores_for(self, indices):
        """ performs the AHP scores calculation with respect to the self criterion """
        names = None
        if self.is_final_criterion:
            res = np.array([alt.weight for alt in self.children])[indices]
            names = [child.name for i, child in enumerate(self.children) if i in indices]
            return res, names
        else:
            res = np.zeros(len(indices))
            for criterion in self.children:
                scores, names = criterion.get_scores_for(indices)
                res += scores * criterion.weight
        return res, names

    def reset_matrix(self):
        self.matrix = np.ones((len(self.children),) * 2)
        self.has_custom_matrix = False
        self.update_weights()

    def input_matrix(self):
        """ reads the new decision matrix values from the user via the command line """
        child_count = len(self.children)
        for i in range(0, child_count):
            for j in range(i + 1, child_count):
                msg = f"How do you compare {self.children[i].name} to {self.children[j].name} with respect to {self.name}?"
                msg += f"\n(Previously {self.matrix[i][j]})\n> "
                while True:
                    try:
                        value = float(input(msg))
                        assert 0 < abs(value) <= 9, "Number out of range [-9, 0) u (0, 9]"
                        if value < 0:
                            value = (1 / -value)
                        self.matrix[i][j] = value
                        self.matrix[j][i] = 1 / value
                        break
                    except (AssertionError, ValueError) as e:
                        print("Invalid input: " + str(e))
        self.has_custom_matrix = True
        self.update_weights()
        print(f"Weights for criterion {self.name} has been set")

    def load_matrix(self, root):
        """ returns a matrix for the criterion name read from the xml file, returns None if the matrix doesn't exist """
        matrix_node = root.find(f'.//matrix[@for="{self.name}"]')
        if matrix_node is None:
            return None
        y, x = list(map(int, [matrix_node.get('height'), matrix_node.get('width')]))
        if x != y or x != len(self.children):
            print(f"Invalid matrix size for {self.name}")
            return None
        matrix = np.ones((y, x), dtype=np.float64)
        for value in matrix_node:
            x, y = list(map(int, [value.get('x'), value.get('y')]))
            val = float(value.text)
            val = -(1 / val) if val < 0 else val
            if x < 0 or x > len(self.children) or y < 0 or y > len(self.children):
                print(f"Invalid attributes for value: <value x='{x}' y='{y}'>{value.text}</value> in matrix for {self.name}")
                return None
            matrix[y, x] = val
            matrix[x, y] = 1 / val
        print(f"# Loaded matrix for {self.name}")
        return matrix

    def find_criterion(self, name):
        """ recursively searches for the criterion with the specified name among it's children """
        if self.name == name:
            return self
        if not self.children or self.is_final_criterion:
            return None
        else:
            results = ([node.find_criterion(name) for node in self.children])
            return next((item for item in results if item is not None), None)

    def create_matrix_node_at(self, node):
        """ creates a matrix node in the specified node of the etree with the decision matrix data """
        new_matrix = ET.SubElement(node, 'matrix')
        new_matrix.set('for', self.name)
        x, y = self.matrix.shape
        new_matrix.set('width', str(x))
        new_matrix.set('height', str(y))
        for i in range(0, y - 1):
            for j in range(i + 1, x):
                value = ET.SubElement(new_matrix, 'value')
                value.set('x', str(j))
                value.set('y', str(i))
                value.text = str(self.matrix[i, j])

    def save_decision_matrix(self, data_node):
        """
        updates the etree matrix node for this criterion. Removes the current one and creates one with the
        current matrix data instead if self.has_custom_node == True
        """
        matrix = data_node.find(f"./matrix[@for='{self.name}']")
        if matrix:
            data_node.remove(matrix)
        if self.has_custom_matrix:
            self.create_matrix_node_at(data_node)
            if not self.is_final_criterion:
                for child in self.children:
                    child.save_decision_matrix(data_node)
