import logging
import os
from typing import Optional
from pathlib import Path

import numpy as np
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from cli import CLI
from ahp.criterion import calc_weight_methods, ic_complete_methods, ic_incomplete_methods
from gui.methodSelect import MethodSelect
from gui.scoreDisplay import ScoreDisplay

log = logging.getLogger('mylogger')
MAX_OUTPUT_HEIGHT = 20


class MyButton(Button):
    pass


class ChooseFilePopup(Popup):
    pass


class TextInputPopup(Popup):
    def __init__(self, **kwargs):
        self.label_text = kwargs.pop('label_text')
        self.on_choose = kwargs.pop('on_choose')
        super().__init__(**kwargs)


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
        self.addCriterionPopup = None
        self.removeAlternativePopup = None
        self.addAlternativePopup = None
        self.rankingNameInputPopup = None
        self.score_display = None
        self.fileChoosePopup = None
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

    def create_ahp(self):
        self.rankingNameInputPopup.dismiss()
        input = self.rankingNameInputPopup.ids['text_input'].text
        split = input.split()
        if not split:
            log.error("Invalid goal name")
            return
        goal_name = ' '.join(split).encode(encoding='ascii', errors="replace").decode()  # remove non ascii characters
        filename = '_'.join(split) + ".xml"
        Path("./xmls/").mkdir(parents=True, exist_ok=True)
        if Path('./xmls/' + filename).exists():
            log.error(f"File '{filename}' already exists in the xml directory")
            return
        try:
            with open('./xmls/' + filename, 'w') as f:
                pass
        except:
            log.error("Could not create file ./xmls/" + filename)
            return
        with open('./xmls/' + filename, 'w') as f:
            f.writelines(['<?xml version="1.0" encoding="UTF-8"?>\n',
                          "<root>\n",
                          f'<criterion name="Goal" goal="{goal_name}">"</criterion>\n',
                          "<alternatives></alternatives>\n",
                          "<data></data>\n",
                          "</root>\n"])
        self.cli.on_load(f"./xmls/{filename}")
        self.on_change_ahp()

    def modify_alternatives(self, remove=False):
        popup = self.addAlternativePopup if not remove else self.removeAlternativePopup
        popup.dismiss()
        if not self.cli.ahp:
            log.error("No ahp loaded")
            return
        name = popup.ids['text_input'].text
        popup.ids['text_input'].text = ""  # clear input
        if len(name) > 0:
            log.info("All matrices dependent on alternatives will be removed")
            if not remove:
                res = self.cli.ahp.add_alternative(name)
            else:
                res = self.cli.ahp.remove_alternative(name)
            if res:
                self.on_edit_criterion()
                log.info(f"Alternative {name} removed")
            else:
                log.error("Could not remove alternative " + name)
        else:
            log.error("No name specified")

    def add_criterion(self):
        popup = self.addCriterionPopup
        popup.dismiss()
        if not self.cli.ahp:
            log.error("No ahp loaded")
            return
        name = popup.ids['text_input'].text
        popup.ids['text_input'].text = ""  # clear input
        if len(name) > 0:
            log.info("All matrices dependent on alternatives will be removed")
            self.cli.selected_criterion.add_subcriterion(name)
            self.on_change_ahp()  # to update criterion select
        else:
            log.error("No name specified")

    def remove_criterion(self, instance):
        if not self.cli.ahp:
            log.error("No ahp loaded")
            return
        if self.cli.selected_criterion == self.cli.ahp.root_criterion:
            log.error("Can not remove the root criterion")
            return
        toSelectNext = self.cli.selected_criterion.parent
        self.cli.selected_criterion.remove()
        self.cli.selected_criterion = toSelectNext
        self.on_change_ahp()  # to update criterion select

    def setup(self, **kwargs):
        """Creates the layout. Buttons, scores, method dropdowns and console log"""
        self.cli = kwargs['cli']
        self.matrices_display = kwargs['matrices_display']
        self.on_change_ahp = kwargs['on_change_ahp']
        self.on_edit_criterion = kwargs['on_edit_criterion']
        self.on_change_ic_method = kwargs.pop('on_change_ic_method')
        self.fileChoosePopup = ChooseFilePopup()
        self.fileChoosePopup.on_choose = self.load_ahp
        self.rankingNameInputPopup = TextInputPopup(label_text="Choose new ranking's filename:",
                                                    on_choose=self.create_ahp)
        self.addAlternativePopup = TextInputPopup(label_text="What is the new alternatives name?",
                                                  on_choose=self.modify_alternatives)
        self.removeAlternativePopup = TextInputPopup(
            label_text="What is the name of the alternative you want to remove?",
            on_choose=lambda: self.modify_alternatives(True))
        self.addCriterionPopup = TextInputPopup(label_text="Choose new criterion's name?",
                                                on_choose=self.add_criterion)
        self.chooseSaveNamePopup = TextInputPopup(
            label_text="Choose filename to save to. Leave blank to overwrite the previously loaded file.",
            on_choose=self.save_all)

        cont = GridLayout(cols=3)
        cont.size_hint_y = 0.7
        btns = [MyButton(text="Load ranking", on_press=self.fileChoosePopup.open),
                MyButton(text="New ranking", on_press=self.rankingNameInputPopup.open),
                MyButton(text="Apply matrix", on_press=self.apply_matrix),
                MyButton(text="Add matrix", on_press=self.add_matrix),
                MyButton(text="Remove matrix", on_press=self.remove_matrix),
                MyButton(text="Reset matrix", on_press=self.reset_matrix),
                MyButton(text="Add alternative", on_press=self.addAlternativePopup.open),
                MyButton(text="Erase alternative", on_press=self.removeAlternativePopup.open),
                MyButton(text="Add criterion", on_press=self.addCriterionPopup.open),
                MyButton(text="Remove criterion", on_press=self.remove_criterion),
                MyButton(text="Save to file", on_press=self.chooseSaveNamePopup.open)
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

    def save_all(self):
        if not self.cli.ahp:
            log.error("No ahp loaded")
            return
        self.chooseSaveNamePopup.dismiss()
        text = self.chooseSaveNamePopup.ids['text_input'].text
        filename = self.cli.ahp.filename if not text else text
        if not filename.endswith('.xml'):
            filename += ".xml"
        filename = os.path.basename(os.path.normpath(filename))
        filename = os.path.join("xmls", filename)
        self.cli.ahp.save_to_file(filename)
        log.info(f"Ranking saved successfully to '{filename}'")

    def load_ahp(self):
        self.fileChoosePopup.dismiss()
        fc = self.fileChoosePopup.ids['filechooser']
        if not fc.selection:
            log.error("Loading unsuccessful - no file selected")
            return
        try:
            self.cli.on_load(fc.selection[0])
        except ValueError as e:
            filename = os.path.basename(fc.selection[0])
            log.error(f"Loading unsuccessful - invalid or corrupted ranking '{filename}'")
            return
        self.on_change_ahp()

    def apply_matrix(self, instance):
        if not self.cli.ahp:
            log.error("No loaded ahp")
            return
        curr_idx = self.matrices_display.current_tab._label.text  # get selected tab's name
        if curr_idx == 'A':
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

    def reset_matrix(self, instance):
        if not self.cli.ahp:
            log.error("No ahp loaded")
            return
        curr_idx = self.matrices_display.current_tab._label.text  # get selected tab's name
        if curr_idx == 'A':
            log.info("Can not reset the aggregated matrix")
            return
        self.cli.selected_criterion.reset_matrix(int(curr_idx) - 1)
        self.on_edit_criterion()
