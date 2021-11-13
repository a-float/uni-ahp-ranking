import xml.etree.ElementTree as ET
import numpy as np


class AHP:
    def __init__(self, root):
        self.alternatives = []
        self.root_criterion = Criterion(root.find('./criterion'), root)
        for alt_node in root.find('alternatives'):
            self.alternatives.append(alt_node.get('name'))

    def set_default_weights(self):
        self.root_criterion.set_default_weights()

    def get_scores_for(self, indices):
        scores = self.root_criterion.get_scores_for(indices)
        return {self.alternatives[i]: scores[i] for i in indices}

    def __repr__(self):
        res = ["<AHP object",
               f'Criteria = {list(map(lambda x: repr(x), self.root_criterion.sub_criteria))}',
               f'Alternatives = {self.alternatives}/>']
        return '\n'.join(res)


def calculate_weights(matrix):
    eigenvalues, eigenvector = map(np.real, np.linalg.eig(matrix))
    max_index = np.argmax(eigenvalues)
    weights = eigenvector[:, max_index]
    return weights / np.sum(weights)


class Criterion:
    def __init__(self, criterion_node, root):
        self.name = criterion_node.get('name')
        self.sub_criteria = []
        self.weight = 1
        self.decision_weights = None
        for cat_node in criterion_node:
            self.sub_criteria.append(Criterion(cat_node, root))
        self.decision_matrix = self.load_matrix(root)
        weights = calculate_weights(self.decision_matrix)
        if self.sub_criteria:
            # decision matrix defines criteria importance
            for i, w in enumerate(weights):
                self.sub_criteria[i].weight = w
        else:
            # decision matrix defines alternative's score
            self.decision_weights = weights

    def __repr__(self):
        return self.name + ':' + str(self.weight)

    def get_scores_for(self, indices):
        if not self.sub_criteria:
            res = self.decision_weights[indices]
        else:
            res = np.zeros(len(indices))
            for criterion in self.sub_criteria:
                scores = criterion.get_scores_for(indices)
                # print(self.name + f' adding {criterion.name}: ' + str(scores) + ' ' + str(sum(scores)))
                res += scores
        # print(self.name + " " + str(res) + ' ' + str(sum(res)))
        return res * self.weight

    def set_default_weights(self):
        for sub_crit in self.sub_criteria:
            sub_crit.weight = 1 / len(self.sub_criteria)
            sub_crit.set_default_weights()

    def load_matrix(self, root):
        matrix_node = root.find(f'.//matrix[@for="{self.name}"]')
        y, x = list(map(int, [matrix_node.get('height'), matrix_node.get('width')]))
        matrix = np.ones((y, x), dtype=np.float64)
        for value in matrix_node:
            x, y = list(map(int, [value.get('x'), value.get('y')]))
            val = float(value.text)
            val = -(1 / val) if val < 0 else val
            matrix[y, x] = val
            matrix[x, y] = 1 / val
        return matrix


def main():
    root = ET.parse('data.xml').getroot()
    # print(load_matrix(root, 'Age'))
    ahp = AHP(root)
    print(ahp)
    print('Ranking is: ')
    print(ahp.get_scores_for([0, 1, 2]))


if __name__ == '__main__':
    main()
