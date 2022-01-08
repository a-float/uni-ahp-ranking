from typing import Optional
import numpy as np
from kivy.config import Config

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '600')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.write()

import kivy
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from CLI import CLI
from Node import Node
from kivy.clock import Clock
from gui.MatrixEditor import MatrixInput, MatrixEditor
import logging

kivy.require('2.0.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewLabel

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty

log = logging.getLogger('mylogger')

MAX_OUTPUT_HEIGHT = 20
SCORE_ACC = 6


class CriterionSelect(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tv = TreeView(root_options=dict(text='Criteria'),
                           hide_root=True)
        self.add_widget(self.tv)
        self.cli = None
        self.on_select_criterion = None

    def setup(self, **kwargs):
        self.cli = kwargs['cli']
        self.on_select_criterion = kwargs['on_select_criterion']

    def update(self):  # TODO tree view reload and update
        if self.cli.ahp:
            for node in [i for i in self.tv.iterate_all_nodes()]:
                self.tv.remove_node(node)
            CriterionSelect.populate_tree_view(self.tv, None, self.cli.ahp.root_criterion)

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        for node in self.tv.iterate_open_nodes():
            if node.collide_point(*touch.pos):
                self.on_select_criterion(node.text)

    @staticmethod
    def populate_tree_view(tree_view, parent, node: Node):
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=node.name,
                                                         is_open=True))
        else:
            tree_node = tree_view.add_node(TreeViewLabel(text=node.name,
                                                         is_open=True), parent)

        for child_node in node.children:
            if child_node.children:  # do not create views for alternatives
                CriterionSelect.populate_tree_view(tree_view, tree_node, child_node)


