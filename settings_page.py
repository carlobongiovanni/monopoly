from direct.showbase.DirectObject import DirectObject
from panda3d.core import TransparencyAttrib, TextNode, LineSegs, NodePath, ColorBlendAttrib, LColor
import sys
from settings_characters_page import CharactersSettings

class SettingsPage(DirectObject):
    def __init__(self, base, on_start_game):
        super().__init__()
        self.base = base
        self.on_start_game = on_start_game
        self.text_nodes = []
        self.selected_index = 0
        self.callbacks = {}
        # container for all menu nodes
        self.menu_root = None

        print("SettingsPage init - press enter again")
        # Example: user sets config, then presses Enter
#        self.accept("enter", self.start_game)
        self.base.accept("escape", sys.exit)

        self.bold_font = self.base.loader.loadFont("assets/fonts/Orbitron/static/Orbitron-Bold.ttf")

        self.show_menu()
        # draw the options for the settings menu

        self.base.accept("arrow_up",   self._move_selection, [-1])
        self.base.accept("arrow_down", self._move_selection, [1])
        self.base.accept("enter",      self._select_current)

    def show_menu(self):
        if self.menu_root:
            self.menu_root.removeNode()

        self.menu_root = self.base.aspect2d.attachNewNode("menu-root")
        self.text_nodes.clear()
        self.callbacks.clear()

        self.draw_menu_element("view-tutorial", "Tutorial", 0.4, self.tutorial_cb)
        self.draw_menu_element("edit-characters", "Edit Characters", 0.2, self.characters_settings_cb)
        self.draw_menu_element("edit-custom-settings", "Custom Settings", 0, self.custom_settings_cb)
        self.draw_menu_element("start-game", "Start Game", -0.2, self.start_game_cb)

    def hide_menu(self):
        # nukes the entire menu and all its text nodes
        if self.menu_root:
            self.menu_root.removeNode()
            self.menu_root = None
            self.text_nodes.clear()
            self.callbacks.clear()

    def draw_menu_element(self, node_name, label, y_position, callback):
        text_node = TextNode(node_name)
        text_node.setText(label)
        text_node.setFont(self.bold_font)
        text_node.setAlign(TextNode.ACenter)

        text_node_np = self.menu_root.attachNewNode(text_node.generate())
        text_node_np.setColor(1,0,0,1)
        text_node_np.setScale(0.1)
        text_node_np.setPos(0, 0, y_position)
        text_node_np.setTransparency(True)

        self.text_nodes.append(text_node_np)
        self.callbacks[text_node_np] = callback

    def _move_selection(self, delta):
        count = len(self.text_nodes)
        self.selected_index = (self.selected_index + delta) % count
        self._update_highlight()

    def _update_highlight(self):
        for idx, np in enumerate(self.text_nodes):
            if idx == self.selected_index:
                np.setColor(1,1,0,1)  # yellow
            else:
                np.setColor(1,0,0,1)

    def _select_current(self):
        node = self.text_nodes[self.selected_index]
        cb   = self.callbacks.get(node)
        if cb:
            cb()

    ## callbacks
    def start_game_cb(self):
        self.cleanup()
        self.on_start_game()

    def tutorial_cb(self):
        print("tutorial")

    def custom_settings_cb(self):
        print("custom_settings_cb")

    def characters_settings_cb(self):
        print("characters_settings_cb")
        self.cleanup()
        cs = CharactersSettings(base=self.base, on_start=self.show_menu)
    ## end callbacks

    def _start_game(self):
        print("Starting game from settings...")
        self.cleanup()
        self.on_start_game()

    def cleanup(self):
        self.base.ignore("arrow_up")
        self.base.ignore("arrow_down")
        self.base.ignore("enter")
        self.hide_menu()
