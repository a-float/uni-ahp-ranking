from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

SCORE_ACC = 6


class ScoreDisplay(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = None
        self.labels = {}

    def setup(self, rows):
        grid = self.ids['table']
        for old_label in self.labels.values():
            grid.remove_widget(old_label)
        for y in range(rows + 1):  # one header row
            for x in range(2):
                label = Label(text="", halign="left")
                # if y != 0:  # keep the headers centered
                #     label.bind(size=label.setter('text_size'))
                label.font_size = "17sp" if y != 0 else "19sp"
                grid.add_widget(label)
                self.labels[str((x, y))] = label
        self.labels[str((0, 0))].text = "Alternative"
        self.labels[str((1, 0))].text = "Score"

    def update(self, scores, names, criterion_name):
        if len(names) > len(self.labels) // 2 - 1: # an alternative must have been added
            current = len(self.labels) // 2 - 1
            toAdd = len(names) - current
            for y in range(current+1, current+ 1 + toAdd):
                for x in range(2):
                    label = Label(text="", halign="left")
                    label.font_size = "18sp"
                    self.ids['table'].add_widget(label)
                    self.labels[str((x, y))] = label

        self.labels[str((1, 0))].text = f"Score for {criterion_name}"
        print(names)
        for i, name in enumerate(names):
            self.labels[str((0, i + 1))].text = name
            self.labels[str((1, i + 1))].text = str(scores[i])[:SCORE_ACC]
        # clear the additional labels (left after removal of alternatives)
        for y in range(len(names)+1, len(self.labels) // 2):
            self.labels[str((0, y))].text = ''
            self.labels[str((1, y))].text = ''
