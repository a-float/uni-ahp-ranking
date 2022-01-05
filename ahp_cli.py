from tabulate import tabulate
from AHP import AHP
from Criterion import Criterion


def on_help(comm):
    help_msg = [["load [filename]", "creates a new AHP object from xml file and selects it's root"],
                ["show", "displays current AHP status and the selected criterion"],
                ["select [criterion name]", "select criterion with specified name or None if it doesn't exist"],
                ["scores ['all' | indices] sort?", "display chosen alternatives' scores at selected criterion"],
                ["change-matrix", "manually change matrix values at the selected criterion"],
                ["show-matrix", "display selected criterion's matrix"],
                ["reset-matrix", "set selected criterion's matrix to an identity matrix"],
                ["save [filename]", "save the model with decision weights to the specified file"],
                ["ic", "calculate inconsistancy"],
                ["load-additional [filename]", "loads additional matrix from other expert"],
                ["select-multiple [criterion name1] [criterion name2] ...", "multiple level criteria selection"],
                ["exit", "quit the program"]]
    print(tabulate(help_msg, headers=["Command", "Description"], tablefmt='simple'))


EVM = "EVM"
GMM = "GMM"

class CLI:
    """ handles the manin input loop, parses and executes commands """

    def __init__(self):
        self.ahp = None
        self.selected_criterion = None
        self.selected_multiple_criterion = []
        self.done = False
        self.doesnt_need_ahp = ['help', 'exit', 'load']
        self.actions = {
            'load': self.on_load,
            'show': self.on_show,
            'select': self.on_select,
            'scores': self.on_scores,
            'change-matrix': self.on_change_matrix,
            'show-matrix': self.on_show_matrix,
            'reset-matrix': self.on_reset_matrix,
            'save': self.on_save,
            'ic':self.on_ic,
            'load-additional':self.load_additional,
            'select-multiple':self.select_multiple,
            'help': on_help,
        }

    def select_multiple(self, comm):
        assert len(comm) > 2, "No filenames specified"
        n = len(comm)
        for i in range(1, n):
            name = comm[i]   # UWAGA <= kryterium musi byc jednoczlonowe
            print(name)
            self.selected_multiple_criterion.append(self.ahp.find_criterion(name))
            print(f"Selected criterion: {self.selected_multiple_criterion[i-1]}")

    def load_additional(self, comm):
        assert len(comm) == 2, "No filename specified"
        self.selected_criterion.load_additional(comm[1])

    def on_ic(self, comm):
        assert len(comm) == 1, "No need for extra arguments"
        self.selected_criterion.ic()

    def on_load(self, comm):
        assert len(comm) == 2, "No filename specified"
        self.ahp = AHP(comm[1])
        self.selected_criterion = self.ahp.root_criterion

    def on_show(self, comm):
        assert len(comm) == 1, "No arguments required"
        print(f"AHP: {self.ahp}")
        print(f"Selected criterion: {self.selected_criterion}")

    def on_select(self, comm):
        assert len(comm) > 1, "No criterion name specified"
        name = ' '.join(comm[1:])   # bierze elementy listy i łaczy je za pomocą spaji 
        print(name)
        self.selected_criterion = self.ahp.find_criterion(name)
        print(f"Selected criterion: {self.selected_criterion}")

    def on_scores(self, comm):
        try:
            assert len(comm) > 1, "No option specified"
            if comm[1] == 'all':
                scores, names = self.selected_criterion.get_all_scores()
            elif comm[1] == 'multiple':
                if self.selected_multiple_criterion == []:
                    print("no multiple criteria selected")
                    return
                else:
                    scores_tab = []
                    for cirterion in self.selected_multiple_criterion:
                        scores, names = cirterion.get_all_scores()
                        scores_tab.append(scores)
                    res = [0] * len(scores_tab[0])
                    for i in range(0, len(scores_tab[0])):
                        sm = 0
                        for j in range(0, len(scores_tab)):
                            sm += scores_tab[j][i]
                        res[i] = sm/len(scores_tab)
                    scores = res
            else:
                indices = list(map(int, comm[1:]))
                scores, names = self.selected_criterion.get_scores_for(indices)
            res = zip(names, scores)
            if len(comm) > 2 and comm[2] == 'sort':
                res = sorted(res, reverse=True, key=lambda x: x[1])
            print('\n'.join([f"{item[0]}: {round(item[1], 3)}" for item in res]))
        except IndexError as e:
            raise ValueError("Expected 'score [all | indices | multiple] " + str(e))

    def on_change_matrix(self, comm):
        assert len(comm) == 1, "No arguments required"
        if self.selected_criterion:
            self.selected_criterion.input_matrix()
        else:
            print("No criterion selected")

    def on_show_matrix(self, comm):
        assert len(comm) == 1, "No arguments required"
        if self.selected_criterion:
            name_labels = list(map(lambda x: x.name, self.selected_criterion.children))
            matrix = self.selected_criterion.matrix
            rows = [[name_labels[i]] + list(matrix[i]) for i in range(len(name_labels))]
            print(tabulate(rows, headers=name_labels, tablefmt='simple'))
        else:
            print("No criterion selected")

    def on_reset_matrix(self, comm):
        assert len(comm) == 1, "No arguments required"
        if self.selected_criterion:
            self.selected_criterion.reset_matrix()
            print("Matrix has been reset")
        else:
            print("No criterion selected")

    def on_save(self, comm):
        assert len(comm) == 2, "no filename specified"
        self.ahp.save_decisions(comm[1])
        print("Decisions saved successfully to " + comm[1])

    def loop(self):
        while not self.done:
            comm = None
            while not comm:
                comm = input('>').split()
            if comm[0] in self.actions.keys():
                if self.ahp is None and comm[0] not in self.doesnt_need_ahp:
                    print("No ahp loaded. Use load command first.")
                    continue
                try:
                    self.actions[comm[0]](comm)
                except (AssertionError, ValueError) as e:
                    print(str(e))
            elif comm[0] == 'exit':
                self.done = True
            else:
                print("Unknown command")


