from kivy.config import Config

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '600')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.write()

import kivy
from CLI import CLI
import os
from Criterion import ic_complete_methods

kivy.require('2.0.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
import gui  # needs to be there for kivy
import logging

log = logging.getLogger('mylogger')


class Controller(BoxLayout):
    inconsistency_text = StringProperty(f'Inconsistency: \n\nInconsistency ratio:')

    def __init__(self, **kwargs):
        self.cli = CLI()
        self.ic_method = ic_complete_methods[0]
        super().__init__(**kwargs)
        # self.cli.on_load("xmls/data_leaders.xml")
        self.ids['criterion_select'].setup(
            cli=self.cli,
            on_select_criterion=self.on_select
        )
        self.ids['matrices_display'].setup(
            cli=self.cli,
            on_matrix_edit=self.on_edit_matrix
        )
        self.ids['control_panel'].setup(
            cli=self.cli,
            on_change_ahp=self.on_change_ahp,
            on_edit_criterion=self.on_edit_criterion,
            matrices_display=self.ids['matrices_display'],
            on_change_ic_method=self.on_change_ic_method
        )
        self.ids['criterion_select'].update()
        if self.cli.ahp:
            self.update_inconsistency()
        # Clock.schedule_once(lambda _: self.on_change_ahp(), 0.1)

    def on_edit_criterion(self):
        self.ids['matrices_display'].update()
        self.ids['control_panel'].update()
        self.update_inconsistency()

    def on_change_matrices(self):
        self.ids['criterion_select'].update()
        self.ids['matrices_display'].update()
        self.ids['control_panel'].update()

    def on_edit_matrix(self):
        """To resource hungry atm, most likely because of reading and parsing data from matrix labels"""
        pass
        # self.ids['control_panel'].setup_score_display()  # let the score table know how many rows to make
        # self.ids['control_panel'].update()
        # self.ids['control_panel'].save_matrix(None)  # None is the button instance, maybe will be removed
        # self.update_inconsistency()

    def on_change_ahp(self):
        self.ids['matrices_display'].update()
        self.ids['criterion_select'].update()
        self.ids['control_panel'].setup_score_display()  # let the score table know how many rows to make
        self.ids['control_panel'].update()
        self.update_inconsistency()

    def on_change_ic_method(self, new_method):
        self.ic_method = new_method
        log.info(f'# Changed inconsistency calc method to {new_method}')
        self.update_inconsistency()

    def on_select(self, criterion_name):
        # do something only if the selection has changed
        if self.cli.selected_criterion:
            if not self.cli.selected_criterion or self.cli.selected_criterion.name != criterion_name:
                self.cli.on_select(criterion_name)
                self.ids['matrices_display'].update()
                self.ids['control_panel'].update()
                self.update_inconsistency()

    def update_inconsistency(self):
        ic, icr = self.cli.selected_criterion.ic(self.ic_method)
        if ic is None:
            log.error(f"Invalid method. Can not use {self.ic_method} with current matrices")
            self.inconsistency_text = f'Inconsistency = ?\n\n'
            self.inconsistency_text += f'Inconsistency ratio = ?'
            return
        self.inconsistency_text = f'Inconsistency = {"{:.5f}".format(ic)}\n\n'
        self.inconsistency_text += f'Inconsistency ratio = {"{:.5f}".format(icr)}'


class MainApp(App):
    kv_directory = "kvs"
    title = "AHP Solicitor"

    def build(self):
        try:
            os.mkdir("xmls")  # try to make a directory for rankings
            log.info("Created xmls folder")
        except:
            pass
        return Controller()


if __name__ == '__main__':
    MainApp().run()
