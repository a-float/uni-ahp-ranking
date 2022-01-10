from numpy.core.fromnumeric import size
from Node import Node
from Alternative import Alternative
import xml.etree.ElementTree as ET
import numpy as np
import math
import logging

EVM = "EVM"
GMM = "GMM"
SCI = "SCI"
GW = "GW"
SH = "SH"
calc_weight_methods = [EVM, GMM]
ic_complete_methods = [SCI, GW]
ic_incomplete_methods = [SH]
log = logging.getLogger('mylogger')


class Criterion(Node):
    """ Represents a criterion node. Manages weights for its children using the decision matrix """

    def __init__(self, node, root):
        """node is the xml criterion node for this node, root is the root of the xml tree"""
        super().__init__(node)
        self.is_final_criterion = False  # True if it's children all are Alternatives
        self.calc_weight_method = EVM
        self.has_custom_matrix = False
        for cat_node in node:
            self.children.append(Criterion(cat_node, root))
        if not self.children:
            self.is_final_criterion = True
            for alt_node in root.find('alternatives'):
                self.children.append(Alternative(alt_node, self))

        self.matrix = np.ones((len(self.children),) * 2)  # the aggregated matrix
        self.matrices_completion = []  # ith element is True if ith matrix is complete, otherwise its 0
        self.matrices = []
        self.is_aggregated = True

        # try to load all matrices for this criterion if there are none, add one filled with ones
        self.load_all_matrices(root)
        if self.matrices:
            self.has_custom_matrix = True  # successfully loaded at least one matrix

        # set the children weights
        self._update_weights()
        log.info(f"Created criterion {self.name}")

    def is_complete(self):
        """returns true if at all the sub matrices are complete and false otherwise """
        return 0 not in self.matrices_completion

    def __repr__(self):
        return f"{self.name}: {'✓' if self.has_custom_matrix else '?'} | {'complete' if self.is_complete() else 'incomplete'} | {'weight = ' + '%.3f' % self.weight}"

    def recursive_repr(self, depth=0):
        """ used for printing the AHP tree status """
        res = self.__repr__() + '\n'
        if self.children and not self.is_final_criterion:
            criteria = list(map(lambda x: x.recursive_repr(depth + 1), self.children))
            sep = '---' * (depth + 1) + '> '
            res += sep + sep.join(criteria)
        return res

    def _update_weights(self):
        weights = self.calculate_weights(self.matrix, self.is_complete)
        for i, w in enumerate(weights):
            self.children[i].set_weight(w)

    def get_all_scores(self):
        node = self
        while not node.is_final_criterion:
            node = node.children[0]
        alt_count = len(node.children)  # get the alternative count, needed for the range
        # run the actual calculations
        return self.get_scores_for(list(range(alt_count)))

    def get_scores_for(self, indices):
        if not self.is_aggregated:
            self.aggregate()
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

    def set_matrix(self, idx, new_matrix, is_complete):
        assert idx in range(len(self.matrices_completion)), "Invalid index"
        self.matrices[idx] = new_matrix
        self.matrices_completion[idx] = is_complete
        # always aggregate after setting is_aggregated to False
        # a bit slower, but the aggregated matrix is always updated
        # mainly ull for the GUI
        log.info(f"Matrix {idx + 1} set")
        self.is_aggregated = False
        self.aggregate()

    def reset_matrix(self, idx):
        self.matrices[idx] = np.ones(self.matrices[idx].shape)
        self.is_aggregated = False
        self.aggregate()
        log.info(f"# Matrix {idx} reset")

    def remove_matrix(self, idx):
        try:
            del self.matrices_completion[idx]
            del self.matrices[idx]
            self.is_aggregated = False
            self.aggregate()
        except Exception as e:
            print(e)
            log.error("Invalid remove_matrix index")

    def _input_matrix(self):
        """ reads the new decision matrix values from the user via the command line """
        new_matrix = np.ones((len(self.children),) * 2)
        child_count = len(self.children)
        is_matrix_complete = True
        for i in range(0, child_count):
            for j in range(i + 1, child_count):
                msg = f"How do you compare {self.children[i].name} to {self.children[j].name} with respect to {self.name}?"
                while True:
                    try:
                        raw_value = input(msg)
                        value = float(raw_value)
                        assert 0 <= abs(value) <= 9, "Number out of range [-9, 9]"
                        if 0 < abs(value) <= 9:
                            if value == 0:
                                is_matrix_complete = False
                                new_matrix[i][j] = value
                                new_matrix[j][i] = value
                            else:
                                if value < 0:
                                    value = (1 / -value)
                                new_matrix[i][j] = value
                                new_matrix[j][i] = 1 / value
                            break

                    except (AssertionError, ValueError) as e:
                        print("Invalid input: " + str(e))
        return new_matrix, is_matrix_complete

    def add_matrix(self, new_matrix, complete):
        """Add the given matrix to the matrices list. Assumes the matrix does not contain negative values"""
        if new_matrix.shape != self.matrix.shape:
            pretty_matrix = str(new_matrix).replace('[', '').replace(']', '')
            log.error(f"Matrix:\n{pretty_matrix}\nis of invalid shape. Skipping")
            return
        self.matrices.append(new_matrix)
        self.matrices_completion.append(complete)
        self.is_aggregated = False
        self.aggregate()
        log.info(f"# Added matrix for {self.name}")

    # Aggregated matrix is the geometric average of all sub matrices
    def aggregate(self):
        log.debug("# Aggregating")
        self.matrix = np.ones(self.matrix.shape)
        if self.matrices:
            for sub_matrix in self.matrices:
                self.matrix *= sub_matrix
            r = len(self.matrices)
            self.matrix **= (1 / r)
        self.is_aggregated = True
        self._update_weights()

    def load_all_matrices(self, root):
        nodes = root.findall(f".//matrix[@for='{self.name}']")
        for node in nodes:
            self.add_matrix(*self.load_matrix(node))

    def load_matrix(self, matrix_node):
        """Reads the matrix data from matrix xml node while validating its attributes"""
        is_matrix_complete = True
        if matrix_node is None:
            return None
        y, x = list(map(int, [matrix_node.get('height'), matrix_node.get('width')]))
        if x != y or x != len(self.children):
            log.error(f"Invalid matrix size for {self.name}")
            return None
        matrix = np.zeros((y, x), dtype=np.float64)
        np.fill_diagonal(matrix, 1)
        for value in matrix_node:
            x, y = list(map(int, [value.get('x'), value.get('y')]))
            val = value.text
            # check if the value is valid
            try:
                val = float(value.text)
            except ValueError:
                log.error(
                    f"Invalid value at: <value x='{x}' y='{y}'>{value.text}</value> in matrix for {self.name}")
                return None, None
            # check if the x and y attributes are valid
            if x < 0 or x > len(self.children) or y < 0 or y > len(self.children):
                log.error(
                    f"Invalid attributes for value: <value x='{x}' y='{y}'>{value.text}</value> in matrix for {self.name}")
                return None, None
            # transform value into positive inverse if it's negative
            val = (1 / -val) if val < 0 else val
            if val == 0:
                matrix[y, x] = 0
                matrix[x, y] = 0
                is_matrix_complete = False
            else:
                matrix[x, y] = 1 / val
                matrix[y, x] = val
        return matrix, is_matrix_complete

    def find_criterion(self, name):
        """ recursively searches for the criterion with the specified name among it's children """
        if self.name == name:
            return self
        if not self.children or self.is_final_criterion:
            return None
        else:
            results = ([node.find_criterion(name) for node in self.children])
            return next((item for item in results if item is not None), None)

    def create_matrix_node_at(self, node, matrix):
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
                value.text = str(matrix[i, j])

    def _save_decision_matrices(self, data_node):
        """
        Updates the etree matrix node for this criterion. Removes the current one and creates one with the
        current matrix data instead if self.has_custom_node == True
        """
        old_matrices = data_node.findall(f"./matrix[@for='{self.name}']")
        for matrix in old_matrices:
            data_node.remove(matrix)
        for matrix in self.matrices:
            self.create_matrix_node_at(data_node, matrix)
        if not self.is_final_criterion:
            for child in self.children:
                child._save_decision_matrices(data_node)

    def ic(self, method):
        """Calculates the inconsistency and it's ratio using the specified method"""
        if not self.is_aggregated:
            self.aggregate()
        # inconsistency + consistency ratio
        RI = {3: 0.546, 4: 0.83, 5: 1.08, 6: 1.26, 7: 1.33, 8: 1.41, 9: 1.45, 10: 1.47, 11: 1.51, 12: 1.54, 13: 1.55,
              14: 1.57, 15: 1.58, 16: 1.69, 17: 1.61, 18: 1.61, 19: 1.62, 20: 1.63}

        """są dwie metody dla macierzy kompletnych i jedna dla niekompletnych"""
        CI = None
        if self.is_complete():
            log.debug("# Calculating inconsistency for a complete matrix")
            # method = input("METHOD = [SCI or GW] ")
            if method == SCI:
                # Saaty's consistency index
                eigenvalues, eigenvector = map(np.real, np.linalg.eig(self.matrix))
                lambda_max = np.amax(eigenvalues)
                n = len(self.matrix)
                CI = (lambda_max - n) / (n - 1)
                # log.info("Inconsistency = " + str(CI))
            elif method == GW:
                # Golden Wang index
                n = len(self.matrix)
                _C = np.zeros((n, n), dtype=np.float64)
                sm = 0
                for i in range(n):
                    for j in range(n):
                        for k in range(n):
                            sm += self.matrix[k][j]
                        _C[i][j] = self.matrix[i][j] / sm
                # 6.15 126
                wgm = np.zeros(n, dtype=np.float64)
                for i in range(n):
                    licz = self.wgmu(i, n)
                    mian = 0
                    for j in range(n):
                        mian += self.wgmu(j, n)
                    wgm[i] = licz / mian
                CI = 0
                smm = 0
                for i in range(n):
                    for j in range(n):
                        smm += abs(_C[i][j] - wgm[i])
                CI = 1 / n * smm
                # log.info("Inconsistency = " + str(CI))
        else:
            log.debug("# Calculating inconsistency for an incomplete matrix")
            log.debug("# Using the Saaty-Harker method")
            method = "SH"
            if method == "SH":
                # Saaty-Harker
                # 151
                n = len(self.matrix)
                x = n
                y = n
                B = np.ones((x, y), dtype=np.float64)
                s = np.ones((x, 1), dtype=np.float64)
                for i in range(0, x):
                    for j in range(0, y):
                        if self.matrix[i][j] == 0:
                            s[i] += 1
                for i in range(0, x):
                    for j in range(0, y):
                        if self.matrix[i][j] == 0 and i != j:
                            B[i][j] = 0
                        if self.matrix[i][j] != 0 and i != j:
                            B[i][j] = self.matrix[i][j]
                        if i == j:
                            B[i][j] = s[i]
                eigenvalues, eigenvector = map(np.real, np.linalg.eig(B))
                max_arg = np.amax(eigenvalues)
                CI = max_arg - n / (n - 1)
                # log.info("Inconsistency = " + str(CI))

        if CI is not None and 3 <= n <= 20:
            # log.info("Consistency Ratio = " + str(CI / RI.get(n)))
            return CI, CI / RI.get(n)
        else:
            log.error("Invalid parameters. CI is None or n < 3 and n > 20")
            return None, None

    def wgmu(self, i, n):
        res = 1
        for j in range(n):
            res *= self.matrix[i][j]
        res = res ** (1 / n)
        return res

    def calculate_weights(self, matrix, is_complete):
        method = self.calc_weight_method
        assert method in calc_weight_methods, "Invalid method for calculating weight"
        if is_complete:
            if method == EVM:
                """ finds the orthogonal vector of the decision matrix with maximum length """
                eigenvalues, eigenvector = map(np.real, np.linalg.eig(matrix))
                max_index = np.argmax(eigenvalues)
                weights = eigenvector[:, max_index]
                return weights / np.sum(weights)
            elif method == GMM:
                x, y = matrix.shape
                wgmu = np.ones((x,), dtype=np.float64)
                for i in range(0, x):
                    for k in range(0, x):
                        wgmu[i] *= matrix[i][k]
                    wgmu[i] = math.pow(wgmu[i], 1 / x)
                wgm = np.zeros((x,), dtype=np.float64)
                for i in range(0, x):
                    suma = 0
                    for j in range(0, x):
                        suma += wgmu[j]
                    wgm[i] = wgmu[i] / suma
                return wgm
        else:
            # while method != EVM and method != GMM:
            # method = input("INCOMPLETE MATRIX: choose weight calculation method (EVM/GMM) ")
            x, y = matrix.shape
            B = np.ones((x, y), dtype=np.float64)
            s = np.ones((x, 1), dtype=np.float64)
            for i in range(0, x):
                for j in range(0, y):
                    if matrix[i][j] == 0:
                        s[i] += 1

            if method == EVM:
                for i in range(0, x):
                    for j in range(0, y):
                        if matrix[i][j] == 0 and i != j:
                            B[i][j] = 0
                        if matrix[i][j] != 0 and i != j:
                            B[i][j] = matrix[i][j]
                        if i == j:
                            B[i][j] = s[i]  # no need to add 1, because we initialized vector with ones ;)
                # B*wmax = lambdamax*wmax
                eigenvalues, eigenvector = map(np.real, np.linalg.eig(B))
                max_index = np.argmax(eigenvalues)
                weights = eigenvector[:, max_index]
                return weights / np.sum(weights)
            elif method == GMM:
                for i in range(0, x):
                    for j in range(0, y):
                        if matrix[i][j] == 0 and i != j:
                            B[i][j] = 1
                        if matrix[i][j] != 0 and i != j:
                            B[i][j] = 0
                        if i == j:
                            B[i][j] = x - s[i] + 1  # because we initialized with zeroes
                r = np.zeros((x, 1), dtype=np.float64)
                for i in range(0, x):
                    for j in range(0, y):
                        if matrix[i][j] != 0:
                            r[i] = math.log(matrix[i][j])
                B_inv = np.linalg.inv(B)
                w_log = B_inv.dot(r)
                w = np.zeros((x, 1), dtype=np.float64)
                w_scaled = np.zeros((x, 1), dtype=np.float64)

                for i in range(0, size(w)):
                    w[i] = math.exp(w_log[i])

                for i in range(0, size(w)):
                    suma = 0
                    for j in range(0, size(w)):
                        suma += w[j]
                    w_scaled[i] = w[i] / suma
                res = np.zeros(size(w))
                for i in range(0, size(w)):
                    res[i] = w_scaled[i]
                return res

    def set_all_calc_weight_method(self, new_method):
        self.calc_weight_method = new_method
        self._update_weights()
        if not self.is_final_criterion:
            for crit in self.children:
                crit.set_all_calc_weight_method(new_method)
