import logging
from typing import Optional

import numpy as np
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from CLI import CLI
from Criterion import calc_weight_methods, ic_complete_methods, ic_incomplete_methods
from gui.MethodSelect import MethodSelect
from gui.ScoreDisplay import ScoreDisplay

log = logging.getLogger('mylogger')
MAX_OUTPUT_HEIGHT = 20


class MyButton(Button):
    pass


class ChooseFilePopup(Popup):
    pass


class MyFileChooser(FileChooserListView):
    pass


class OutputView(ScrollView):
    def __init__(self, **kwargs):
        text = kwargs.pop('text', '')
        super().__init__(**kwargs)
        self.set_text(text)

    def set_text(self, new_text):
        self.ids['label'].text = new_text


class ControlPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # all set in setup, sorry
        self.score_display = None
        self.popup = None
        self.output = None  # log output label
        self.cli: Optional[CLI] = None
        self.on_change_ahp = None
        self.on_edit_criterion = None
        self.matrices_display = None
        self.on_change_ic_method = None

        self.logs = []
        log.setLevel(logging.INFO)
        log.addFilter(self.update_output)

    def update(self):
        scores, names = self.cli.selected_criterion.get_all_scores()
        print(scores, names)
        self.score_display.update(scores, names, self.cli.selected_criterion.name)

    def setup_score_display(self):
        self.score_display.setup(len(self.cli.ahp.alternatives))

    def update_output(self, record):
        """Updates output label data each time something of level INFO or ERROR is logged"""
        if self.output and record.levelname in ['INFO', 'ERROR']:
            self.logs.append(record.msg)
            if len(self.logs) > MAX_OUTPUT_HEIGHT:
                self.logs = self.logs[-MAX_OUTPUT_HEIGHT:]
            self.output.set_text('\n'.join(self.logs))
            return True
        return False

    def setup(self, **kwargs):
        """Creates the layout. Buttons, scores, method dropdowns and console log"""
        self.cli = kwargs['cli']
        self.matrices_display = kwargs['matrices_display']
        self.on_change_ahp = kwargs['on_change_ahp']
        self.on_edit_criterion = kwargs['on_edit_criterion']
        self.on_change_ic_method = kwargs.pop('on_change_ic_method')
        self.popup = ChooseFilePopup()
        self.popup.on_choose = self.load_ahp

        # cont = BoxLayout(orientation="vertical")
        cont = GridLayout(cols=3)
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
        box = BoxLayout(orientation='vertical', spacing="2dp")
        box.size_hint = (1, None)
        box.height = "60dp"
        box.add_widget(MethodSelect(descr="Weight calc method",
                                    methods=calc_weight_methods,
                                    on_select=self.on_change_calc_weight_method)
                       )
        box.add_widget(MethodSelect(descr="Inconsistency calc method",
                                    methods=ic_complete_methods + ic_incomplete_methods,
                                    on_select=self.on_change_ic_method)
                       )
        self.add_widget(box)
        output = BoxLayout()
        self.output = OutputView(text="Log console:")
        output.add_widget(self.output)
        self.add_widget(output)

    def on_change_calc_weight_method(self, new_method):
        self.cli.ahp.set_all_calc_weight_method(new_method)
        self.update()

    def save_all(self, instance):
        filename = self.cli.ahp.filename
        self.cli.ahp.save_decisions(filename)
        log.info(f"Ranking saved successfully to {filename}")

    def load_ahp(self):
        self.popup.dismiss()
        self.cli.on_load(self.popup.ids['filechooser'].selection[0])
        self.on_change_ahp()

    def save_matrix(self, instance):
        curr_idx = self.matrices_display.current_tab._label.text  # get selected tab's name
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
        self.on_edit_criterion()

    def remove_matrix(self, instance):
        if self.cli.ahp:
            curr_idx = self.matrices_display.current_tab._label.text  # get selected tab's name
            if curr_idx == 'A':
                log.info("Can not remove the aggregated matrix")
                return
            else:
                self.cli.selected_criterion.remove_matrix(int(curr_idx) - 1)
                log.info("# Matrix removed successfully")
                self.on_edit_criterion()
        else:
            log.info("No loaded ahp")

    def add_matrix(self, instance):
        if self.cli.selected_criterion:
            new_matrix = np.ones(self.cli.selected_criterion.matrix.shape)
            # this matrix is complete
            self.cli.selected_criterion.add_matrix(new_matrix, True)
            self.on_edit_criterion()
        else:
            log.info("No loaded ahp")

    def reset_matrix(self, instance):  # TODO handle no loaded ahp in every method?
        curr_idx = self.matrices_display.current_tab._label.text  # get selected tab's name
        if curr_idx == 'A':
            log.info("Can not reset the aggregated matrix")
            return
        self.cli.selected_criterion.reset_matrix(int(curr_idx) - 1)
        self.on_edit_criterion()
