import os
import sys
import win32timezone  # for kivy filechooser
import kivy
from kivy.app import App
from kivy.lang import Builder
import logging
# important do not remove. Loads custom widgets
import gui

log = logging.getLogger("mylogger")


class MainApp(App):
    title = "AHP Solicitor"

    def build(self):
        try:
            os.mkdir("xmls")  # try to make a directory for rankings
            log.info("Created xmls folder")
        except:
            pass
        self.root = Builder.load_file("layout.kv")
        return self.root


def reset():
    import kivy.core.window as window
    from kivy.base import EventLoop
    if not EventLoop.event_listeners:
        from kivy.cache import Cache
        window.Window = window.core_select_lib('window', window.window_impl, True)
        Cache.print_usage()
        for cat in Cache._categories:
            Cache._objects[cat] = {}


if __name__ == '__main__':
    reset()
    if getattr(sys, 'frozen', False):
        # this is a Pyinstaller bundle
        kivy.resources.resource_add_path(sys._MEIPASS)
    MainApp().run()
