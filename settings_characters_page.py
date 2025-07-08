from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker, Shader, Vec4, loadPrcFileData
import sys

# tell Panda to make a 1024×600 window, windowed (not fullscreen)
loadPrcFileData("", """
    win-size 1024 600
    fullscreen 0
    show-frame-rate-meter 0
""")

class GrayscaleBoxesApp(ShowBase):
    def __init__(self):
        super().__init__()
        self.accept("escape", sys.exit)

        # Load and display the background image on a full-screen quad
        tex = self.loader.loadTexture("assets/bg_characters.png")
        cm  = CardMaker("bg")
        cm.setFrame(-1, 1, -1, 1)
        card = self.render2d.attachNewNode(cm.generate())
        card.setTexture(tex)
        card.setShader(Shader.load(Shader.SL_GLSL,
                                  "assets/shaders/blur.vert",
                                  "assets/shaders/blur.frag"))
        self.card = card

        # 2) define the preset box positions (x, y, w, h) in UV coords
        self.boxPositions = [
            Vec4(0.16, 0.09, 0.3, 0.7),  # left
            Vec4(0.53, 0.22, 0.3, 0.7),  # right
        ]
        self.currentIndex = 1  # start at center
        self.update_shader_box()

        # 3) bind arrows to cycle through those positions
        self.accept("arrow_left",  self.move_box, [-1])
        self.accept("arrow_right", self.move_box, [+1])

    def update_shader_box(self):
        self.card.setShaderInput("box", self.boxPositions[self.currentIndex])

    def move_box(self, delta):
        # wrap index around the list
        self.currentIndex = (self.currentIndex + delta) % len(self.boxPositions)
        self.update_shader_box()

if __name__ == "__main__":
    app = GrayscaleBoxesApp()
    app.run()
