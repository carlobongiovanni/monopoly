from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from direct.interval.IntervalGlobal import LerpColorScaleInterval, Sequence, Func
from panda3d.core import TransparencyAttrib, TextNode, LineSegs, NodePath, ColorBlendAttrib, LColor
import random
import sys
from math import sin

class TitleScreen(DirectObject):
    def __init__(self, base, on_start):
        super().__init__()
        self.base = base
        self.on_start = on_start

        self.accept("enter", self.start_game)
        self.accept("escape", sys.exit)

        self.enter_text = None
        self.noisy_text = None

        # Disable default camera mouse
        self.base.disableMouse()

        # Set 2D aspect render
        self.base.setBackgroundColor(0, 0, 0)
        bg = OnscreenImage(parent=self.base.render2d, image="assets/bg_fill.png")
        bg.setTransparency(TransparencyAttrib.MAlpha)

        self.bold_font = self.base.loader.loadFont("Orbitron/static/Orbitron-Bold.ttf")
        self.title = "CELEBRITY\nWARS"

        # Add noisy red text
        self.create_noisy_text()

        # Add press enter to start
        self.create_press_enter()

        self.lasers = LaserField(self.base.render2d, num_lines=5)
        self.base.taskMgr.doMethodLater(0.2, self.lasers.animate, "LaserUpdateTask")
        self.base.taskMgr.add(self.pulse_text, "PulseTextTask")

    def create_press_enter(self):

        self.enter_text = OnscreenText(
            text="PRESS [ENTER] TO PLAY",
            font=self.bold_font,
            pos=(0, -0.4),  # center down
            scale=0.1,
            fg=LColor(1, 0, 0, 1),  # red
            mayChange=True,
            align=TextNode.ACenter,
            parent=self.base.aspect2d
        )

    def pulse_text(self, task):
        t = globalClock.getFrameTime()
        brightness = 0.5 + 0.5 * abs(sin(t * 3))  # between 0.5 and 1.0
        self.enter_text.setColorScale(brightness, 0.0, 0.0, 1.0)
        return task.cont
        
    def create_noisy_text(self):

        self.noisy_text = OnscreenText(
            text=self.title,
            font=self.bold_font,
            pos=(0, .2),  # center
            scale=0.25,
            fg=LColor(.5, 0, 0, 1),  # red
            mayChange=True,
            align=TextNode.ACenter,
            parent=self.base.aspect2d
        )
        self.noisy_text.setTransparency(True)

    def start_game(self):
        """callback to get into the FSM"""
        print("Enter pressed — starting game!")
        self.ignore("enter")
        self.ignore("escape")
        self.fade_out()

    def fade_out(self):
        fade_duration = 1.2

        # Intervals for text + enter prompt
        text_fade  = LerpColorScaleInterval(self.noisy_text, fade_duration, (0, 0, 0, 0))
        enter_fade = LerpColorScaleInterval(self.enter_text, fade_duration, (0, 0, 0, 0))

        intervals = [text_fade, enter_fade]

        # If lasers exist and weren't removed yet
        if self.lasers and not self.lasers.node.isEmpty():
            laser_fade = LerpColorScaleInterval(self.lasers.node, fade_duration, (0, 0, 0, 0))
            intervals.append(laser_fade)

        # Build and play sequence
        fade_sequence = Sequence(
            *intervals,
            Func(self.cleanup),
            Func(self.on_start)
        )
        fade_sequence.start()

    def cleanup(self):
        self.base.taskMgr.remove("LaserUpdateTask")
        self.base.taskMgr.remove("PulseTextTask")
        if self.lasers and not self.lasers.node.isEmpty():
            self.lasers.node.removeNode()
        self.noisy_text.removeNode()
        self.enter_text.removeNode()



class LaserField:
    def __init__(self, render2d, num_lines=20):
        self.render2d = render2d
        self.num_lines = num_lines
        self.node = NodePath("laser-lines")
        self.node.reparentTo(render2d)
        self.node.setTransparency(TransparencyAttrib.MAlpha)
        self.node.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
        self.update_lasers()

    def update_lasers(self):
        self.node.node().removeAllChildren()
        segs = LineSegs()
        segs.setThickness(2.5)
        segs.setColor(1, 0, 0, 0.7)  # semi-transparent red

        for _ in range(self.num_lines):
            x1, y1 = random.uniform(-1.5, 1.5), random.uniform(-1, 1)
            x2, y2 = random.uniform(-1.5, 1.5), random.uniform(-1, 1)
            segs.moveTo(x1, 0, y1)
            segs.drawTo(x2, 0, y2)

        self.node.attachNewNode(segs.create())

    def animate(self, task):
        self.update_lasers()
        # Rotate slowly over time
        t = task.time
        self.node.setH(t * 30)  # 10 degrees per second
        
        return Task.cont
