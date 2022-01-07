from typing import Optional

import numpy as np
import kivy
from kivy.uix.button import Button
from kivy.uix.stacklayout import StackLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from CLI import CLI
from Node import Node
from kivy.clock import Clock
from gui.MatrixEditor import MatrixInput, MatrixEditor

kivy.require('1.0.5')

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewLabel

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty


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

    def update(self):   # TODO tree view reload and update
        if self.cli.ahp:
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

    def update(self):   # TODO optimize update cache matrix editors?
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


class ControlPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cli : Optional[CLI] = None
        self.notify_about_change = None
        self.matrices_display = None

    def save_matrix(self, instance):
        curr_idx = self.matrices_display.current_tab._label.text  # tab name
        if curr_idx == 'A':
            print("Can not modify the aggregated matrix")
            return
        matrix_editor = self.matrices_display.current_tab.content
        if any([not inp.is_valid for inp in matrix_editor.inputs.values()]):
            print("Can not save an invalid matrix")
            return
        # apply symmetry before saving
        for inp in matrix_editor.inputs.values():
            inp.on_text_validate()
        values = [float(inp.text) for inp in matrix_editor.inputs.values()]
        is_complete = True
        for i, val in enumerate(values):
            if val < 0:
                values[i] = -(1/val)
            if val == 0:
                is_complete = False
        matrix = np.reshape(values, self.cli.selected_criterion.matrix.shape)
        self.cli.selected_criterion.set_matrix(int(curr_idx)-1, matrix, is_complete)
        self.notify_about_change()

    def remove_matrix(self, instance):
        if self.cli.ahp:
            curr_idx = self.matrices_display.current_tab._label.text  # tab name
            if curr_idx == 'A':
                print("Can not remove the aggregated matrix")
                return
            else:
                self.cli.selected_criterion.remove_matrix(int(curr_idx)-1)
                self.notify_about_change()
        else:
            print("No loaded ahp")

    def add_matrix(self, instance):
        if self.cli.selected_criterion:
            new_matrix = np.ones(self.cli.selected_criterion.matrix.shape)
            # this matrix is complete
            self.cli.selected_criterion.add_matrix(new_matrix, True)
            self.notify_about_change()
        else:
            print("No loaded ahp")

    def reset_matrix(self, instance):   # TODO handle no loaded ahp in every method
        curr_idx = self.matrices_display.current_tab._label.text
        if curr_idx == 'A':
            print("Can not reset the aggregated matrix")
            return
        self.cli.selected_criterion.reset_matrix(int(curr_idx)-1)
        self.notify_about_change()

    def setup(self, **kwargs):
        self.cli = kwargs['cli']
        self.matrices_display = kwargs['matrices_display']
        self.notify_about_change = kwargs['on_change']
        cont = StackLayout()
        btns = [MyButton(text="Save matrix", on_press=self.save_matrix),
                MyButton(text="Remove matrix", on_press=self.remove_matrix),
                MyButton(text="Add matrix", on_press=self.add_matrix),
                MyButton(text="Reset matrix", on_press=self.reset_matrix)]
        for btn in btns:
            cont.add_widget(btn)
        self.add_widget(cont)


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
            on_change=self.on_change_matrices,
            matrices_display=self.ids['matrices_display']
        )
        self.ids['criterion_select'].update()
        Clock.schedule_once(lambda _: self.ids['matrices_display'].update(), 0.1)

    def on_change_matrices(self):
        # self.ids['criterion_select'].update()
        self.ids['matrices_display'].update()

    def on_select(self, criterion_name):
        # select only if it's not already selected
        if not self.cli.selected_criterion or self.cli.selected_criterion.name != criterion_name:
            self.cli.on_select(criterion_name)
            self.ids['matrices_display'].update()


class MainApp(App):
    kv_directory = "kvs"

    def build(self):
        return Controller()


if __name__ == '__main__':
    MainApp().run()
