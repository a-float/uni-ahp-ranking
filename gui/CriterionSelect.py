from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeViewLabel, TreeView


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

    def update(self):
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
    def populate_tree_view(tree_view, parent, node):
        name = node.name
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=name,
                                                         is_open=True))
        else:
            tree_node = tree_view.add_node(TreeViewLabel(text=name,
                                                         is_open=True), parent)
        if not node.is_final_criterion:
            for child_node in node.children:
                CriterionSelect.populate_tree_view(tree_view, tree_node, child_node)
