from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib, TextNode, Loader, LPoint3f, LColor

class ActionCardPopup:
    def __init__(self, parent, position, options, texture, font_path=None, scale=0.8):
        """
        options: dict mapping option_key -> (label, callback)
        texture: path to your popup card PNG
        font_path: path to your Sierra-style .ttf
        scale: overall size of the card (fraction of screen)
        """
        self.options = options

        self.selected_index = 0
        self.text_nodes = []  # store the NodePaths for the option labels

        # 1) Draw the card background
        aspect = base.getAspectRatio()
        self.card = OnscreenImage(
            image=texture,
#            pos=(parent.getX(), parent.getY(), parent.getZ()),
            pos=position,
            scale=(scale * aspect, 1, scale),
            parent=parent
        )
        self.card.setTransparency(TransparencyAttrib.MAlpha)

        # 2) Load your pixel/serif font
        if font_path:
            self.font = loader.loadFont(font_path)

        # 3) Define clickable regions (normalized coords)
        #    Here we stack options vertically. Adjust y_start/dy to taste.
        count  = len(options)
        y_start = 0.3
        dy      = -0.6 / (count - 1) if count > 1 else 0
        self.regions = {}  # option_key -> (x1,x2,y1,y2)
        for idx, (key, (label, _cb)) in enumerate(options.items()):
            y = y_start + idx*dy
            x1, x2 = -0.4, 0.4
            y1, y2 = y - 0.07, y + 0.07
            self.regions[key] = (x1, x2, y1, y2)

            # 4) Draw the label text in middle of the region
            tn = TextNode(f"opt_{key}")
            if font_path:
                tn.setFont(self.font)
            tn.setText(label)
            tn.setAlign(TextNode.ACenter)
            tn.setTextColor(1,1,1,1)
            text_np = self.card.attachNewNode(tn)
            text_np.setScale(0.06)
            midx = (x1 + x2) / 2
            midy = (y1 + y2) / 2
            text_np.setPos(midx, 0, midy)
            self.text_nodes.append(text_np)

        self._update_highlight()

        # listen for keys
        base.accept("arrow_up",   self._move_selection, [-1])
        base.accept("arrow_down", self._move_selection, [1])
        base.accept("enter",      self._select_current)


    def _move_selection(self, delta):
        count = len(self.text_nodes)
        self.selected_index = (self.selected_index + delta) % count
        self._update_highlight()

    def _update_highlight(self):
        for idx, np in enumerate(self.text_nodes):
            if idx == self.selected_index:
                np.setColorScale(LColor(1, 1, 0, 1))  # yellow glow
            else:
                np.clearColorScale()

    def _select_current(self):
        key = list(self.options.keys())[self.selected_index]
        _, cb = self.options[key]
        cb()
        self.destroy()

    def destroy(self):
        # remove the card and all children the popup created
        if self.card:
            self.card.removeNode()
        # unhook arrows listener
        base.ignore("arrow_up")
        base.ignore("arrow_down")
#        base.ignore("enter")
