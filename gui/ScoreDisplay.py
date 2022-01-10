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
                # TODO create custom Label object!
                label = Label(text="", halign="left")
                # if y != 0:  # keep the headers centered
                #     label.bind(size=label.setter('text_size'))
                label.font_size = "18sp"
                grid.add_widget(label)
                self.labels[str((x, y))] = label
        self.labels[str((0, 0))].text = "Alternative"
        self.labels[str((1, 0))].text = "Score"

    def update(self, scores, names, criterion_name):
        self.labels[str((1, 0))].text = f"Score for {criterion_name}"
        for i, name in enumerate(names):
            self.labels[str((0, i + 1))].text = name
            self.labels[str((1, i + 1))].text = str(scores[i])[:SCORE_ACC]
