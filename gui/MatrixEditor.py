from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput


class MatrixInput(TextInput):
    def __init__(self, **kwargs):
        self.shortable = kwargs.pop('shortable', True)
        if self.shortable and len(kwargs['text']) > 5:
            kwargs['text'] = kwargs['text'][:5]
        self.font_size = kwargs.pop('font_size', '20sp')
        self.grid_pos = kwargs.pop('pos', None)
        self.on_input_change = kwargs.pop("on_input_change", None)
        self.readonly = kwargs.pop('readonly', False)
        super().__init__(**kwargs)
        self.is_valid = True  # is the current text a valid ahp comparison value
        self.check_text(None, None)  # set self.is_valid
        self.bind(text=self.check_text)
        if self.readonly:
            self.background_color = .7, .7, .7, .2
            self.foreground_color = .75, .75, .75, 1

    def insert_text(self, diff, from_undo=False):
        if not self.readonly and len(self.text + diff) <= 5:
            super().insert_text(diff, from_undo)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] == 'tab':  # deal with cycle
            if "shift" in modifiers:
                nextInp = self.get_focus_previous()
            else:
                nextInp = self.get_focus_next()
            if nextInp:
                self.focus = False
                nextInp.focus = True
                nextInp.select_all()
            return True
        super().keyboard_on_key_down(window, keycode, text, modifiers)
        return False

    def check_text(self, instance, value):
        if self.shortable:
            self.text = self.text[:5]
        try:
            val = float(self.text)
            assert -9 <= val <= 9
            self.foreground_color = .8, .8, .8, 1
            self.is_valid = True
            if not self.readonly:
                self.on_input_change(self.grid_pos)  # fix the symmetry
        except (ValueError, AssertionError):
            self.foreground_color = (1, 0.3, 0.3, 1)
            self.is_valid = False


class MatrixEditor(GridLayout):
    def __init__(self, **kwargs):
        self.matrix = kwargs.pop('matrix')
        headers = kwargs.pop('children')
        self.on_matrix_edit = kwargs.pop('on_matrix_edit')
        self.idx = kwargs.pop('idx')
        self.cols = self.matrix.shape[1] + 1  # +1 for the headers
        super().__init__(**kwargs)

        # create the matrix
        self.inputs = {}
        for y in range(self.cols):
            for x in range(self.cols):
                if y == 0 and x == 0:
                    inp = MatrixInput(text="", readonly=True, font_size="5sp")
                elif y == 0:
                    inp = MatrixInput(text=headers[x - 1].name, readonly=True, font_size="15sp", shortable=False)
                elif x == 0:
                    inp = MatrixInput(text=headers[y - 1].name, readonly=True, font_size="15sp", shortable=False)
                else:
                    is_lower_triangle = y >= x
                    # if idx == -1, this matrix is the aggregated one - make is readonly
                    inp = MatrixInput(text=str(self.matrix[y - 1][x - 1]),
                                      readonly=(is_lower_triangle or self.idx == -1),
                                      pos=(x - 1, y - 1),
                                      on_input_change=self.on_input_change
                                      )
                    self.inputs[str((x - 1, y - 1))] = inp
                self.add_widget(inp)

    def on_input_change(self, inp_pos):
        if str(inp_pos) not in self.inputs:
            return
        text = self.inputs[str(inp_pos)].text
        sym_input = self.inputs[str((inp_pos[1], inp_pos[0]))]
        if not text:
            sym_input.text = ''
            return
        value = float(text)  # no exception as it should be validated by the validation in MatrixInput
        if value == 0:
            sym_input.text = '0'
        elif value < 0:
            sym_input.text = str(-value)
        else:
            sym_input.text = str(1 / value)
        self.on_matrix_edit() # TODO add it back?
