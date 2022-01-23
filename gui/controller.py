from kivy.clock import Clock
from kivy.config import Config

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '600')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.write()

import kivy
from cli import CLI
import os
from ahp.criterion import ic_complete_methods

kivy.require('2.0.0')

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
import logging

log = logging.getLogger('mylogger')


class Controller(BoxLayout):
    inconsistency_text = StringProperty(f'Inconsistency: \n\nInconsistency ratio:')

    def __init__(self, **kwargs):
        self.cli = CLI()
        self.ic_method = ic_complete_methods[0]
        super().__init__(**kwargs)
        Clock.schedule_once(lambda x: self.setup(), 0.1)

    def setup(self):
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
            on_edit_criterion=self.on_edit_criterion,
            matrices_display=self.ids['matrices_display'],
            on_change_ic_method=self.on_change_ic_method
        )
        if self.cli.ahp:
            self.ids['criterion_select'].update(self.cli.selected_criterion.name)
            self.update_inconsistency()

    def on_edit_criterion(self):
        self.ids['matrices_display'].update()
        self.ids['control_panel'].update()
        self.update_inconsistency()

    def on_change_matrices(self):
        self.ids['criterion_select'].update(self.cli.selected_criterion.name)
        self.ids['matrices_display'].update()
        self.ids['control_panel'].update()

    def on_change_ahp(self):
        self.ids['matrices_display'].update()
        self.ids['criterion_select'].update(self.cli.selected_criterion.name)
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