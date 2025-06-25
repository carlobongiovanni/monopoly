from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib, TextNode, Loader, LPoint3f

class ActionCardPopup:
    def __init__(self, parent, position, options, texture, font_path=None, scale=0.8):
        """
        options: dict mapping option_key -> (label, callback)
        texture: path to your popup card PNG
        font_path: path to your Sierra-style .ttf
        scale: overall size of the card (fraction of screen)
        """
        self.options = options

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

        print("Popup attached to:", self.card.getParent())
        print("Position:", self.card.getPos(render2d))  # or render2d if using aspect2d

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

        # 5) Listen for clicks
        base.accept("mouse1", self._on_click)

    def _on_click(self):
        if not base.mouseWatcherNode.hasMouse():
            return
        mx, my = base.mouseWatcherNode.getMouse()  # -1..+1 on both axes
        # check which region it falls into
        for key, (x1,x2,y1,y2) in self.regions.items():
            if x1 <= mx <= x2 and y1 <= my <= y2:
                # call the callback
                _, cb = self.options[key]
                cb()
                self.destroy()
                break

    def destroy(self):
        # remove the card and all children the popup created
        if self.card:
            self.card.removeNode()
        # unhook mouse listener
        base.ignore("mouse1")
