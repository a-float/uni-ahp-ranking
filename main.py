import sys
import xml.etree.ElementTree as ET
import numpy as np


class AHP:
    def __init__(self, filename):
        try:
            root = ET.parse(filename).getroot()
        except (FileNotFoundError, ET.ParseError) as e:
            raise ValueError("Exception while creating AHP object:" + str(e))
        self.alternatives = []
        self.root_criterion = Criterion(root.find('./criterion'), root)
        for alt_node in root.find('alternatives'):
            self.alternatives.append(alt_node.get('name'))

    def get_all_scores(self):
        return self.get_scores_for(list(range(len(self.alternatives))))

    def get_scores_for(self, indices):
        scores = self.root_criterion.get_scores_for(indices)
        return {self.alternatives[i]: scores[i] for i in indices}

    def find_criterion(self, name):
        return self.root_criterion.find_criterion(name)

    def __repr__(self):
        res = f"AHP object {self.__str__()} />"
        return res

    def __str__(self):
        return "Criteria:\n" + self.root_criterion.recursive_repr() + '\n' + f'Alternatives = {self.alternatives}'


def calculate_weights(matrix):
    eigenvalues, eigenvector = map(np.real, np.linalg.eig(matrix))
    max_index = np.argmax(eigenvalues)
    weights = eigenvector[:, max_index]
    return weights / np.sum(weights)


class Node:
    def __init__(self, node):
        self.name = node.get('name')
        self.children = []
        self.weight = 1


class Alternative(Node):
    def __init__(self, node, parent_criterion):
        super().__init__(node)
        self.criterion = parent_criterion

    def __repr__(self):
        return f"{self.name}: {round(self.weight, 3)} from {self.criterion.name}"


class Criterion(Node):
    def __init__(self, node, root, ):
        super().__init__(node)
        self.is_final_criterion = False
        for cat_node in node:
            self.children.append(Criterion(cat_node, root))
        if not self.children:
            self.is_final_criterion = True
            for alt_node in root.find('alternatives'):
                self.children.append(Alternative(alt_node, self))

        matrix = self.load_matrix(root)  # the decision matrix
        if matrix is not None:
            self.matrix = matrix
        else:
            self.reset_matrix()
        self.set_weights()

    def __repr__(self):
        return f"{self.name}: {'?' if self.matrix is None else '✓'} {round(self.weight, 3)}"

    def recursive_repr(self, depth=0):
        res = self.__repr__() + '\n'
        if self.children and not self.is_final_criterion:
            criteria = list(map(lambda x: x.recursive_repr(depth + 1), self.children))
            sep = '---' * (depth + 1) + '> '
            res += sep + sep.join(criteria)
        return res

    def set_weights(self):
        weights = calculate_weights(self.matrix)
        for i, w in enumerate(weights):
            self.children[i].weight = w

    def get_scores_for(self, indices, with_names=False):
        if self.is_final_criterion:
            res = np.array([alt.weight for alt in self.children])[indices]
        else:
            res = np.zeros(len(indices))
            for criterion in self.children:
                scores = criterion.get_scores_for(indices)
                res += scores
        res *= self.weight
        return res

    def get_all_scores(self):
        return self.get_scores_for(list(range(len(self.children))))

    def reset_matrix(self):
        self.matrix = np.ones((len(self.children),) * 2)

    def input_matrix(self):
        child_count = len(self.children)
        for i in range(0, child_count):
            for j in range(i + 1, child_count):
                print(i, j)
                msg = f"How do you compare {self.children[i].name} to {self.children[j].name} with respect to {self.name}?"
                msg += f"\n(Previously {self.matrix[i][j]})\n> "
                while True:
                    try:
                        value = float(input(msg))
                        self.matrix[i][j] = value
                        self.matrix[j][i] = 1 / value
                        assert -9 < value < 9, "Number out of range"
                        break
                    except (AssertionError, ValueError) as e:
                        print("Invalid input: " + str(e))
        self.set_weights()
        print(f"Weights for criterion {self.name} has been set")

    def load_matrix(self, root):
        matrix_node = root.find(f'.//matrix[@for="{self.name}"]')
        if matrix_node is None:
            return None
        y, x = list(map(int, [matrix_node.get('height'), matrix_node.get('width')]))
        matrix = np.ones((y, x), dtype=np.float64)
        for value in matrix_node:
            x, y = list(map(int, [value.get('x'), value.get('y')]))
            val = float(value.text)
            val = -(1 / val) if val < 0 else val
            matrix[y, x] = val
            matrix[x, y] = 1 / val
        print(f"# Loaded matrix for {self.name}")
        return matrix

    def find_criterion(self, name):
        if self.name == name:
            return self
        if not self.children or self.is_final_criterion:
            return None
        else:
            results = ([node.find_criterion(name) for node in self.children])
            return next((item for item in results if item is not None), None)


def main():
    # ahp = AHP('data_cars.xml')
    # print(ahp)
    # print('Ranking:')
    # print(ahp.get_scores_for([0, 1]))
    # print(ahp.get_all_scores())
    # print(ahp.find_criterion('Cost'))
    ahp = None
    done = False
    selected_criterion = None
    while not done:
        comm = None
        while not comm:
            comm = input('>').split()
        if comm[0] == 'load':
            try:
                ahp = AHP(comm[1])
                selected_criterion = ahp.root_criterion
            except ValueError as e:
                print(str(e))
        elif comm[0] == 'select':
            selected_criterion = ahp.find_criterion(comm[1])
            print(f"Selected criterion is {selected_criterion}")
        elif comm[0] == 'scores':
            try:
                if comm[1] == 'all':
                    res = selected_criterion.get_all_scores()
                else:
                    res = selected_criterion.get_scores_for(list(map(int, comm[1:])))
            except Exception as e:
                print("Expected 'score [all | alternatives' indices]")
            print(res)
        elif comm[0] == 'show':
            print(f"AHP: {ahp}")
            print(f"Selected criterion: {selected_criterion}")
        elif comm[0] == 'reset-matrix':
            if selected_criterion:
                selected_criterion.reset_matrix()
            else:
                print("No criterion selected")
        elif comm[0] == 'change-matrix':
            if selected_criterion:
                selected_criterion.input_matrix()
            else:
                print("No criterion selected")
        elif comm[0] == 'show-matrix':
            if selected_criterion:
                print(selected_criterion.matrix)
            else:
                print("No criterion selected")
        elif comm[0] == 'exit' or comm[0] == 'q':
            done = True
        elif comm[0] == 'help':
            help_msg = ["load [filename] - creates a new AHP object from xml file and selects it's root",
                        'show - displays current AHP status and the selected criterion',
                        'select [criterion name] - select criterion with specified name or None if it doesn\'t exist',
                        'score [all|alternatives\' indices] - display chosen alternatives\' scores at selected criterion',
                        'change-matrix - manually change matrix values at the selected criterion',
                        'show-matrix - display selected criterion\'s matrix',
                        'reset-matrix - set selected criterion\'s matrix to an identity matrix']
            print("\n".join(help_msg))
        else:
            print("Unknown command")


if __name__ == '__main__':
    main()
