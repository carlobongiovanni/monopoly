from direct.showbase.DirectObject import DirectObject
from panda3d.core import CardMaker, Shader, Vec4
import sys

class CharactersSettings(DirectObject):
    def __init__(self, base, on_start, on_escape):
        super().__init__()
        self.base = base
        self.on_start_cb = on_start
        self.on_escape_cb = on_escape
        # escape will go back
        self.accept("escape", self._handle_escape)
        # start will save and go back
        self.accept("enter", self._handle_start)

        self.characters_settings_root = None
        self.card = None

        self.box_positions = [
            Vec4(0.16, 0.09, 0.3, 0.7),  # left
            Vec4(0.53, 0.22, 0.3, 0.7),  # right
        ]
        self.current_index = 0

        self.draw_characters_settings()

        self.accept("arrow_left",  self.move_box, [-1])
        self.accept("arrow_right", self.move_box, [+1])

    def _handle_start(self):
        print("saving selected character and going back")
        self.hide_character_settings()
        self.ignore("arrow_left")
        self.ignore("arrow_right")
        self.ignore("enter")
        self.ignore("escape")
        self.on_start_cb()

    def _handle_escape(self):
        print("no saving, going back")
        self.hide_character_settings()
        self.ignore("arrow_left")
        self.ignore("arrow_right")
        self.ignore("enter")
        self.ignore("escape")
        self.on_escape_cb()

    def hide_character_settings(self):
        if self.characters_settings_root:
            self.characters_settings_root.removeNode()
            self.characters_settings_root = None
            self.current_index = 1
            self.card = None

    def draw_characters_settings(self):
        if self.characters_settings_root:
            self.characters_settings_root.removeNode()
        self.current_index = 1
        self.card = None

        self.characters_settings_root = self.base.render2d.attachNewNode("characters-setting-root")

        # Load and display the background image on a full-screen quad
        tex = self.base.loader.loadTexture("assets/bg_characters.png")
        cm  = CardMaker("bg_characters")
        cm.setFrame(-1, 1, -1, 1)
        card = self.characters_settings_root.attachNewNode(cm.generate())
        card.setDepthTest(False)
        card.setDepthWrite(False)
        card.setBin("fixed", 50)
        card.setTexture(tex)
        card.setShader(Shader.load(Shader.SL_GLSL,
                                  "assets/shaders/blur.vert",
                                  "assets/shaders/blur.frag"))
        self.card = card
        self.update_shader_box()

    def update_shader_box(self):
        self.card.setShaderInput("box", self.box_positions[self.current_index])

    def move_box(self, delta):
        # wrap index around the list
        self.current_index = (self.current_index + delta) % len(self.box_positions)
        self.update_shader_box()
