from kivy.uix.tabbedpanel import TabbedPanelItem, TabbedPanel
from gui.MatrixEditor import MatrixEditor


class MatricesDisplay(TabbedPanel):
    def __init__(self, **kwargs):
        self.on_matrix_edit = None
        super().__init__(**kwargs)
        self.cli = None

    def setup(self, **kwargs):
        self.on_matrix_edit = kwargs.pop('on_matrix_edit')
        self.cli = kwargs['cli']

    def update(self):  # TODO optimize update - cache matrix editors?
        if self.cli.ahp:
            prev_tab_name = self.current_tab._label.text
            selected = self.cli.selected_criterion
            self.clear_tabs()
            panel_items = []
            aggr_panel = TabbedPanelItem(text="A")
            aggr_panel.add_widget(MatrixEditor(idx=-1, children=selected.children, matrix=selected.matrix,
                                               on_matrix_edit=self.on_matrix_edit))
            panel_items.append(aggr_panel)
            for i, matrix in enumerate(self.cli.selected_criterion.matrices):
                panel = TabbedPanelItem(text=f"{i + 1}")
                panel.add_widget(MatrixEditor(idx=i, children=selected.children, matrix=selected.matrices[i],
                                              on_matrix_edit=self.on_matrix_edit))
                panel_items.append(panel)
            for panel in panel_items:
                self.add_widget(panel)
            # if possible, switch back to the previous tab
            tab_names = list(map(lambda x: x._label.text, self.tab_list))
            if prev_tab_name in tab_names:
                self.switch_to(self.tab_list[tab_names.index(prev_tab_name)])
            else:
                self._switch_to_first_tab()
