from direct.showbase.DirectObject import DirectObject
from panda3d.core import TransparencyAttrib, TextNode, LineSegs, NodePath, ColorBlendAttrib, LColor
import sys

class SettingsPage(DirectObject):
    def __init__(self, base, on_start_game):
        super().__init__()
        self.base = base
        self.on_start_game = on_start_game
        self.text_nodes = []
        self.selected_index = 0
        self.callbacks = {}

        print("SettingsPage init - press enter again")
        # Example: user sets config, then presses Enter
#        self.accept("enter", self.start_game)
        self.accept("escape", sys.exit)

        self.bold_font = self.base.loader.loadFont("assets/fonts/Orbitron/static/Orbitron-Bold.ttf")

        # draw the options for the settings menu
        self.tutorial()
        self.characters_settings()
        self.custom_settings()
        self.start_game()

        self.base.accept("arrow_up",   self._move_selection, [-1])
        self.base.accept("arrow_down", self._move_selection, [1])
        self.base.accept("enter",      self._select_current)



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
    ## end callbacks

    def start_game(self):
        text_node = TextNode("start-game")
        text_node.setText("Start Game")
        text_node.setFont(self.bold_font)
        text_node.setAlign(TextNode.ACenter)

        start_game_np = self.base.aspect2d.attachNewNode(text_node.generate())
        start_game_np.setColor(1,0,0,1)
        start_game_np.setScale(0.1)
        start_game_np.setPos(0, 0, -0.2)
        start_game_np.setTransparency(True)
        
        self.text_nodes.append(start_game_np)
        self.callbacks[start_game_np] = self.start_game_cb

    def tutorial(self):
        text_node = TextNode("view-tutorial")
        text_node.setText("Tutorial")
        text_node.setFont(self.bold_font)
        text_node.setAlign(TextNode.ACenter)

        tutorial_np = self.base.aspect2d.attachNewNode(text_node.generate())
        tutorial_np.setColor(1,0,0,1)
        tutorial_np.setScale(0.1)
        tutorial_np.setPos(0, 0, 0.4)
        tutorial_np.setTransparency(True)

        self.text_nodes.append(tutorial_np)
        self.callbacks[tutorial_np] = self.tutorial_cb


    def custom_settings(self):
        text_node = TextNode("edit-custom-settings")
        text_node.setText("Custom Settings")
        text_node.setFont(self.bold_font)
        text_node.setAlign(TextNode.ACenter)

        custom_settings_np = self.base.aspect2d.attachNewNode(text_node.generate())
        custom_settings_np.setColor(1,0,0,1)
        custom_settings_np.setScale(0.1)
        custom_settings_np.setPos(0, 0, 0)
        custom_settings_np.setTransparency(True)

        self.text_nodes.append(custom_settings_np)
        self.callbacks[custom_settings_np] = self.custom_settings_cb


    def characters_settings(self):
        text_node = TextNode("edit-characters")
        text_node.setText("Edit Characters")
        text_node.setFont(self.bold_font)
        text_node.setAlign(TextNode.ACenter)

        characters_settings_np = self.base.aspect2d.attachNewNode(text_node.generate())
        characters_settings_np.setColor(1,0,0,1)
        characters_settings_np.setScale(0.1)
        characters_settings_np.setPos(0, 0, 0.2)
        characters_settings_np.setTransparency(True)

        self.text_nodes.append(characters_settings_np)
        self.callbacks[characters_settings_np] = self.characters_settings_cb
        


    def _start_game(self):
        print("Starting game from settings...")
        self.cleanup()
        self.on_start_game()

    def cleanup(self):
        self.ignoreAll()
        # remove ui nodes