class MatricesDisplay(TabbedPanel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cli = None

    def setup(self, **kwargs):
        self.cli = kwargs['cli']

    def update(self):  # TODO optimize update cache matrix editors?
        if self.cli.ahp:
            prev_tab_name = self.current_tab._label.text
            selected = self.cli.selected_criterion
            self.clear_tabs()
            panel_items = []
            aggr_panel = TabbedPanelItem(text="A")
            aggr_panel.add_widget(MatrixEditor(idx=-1, children=selected.children, matrix=selected.matrix))
            panel_items.append(aggr_panel)
            for i, matrix in enumerate(self.cli.selected_criterion.matrices):
                panel = TabbedPanelItem(text=f"{i + 1}")
                panel.add_widget(MatrixEditor(idx=i, children=selected.children, matrix=selected.matrices[i]))
                panel_items.append(panel)
            for panel in panel_items:
                self.add_widget(panel)
            # if possible, switch back to the previous tab
            tab_names = list(map(lambda x: x._label.text, self.tab_list))
            if prev_tab_name in tab_names:
                self.switch_to(self.tab_list[tab_names.index(prev_tab_name)])
            else:
                self._switch_to_first_tab()


class MyButton(Button):
    pass


class OutputView(ScrollView):
    def __init__(self, **kwargs):
        text = kwargs.pop('text', '')
        super().__init__(**kwargs)
        self.set_text(text)

    def set_text(self, new_text):
        self.ids['label'].text = new_text


class ChooseFilePopup(Popup):
    pass


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
                label.font_size = "20sp"
                grid.add_widget(label)
                self.labels[str((x, y))] = label
        self.labels[str((0, 0))].text = "Alternative"
        self.labels[str((1, 0))].text = "Score"

    def update(self, scores, names, criterion_name):
        self.labels[str((1, 0))].text = f"Score for {criterion_name}"
        for i, name in enumerate(names):
            self.labels[str((0, i + 1))].text = name
            self.labels[str((1, i + 1))].text = str(scores[i])[:SCORE_ACC]


class ControlPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score_display = None
        self.popup = None
        self.output = None
        self.cli: Optional[CLI] = None
        self.on_change_ahp = None
        self.on_change_criterion = None
        self.matrices_display = None

        self.logs = []
        log.setLevel(logging.INFO)
        log.addFilter(self.update_output)

    def update(self):
        scores, names = self.cli.selected_criterion.get_all_scores()
        self.score_display.update(scores, names, self.cli.selected_criterion.name)

    def setup_score_display(self):
        self.score_display.setup(len(self.cli.ahp.alternatives))

    def update_output(self, record):
        """Updates output label data. Also a log filter"""
        if self.output and record.levelname in ['INFO', 'ERROR']:
            self.logs.append(record.msg)
            if len(self.logs) > MAX_OUTPUT_HEIGHT:
                self.logs = self.logs[-MAX_OUTPUT_HEIGHT:]
            self.output.set_text('\n'.join(self.logs))
            return True
        return False

    def setup(self, **kwargs):
        self.cli = kwargs['cli']
        self.matrices_display = kwargs['matrices_display']
        self.on_change_ahp = kwargs['on_change_ahp']
        self.on_change_criterion = kwargs['on_change_criterion']
        self.popup = ChooseFilePopup()
        self.popup.on_choose = self.load_ahp

        # cont = BoxLayout(orientation="vertical")
        cont = GridLayout(cols=4)
        cont.size_hint_y = 0.3
        btns = [MyButton(text="Save matrix", on_press=self.save_matrix),
                MyButton(text="Remove matrix", on_press=self.remove_matrix),
                MyButton(text="Add matrix", on_press=self.add_matrix),
                MyButton(text="Reset matrix", on_press=self.reset_matrix),
                MyButton(text="Load ranking", on_press=self.popup.open),
                MyButton(text="Save to file", on_press=self.save_all)
                ]
        for btn in btns:
            cont.add_widget(btn)
        self.add_widget(cont)
        self.score_display = ScoreDisplay()
        self.add_widget(self.score_display)
        output = BoxLayout()
        self.output = OutputView(text="Log console:")
        output.add_widget(self.output)
        self.add_widget(output)

    def save_all(self, instance):
        filename = self.cli.ahp.filename
        self.cli.ahp.save_decisions(filename)
        log.info(f"Ranking saved successfully to {filename}")

    def load_ahp(self):
        # print(self.popup.ids['filechooser'].selection)
        self.popup.dismiss()
        self.cli.on_load(self.popup.ids['filechooser'].selection[0])
        self.on_change_ahp()

    def save_matrix(self, instance):
        curr_idx = self.matrices_display.current_tab._label.text  # tab name
        if curr_idx == 'A':
            # TODO error?
            log.info("Can not modify the aggregated matrix")
            return
        matrix_editor = self.matrices_display.current_tab.content
        if any([not inp.is_valid for inp in matrix_editor.inputs.values()]):
            log.info("Can not save an invalid matrix")
            return
        # apply symmetry before saving
        for inp in matrix_editor.inputs.values():
            inp.on_text_validate()
        values = [float(inp.text) for inp in matrix_editor.inputs.values()]
        is_complete = True
        for i, val in enumerate(values):
            if val < 0:
                values[i] = -(1 / val)
            if val == 0:
                is_complete = False
        matrix = np.reshape(values, self.cli.selected_criterion.matrix.shape)
        self.cli.selected_criterion.set_matrix(int(curr_idx) - 1, matrix, is_complete)
        self.on_change_criterion()

    def remove_matrix(self, instance):
        if self.cli.ahp:
            curr_idx = self.matrices_display.current_tab._label.text  # tab name
            if curr_idx == 'A':
                log.info("Can not remove the aggregated matrix")
                return
            else:
                self.cli.selected_criterion.remove_matrix(int(curr_idx) - 1)
                log.info("# Matrix removed successfully")
                self.on_change_criterion()
        else:
            log.info("No loaded ahp")

    def add_matrix(self, instance):
        if self.cli.selected_criterion:
            new_matrix = np.ones(self.cli.selected_criterion.matrix.shape)
            # this matrix is complete
            self.cli.selected_criterion.add_matrix(new_matrix, True)
            self.on_change_criterion()
        else:
            log.info("No loaded ahp")

    def reset_matrix(self, instance):  # TODO handle no loaded ahp in every method
        curr_idx = self.matrices_display.current_tab._label.text
        if curr_idx == 'A':
            log.info("Can not reset the aggregated matrix")
            return
        self.cli.selected_criterion.reset_matrix(int(curr_idx) - 1)
        self.on_change_criterion()


class Controller(BoxLayout):
    def __init__(self, **kwargs):
        self.cli = CLI()
        super().__init__(**kwargs)
        self.cli.on_load("xmls/data_leaders.xml")
        self.ids['criterion_select'].setup(
            cli=self.cli,
            on_select_criterion=self.on_select
        )
        self.ids['matrices_display'].setup(
            cli=self.cli,
        )
        self.ids['control_panel'].setup(
            cli=self.cli,
            on_change_ahp=self.on_change_ahp,
            on_change_criterion=self.on_change_criterion,
            matrices_display=self.ids['matrices_display']
        )
        self.ids['criterion_select'].update()
        Clock.schedule_once(lambda _: self.on_change_ahp(), 0.1)

    def on_change_criterion(self):
        self.ids['matrices_display'].update()
        self.ids['criterion_select'].update()
        self.ids['control_panel'].setup_score_display()  # let the score table know how many rows to make
        self.ids['control_panel'].update()

    def on_change_matrices(self):
        # self.ids['criterion_select'].update()
        self.ids['matrices_display'].update()
        self.ids['control_panel'].update()

    def on_change_ahp(self):
        self.ids['matrices_display'].update()
        self.ids['criterion_select'].update()
        self.ids['control_panel'].setup_score_display()   # let the score table know how many rows to make
        self.ids['control_panel'].update()

    def on_select(self, criterion_name):
        # do something only if the selection has changed
        if not self.cli.selected_criterion or self.cli.selected_criterion.name != criterion_name:
            self.cli.on_select(criterion_name)
            self.ids['matrices_display'].update()
            self.ids['control_panel'].update()


class MyFileChooser(FileChooserListView):
    pass


class MainApp(App):
    kv_directory = "kvs"

    def build(self):
        return Controller()


if __name__ == '__main__':
    MainApp().run()
