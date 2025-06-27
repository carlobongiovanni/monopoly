# /// script
# dependencies = [
#   "panda3d",
# ]
# ///

import sys
import random
import logging
import asyncio
import os
from panda3d.core import CardMaker, ScissorAttrib, TextNode, LColor, TexGenAttrib, TextureStage, loadPrcFileData, LPoint3f
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import (
    DirectFrame, DirectLabel, DirectEntry, DirectButton
)
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.interval.IntervalGlobal import Sequence, Wait, Func, LerpPosInterval
from direct.fsm.FSM import FSM
from action_card_popup import ActionCardPopup

DEBUG = os.environ.get("DEBUG")

# tell Panda to make a 1024×600 window, windowed (not fullscreen)
loadPrcFileData("", """
    win-size 1024 600
    fullscreen 0
    show-frame-rate-meter 0
""")

logging.basicConfig(level=logging.INFO)

class Monopoly2d(ShowBase, FSM):
    def __init__(self):
        super().__init__()
        FSM.__init__(self, "GameFSM")

        logging.info("Entering init")

        # initialize variables
        self.count_monopoly_cards = 20        # total rectangles per lane
        self.visible_slots  = 2         # how many fit on screen at once
        self.card_height    = 1
        self.scroll_speed   = 1         # slots per second when holding key
        # this is played by the real player
        self.player1_name   = "Alice"
        self.content_pane_top = 0.8
        self.content_pane_bottom = -0.6

        self.left_lane = None
        self.right_lane = None
        self.left_content  = None
        self.right_content = None
        self.monopoly_map = None
        self.rects_left  = []
        self.rects_right = []
        self.index1       = 0   # player1 on right
        self.index2       = 0   # player2 on left
        self.guide_text = None
        self.inventory_left_text = None
        self.inventory_right_text = None

        # dices
        self.dice = []
        self.dice_textures = None
        self.value_dice_1 = 1
        self.value_dice_2 = 1

        # placeholders for GUI widgets
        self.menu_frame    = None
        self.count_entry   = None
        self.p1_entry      = None
        self.start_button  = None

        # which actor is in charge of action now
        self.actor = "human"

        # inventory storage
        self.human_inventory = {}
        self.bot_inventory = {}

        # powers
        self.powers = ["cheaper_upgrades", "bonus"]
        # 10% discount
        self.power_cheaper_upgrades = 10
        # 30 $
        self.power_bonus = 30

        # popup
        self.popup = None

        # tracks how many turns have passed
        self.turn = 0

        # debug will to skip setup - set debug as env variable
        self.debug = bool(DEBUG)

        if self.debug:
            logging.info("Debug ACTIVE")
            self.accept("escape", sys.exit)
            self._on_start_pressed()
        else:
            logging.info("Debug UNACTIVE")
            self.request("Idle")

    def _debug_node(self, node):
        """helper to understand WTF I did"""
        self.aspect2d.ls()
        print("State on parent:", node.getState())
        print(node.getParent().getName())

    def _build_game(self):
        """draws the game interface and the cards"""
        bg_left  = self.create_background(
            "bg_left", 
            self.aspect2d,
            -self.getAspectRatio(),
            0.0,
            self.content_pane_bottom,
            self.content_pane_top,
            (0.1, 0.1, 0.5, 1)
        )

        bg_inventory_left  = self.create_background(
            "bg_inventory_left", 
            self.aspect2d,
            -self.getAspectRatio(),
            0.0,
            -1,
            self.content_pane_bottom,
            (0, 0, 0, 1)
        )
        bg_inventory_left.clearColor()

        bg_right = self.create_background(
            "bg_right", 
            self.aspect2d,
            0.0,
            self.getAspectRatio(),
            self.content_pane_bottom,
            self.content_pane_top,
            (0.5, 0.1, 0.1, 1)
        )

        bg_inventory_right  = self.create_background(
            "bg_inventory_right", 
            self.aspect2d,
            0.0,
            self.getAspectRatio(),
            -1,
            self.content_pane_bottom,
            (0, 0, 0, 1)
        )
        bg_inventory_right.clearColor()

        bg_scoring = self.create_background(
            "bg_scoring", 
            self.aspect2d,
            -self.getAspectRatio(),
            self.getAspectRatio(),
            self.content_pane_top,
            1,
            (0, 0, 0, 1)
        )

        # Create a middle divider
        divider = CardMaker("divider")
        divider.setFrame(-0.01, 0.01, -1, self.content_pane_top)
        divider_node = self.aspect2d.attachNewNode(divider.generate())
        divider_node.setColor(0, 0, 0, 1)
        divider_node.setX(0)

        # add dices system
        self.setup_dices(bg_scoring)

        # textnode for guiding user
        self.guide_text = OnscreenText(
            text="",
            pos=(0, .87),  # Positioning above the rectangle
            scale=.1,
            fg=(0, 0, 0, 1),
            parent=bg_scoring,  # Attach to the rectangle
            align=TextNode.ACenter
        )

        # textnode for inventory left
        self.inventory_left_text = OnscreenText(
            text="INVENTORY LEFT PLAYER",
            pos=(-self.getAspectRatio() + .05, self.content_pane_bottom - 0.1),
            scale=.1,
            fg=(0, 0, 0, 1),
            parent=bg_inventory_left,  # Attach to the rectangle
            align=TextNode.ALeft
        )

        # textnode for inventory right
        self.inventory_right_text = OnscreenText(
            text="INVENTORY RIGHT PLAYER",
            pos=(.05, self.content_pane_bottom - 0.1),
            scale=.1,
            fg=(0, 0, 0, 1),
            parent=bg_inventory_right,  # Attach to the rectangle
            align=TextNode.ALeft
        )

        # generate the map of the game
        self.monopoly_map = self.generate_map()

        # populate the lanes
        self.left_lane  = bg_left.attachNewNode("left_lane")
        self.right_lane = bg_right.attachNewNode("right_lane")

        self.left_lane.setAttrib(
            ScissorAttrib.make(0.0,   # left edge of scissor (0% of win)
                               0.5,   # right edge (50%)
                               0.0,   # bottom  (0%)
                               1.0)   # top     (100%)
        )

        # and the right lane to the right half
        self.right_lane.setAttrib(
            ScissorAttrib.make(0.5,   # 50% of win
                               1.0,   # 100% of win
                               0.0,
                               1.0)
        )

        self.left_lane.setScale(0.5, 1, 1)
        self.left_lane.setX(-0.5)
        self.right_lane.setScale(0.5, 1, 1)
        self.right_lane.setX(0.5)

        # each lane gets a “content” NodePath under which we create ALL cards
        self.left_content  = self.left_lane.attachNewNode("left_content")

        self.right_content = self.right_lane.attachNewNode("right_content")

        # compute the slot width so exactly visible_slots fill –1→+1
        width = 2.0 / self.visible_slots

        self.rects_left  = []
        self.rects_right = []
        for i, v in enumerate(self.monopoly_map):
            # left
            cm = CardMaker(f"L{i}")
            cm.setFrame(-width/2, +width/2, -self.card_height/2, +self.card_height/2)
            node = self.left_content.attachNewNode(cm.generate())
            node.setX(-self.getAspectRatio() - 0.5 + width/2 + i*width)
            node.setZ(0.1)
            node.setColor(self.generate_color_from_map(v))
            text = OnscreenText(
                text=str(v),  # Rectangle number
                pos=(0, self.card_height/2 - 0.1),  # Positioning above the rectangle
                scale=0.1,
                fg=(1, 1, 1, 1),  # White text
                parent=node,  # Attach to the rectangle
                align=TextNode.ACenter
            )
            self.rects_left.append(node)

            # right
            cm2 = CardMaker(f"R{i}")
            cm2.setFrame(-width/2, +width/2, -self.card_height/2, +self.card_height/2)
            node2 = self.right_content.attachNewNode(cm2.generate())
            node2.setX(-0.75 + width/2 + i*width)
            node2.setZ(0.1)
            node2.setColor(self.generate_color_from_map(v))
            text2 = OnscreenText(
                text=str(v),  # Rectangle number
                pos=(0, self.card_height/2 - 0.1),  # Positioning above the rectangle
                scale=0.1,
                fg=(1, 1, 1, 1),  # White text
                parent=node2,  # Attach to the rectangle
                align=TextNode.ACenter
            )
            self.rects_right.append(node2)

        # prepares inventory
        self.prepare_inventory()
        self.draw_inventory()

        self.accept("arrow_left",  self.move1, [-1])
        self.accept("arrow_right", self.move1, [+1])
        self.accept("a",  self.move2, [-1])
        self.accept("d", self.move2, [+1])

    def draw_inventory(self):
        """draws the inventory adding initial power and gold"""
        human_gold = self.human_inventory.get("money", 0)
        bot_gold = self.human_inventory.get("money", 0)
        human_power = self.human_inventory.get("power", "")
        bot_power = self.bot_inventory.get("power", "")
        human_message = f"Gold: {human_gold} $\nPower: {human_power}"
        bot_message = f"Gold: {bot_gold} $\nPower: {bot_power}"
        self.update_inventory("human", human_message)
        self.update_inventory("bot", bot_message)

    def update_inventory(self, target, message):
        """updates the inventory"""
        if target == "bot":
            self.inventory_left_text.setText(message)
        elif target == "human":
            self.inventory_right_text.setText(message)

    def prepare_inventory(self):
        """inventory is prepared with starting money and random powers"""
        # set power
        powers = self.powers
        human_power = random.choice(powers)
        powers.remove(human_power)
        bot_power = powers[0]

        # set starting money
        starting_money = 100
        self.human_inventory = {
            "power": human_power,
            "money": starting_money,
            "cards": [{}]
        }
        self.bot_inventory = {
            "power": bot_power,
            "money": starting_money,
            "cards": [{}]
        }


    def setup_dices(self, nodename):
        """adds the dices to the bg_scoring"""
        # clears the parent color or the texture won't show!
        nodename.clearColor()
        # 1) Load the six face‐textures once
        self.dice_textures = [
            self.loader.loadTexture(f"assets/Dice-{i}.png")
            for i in range(1,7)
        ]

        # 2) Create two dice quads in aspect2d
        self.dice = []
        positions = [1, 1.2]    # X positions for Die1 / Die2
        size      = 0.07            # half-width and half-height of each die

        for i, x in enumerate(positions):
            cm = CardMaker(f"die{i+1}")
            cm.setFrame(-size, size, -size, size)
            node = nodename.attachNewNode(cm.generate())
            node.setPos(x, 0, 0.9)
            # start with face “1”
            node.setTexture(self.dice_textures[0], 1)
            self.dice.append(node)


    def enterIdle(self):
        """Show the configuration menu."""
        logging.info("Idle State aka selection menu entered")
        self.menu_frame = DirectFrame(
            frameColor=(0,0,0,0.7),
            frameSize=(-0.8,0.8,-0.6,0.6),
            pos=(0,0,0)
        )

        # 2) Label + DirectEntry for card count
        DirectLabel(
            text="Number of Cards:",
            parent=self.menu_frame,
            pos=(-0.6,0,0.3),
            scale=0.07,
            text_align=TextNode.ALeft
        )
        self.count_entry = DirectEntry(
            parent=self.menu_frame,
            text=str(self.count_monopoly_cards),
            initialText="",
            numLines=1,
            pos=(0.1,0,0.3),
            scale=0.07,
            width=4,
            command=self._on_count_changed
        )

        # 3) Player 1 name
        DirectLabel(
            text="Player 1 Name:",
            parent=self.menu_frame,
            pos=(-0.6,0,0.1),
            scale=0.07,
            text_align=TextNode.ALeft
        )
        self.p1_entry = DirectEntry(
            parent=self.menu_frame,
            text=self.player1_name,
            numLines=1,
            pos=(0.1,0,0.1),
            scale=0.07,
            width=8,
            command=self._on_p1_name_changed
        )

        # 5) Start Game button
        self.start_button = DirectButton(
            text="Start Game",
            parent=self.menu_frame,
            pos=(0,0,-0.4),
            scale=0.08,
            command=self._on_start_pressed
        )

        # allow escape to quit
        self.accept("escape", sys.exit)

    def exitIdle(self):
        """Tear down the menu widgets."""
        logging.info("exit Idle")

        for w in (self.count_entry, self.p1_entry, self.start_button, self.menu_frame):
            if w:
                w.destroy()
        self.menu_frame   = None
        self.count_entry  = None
        self.p1_entry     = None
        self.start_button = None
#        self.ignore("escape")


    # ──── MENU CALLBACKS ────
    def _on_count_changed(self, text):
        try:
            val = int(text)
            self.count_monopoly_cards = max(1, val)
        except ValueError:
            pass  # ignore bad input

    def _on_p1_name_changed(self, text):
        self.player1_name = text or "Player1"

    def _on_start_pressed(self):
        """User hit Start—build the game boards, then begin P1’s turn."""
        self._build_game()
        self.request("PlayGame")

    def update_guide_text(self, role, target=None):
        """displays the message in the bg_scoring according to the game state"""
        message = "error"
        
        if self.actor == "human":
            if role == "start":
                message = "Press enter to play..."
            elif role == "dice_result":
                message = f"you rolled {self.value_dice_1} and {self.value_dice_2}, that makes {self.value_dice_1+self.value_dice_2}"
        elif self.actor == "bot":
            if role == "start":
                message = "Now it's my turn! let me think..."
            elif role == "dice_result":
                message = f"What? Only {self.value_dice_1} and {self.value_dice_2}? You cheater.."

        if role == "loss":
            if target == "human":
                message = "You lost! Fancy a new game?"
            elif target == "bot":
                message = "I lost! It never happened in my life!"

        logging.info(f"{self.actor} says: {message}")

        self.guide_text.setText(message)

    def enterPlayGame(self):
        """enters the game
        """
        logging.info(f"enter PlayGame for {self.actor}")
        self.update_guide_text(role="start")

        self.turn += 1

        if self.debug:
            logging.info("Debug Jump to RollDice")
            self.taskMgr.doMethodLater(
                0,
                self.enterRollDice,
                "humanRollNow"
            )

        self.check_victory()
        self.check_powers()

        if self.actor == "human":
            self.accept("enter", self.request, ["RollDice"])
        elif self.actor == "bot":
            self.taskMgr.doMethodLater(
                0,
                self.enterRollDice,
                "aiRollNow"
            )

    def check_powers(self):
        """We check powers to know if we need to update inventory"""
        logging.info("Check Powers to update inventory")
        if self.actor == "human":
            human_power = self.human_inventory.get("power", "")
            if human_power == "bonus":
                human_gold = self.human_inventory.get("money", 0)
                human_gold += self.power_bonus
                self.human_inventory["money"] = human_gold

                human_message = f"Gold: {self.human_inventory.get("money", 0)} $\nPower: {human_power}"
                self.update_inventory("human", human_message)

        if self.actor == "bot":
            bot_power = self.bot_inventory.get("power", "")
            if bot_power == "bonus":
                bot_gold = self.bot_inventory.get("money", 0)
                bot_gold += self.power_bonus
                self.bot_inventory["money"] = bot_gold

                bot_message = f"Gold: {self.bot_inventory.get("money", 0)} $\nPower: {bot_power}"
                self.update_inventory("bot", bot_message)

        logging.info("End check Powers to update inventory")


    def check_victory(self):
        """Victory is: 
            One of the players has no money and no properties
            One of the players has completed a mission"""
        human_gold = self.human_inventory.get("money", 0)
        bot_gold = self.bot_inventory.get("money", 0)

        logging.info("Human gold is: %s, Bot gold is: %s", human_gold, bot_gold)

        if human_gold <= 0:
            self.update_guide_text(role="loss", target="human")
            self.game_over(target="human")

        if bot_gold <= 0:
            self.update_guide_text(role="loss", target="bot")
            self.game_over(target="bot")

        logging.info("Game continues... we're at turn %d", self.turn)

    def game_over(self, target):
        """exit"""
        logging.info("%s lost the game", target)

    def enterRollDice(self, task=None):
        logging.info("Rolling dice as %s", self.actor)

        # no more enter accepted or it breaks the flow
#        self.ignore("enter")

        # pick final results
        self.value_dice_1 = random.randint(1,6)
        self.value_dice_2 = random.randint(1,6)

        # build an animation Sequence
        seq = Sequence()
        # flash random faces ~20 times at 0.05 s per flash (~1 s total)
        for _ in range(20):
            f1 = random.randint(1,6)
            f2 = random.randint(1,6)
            seq.append(Func(self._set_faces, f1, f2))
            seq.append(Wait(0.05))
        # finally show the real roll
        seq.append(Func(self._set_faces, self.value_dice_1, self.value_dice_2))
        seq.start()
        self.taskMgr.doMethodLater(
            seq.getDuration(),
            self._finish_roll_task,
            "finishRoll"
        )

    def _finish_roll_task(self, task):
        logging.info(f"Transition to {task}")
        self.request("MovePlayer")
        return Task.done

    def enterMovePlayer(self):
        logging.info(f"Entered PlayerMove as {self.actor}")
        self.update_guide_text(role="dice_result")

        delta = self.value_dice_1 + self.value_dice_2
        self.smooth_variant_move1(delta=delta)


    def _gotoPlayGame(self, task):
        self.request("PlayGame")
        return Task.done

    def exitMovePlayer(self):
        """switch actor"""

        if self.actor == "human":
            self.actor = "bot"
        else:
            self.actor = "human"


    ### end FSM ###

    def _set_faces(self, f1, f2):
        """Helper to set both dice’s textures to faces f1 and f2."""
        self.dice[0].setTexture(self.dice_textures[f1-1], 1)
        self.dice[1].setTexture(self.dice_textures[f2-1], 1)

    def generate_color_from_map(self, position):
        # Possible elements for contiguous blocks
        block_elements = ["Road", "Street", "Castle", "Palace", "Corner"]
        block_element_titles = ["Windsor", "Versailles", "Edinburgh", "Regent", "Victoria", "Kensington", "Balmoral", "Trafalgar", "Piccadilly", "Lancaster", "Dover", "Hampton", "York", "Nottingham"]

        # Elements that follow a contiguous block
        special_elements = ["station", "facility", "prison", "hospital", "museum", "hotel", "shop"]

        if position in special_elements:
            return LColor(.82, .91, .86, 1)
        
        return LColor(.69, .69, .69, 1)

    def generate_map(self):
        # Possible elements for contiguous blocks
        block_elements = ["Road", "Street", "Castle", "Palace", "Corner"]
        block_element_titles = ["Windsor", "Versailles", "Edinburgh", "Regent", "Victoria", "Kensington", "Balmoral", "Trafalgar", "Piccadilly", "Lancaster", "Dover", "Hampton", "York", "Nottingham"]

        # Elements that follow a contiguous block
        special_elements = ["station", "facility", "prison", "hospital", "museum", "hotel", "shop"]

        result = ["start"]
        while len(result) < (self.count_monopoly_cards - 1):
            # Create a contiguous block of 2 or 3 identical items
            block_size = random.choice([2, 3])
            for _ in range(block_size):
                block_element = random.choice(block_elements)
                block_element_title = random.choice(block_element_titles)
                block_name = f"{block_element} {block_element_title}"
                result.append(block_name)

            # Ensure we don't exceed the limit
            if len(result) >= self.count_monopoly_cards:
                break

            # Add a special element
            result.append(random.choice(special_elements))

        # close the list
        result.append("end")

        return result

    def create_background(self, nodename, parent, left, right, bottom, top, color):
        """Creates a background that spans the given horizontal range."""
        cm = CardMaker(nodename)
        cm.setFrame(left, right, bottom, top)  # Covers entire height (-1 to 1)
        bg = parent.attachNewNode(cm.generate())
        bg.setColor(*color)  # Apply color
        return bg

    def move1(self, delta):
        # update only player 1’s index & immediately re‐scroll only the right side
        self.index1 = (self.index1 + delta) % self.count_monopoly_cards
        self._update_right_view()

    def move2(self, delta):
        # update only player 2’s index & immediately re‐scroll only the left side
        self.index2 = (self.index2 + delta) % self.count_monopoly_cards
        self._update_left_view()

    def _update_right_view(self):
        half = self.visible_slots//2
        selected_visible_index = int(round(self.index1))
        start1 = min( max(selected_visible_index-half, 0), self.count_monopoly_cards-self.visible_slots )
        self.right_content.setX( -start1 * (2.0/self.visible_slots) )
        # refresh highlight
        for r in self.rects_right: r.setScale(1,1,1)
        self.rects_right[selected_visible_index].setScale(1.2,1,1.2)

    def _update_left_view(self):
        # same as above but for left_content and rects_left
        half = self.visible_slots//2
        selected_visible_index   = int(round(self.index2))
        start2 = min( max(selected_visible_index-half, 0), self.count_monopoly_cards-self.visible_slots )
        self.left_content.setX( -start2 * (2.0/self.visible_slots) )
        for r in self.rects_left: r.setScale(1,1,1)
        self.rects_left[selected_visible_index].setScale(1.2,1,1.2)

    def smooth_variant_move1(self, delta):
        # deregister enter as we need it inside the popup
#        self.ignore("enter")

        # compute old & new indices
        selected_node_path = None
        selected_card = None
        card_position = None

        if self.actor == "human":
            old_index = self.index1
            new_index = (old_index + delta) % self.count_monopoly_cards
            self.index1 = new_index

            selected_node_path = self.right_content

            card_np = selected_node_path.find(f"**/R{new_index}")
            if not card_np.isEmpty():
                selected_card = card_np

        elif self.actor == "bot":
            old_index = self.index2
            new_index = (old_index + delta) % self.count_monopoly_cards
            self.index2 = new_index

            selected_node_path = self.left_content

            card_np = selected_node_path.find(f"**/L{new_index}")
            if not card_np.isEmpty():
                selected_card = card_np

        card_position = selected_card.getPos()

        # figure out the scroll‐offset before & after, exactly as in _update_right_view()
        half   = self.visible_slots // 2
        width  = 2.0 / self.visible_slots
        start_old = min(max(old_index - half, 0), self.count_monopoly_cards - self.visible_slots)
        start_new = min(max(new_index - half, 0), self.count_monopoly_cards - self.visible_slots)
        x_old = -start_old * width
        x_new = -start_new * width

        # build a 0.5s slide from x_old→x_new, then re‐highlight the cards
        slide = LerpPosInterval(
            nodePath = selected_node_path,
            duration = 0.9,               # tweak for faster/slower
            pos      = (x_new, 0, 0),
            startPos = (x_old, 0, 0),
            blendType= 'easeInOut'        # optional smoothing
        )
        highlight = Func(self._highlight_card)
        popup = Func(self._play_popup, selected_node_path, card_position)

        # play them in order
        Sequence(slide, popup, highlight).start()

    def attempt_buy(self):
        print("Attempting to buy")
        self._close_popup_and_continue()

    def pay_rent(self):
        print("Paying rent")
        self._close_popup_and_continue()

    def start_auction(self):
        print("Starting auction")
        self._close_popup_and_continue()

    def skip_turn(self):
        print("Skipping turn")
        self._close_popup_and_continue()

    def _play_popup(self, selected_node_path, card_position):
        """Plays the popup animation"""
        def buy_cb():  self.attempt_buy()
        def rent_cb(): self.pay_rent()
        def auc_cb():  self.start_auction()
        def skip_cb():  self.skip_turn()

        self.popup = ActionCardPopup(
            parent=selected_node_path,
            position=card_position,
            options={
                "buy":   ("Buy Property", buy_cb),
                "rent":  ("Pay Rent",   rent_cb),
                "auction":("Auction",   auc_cb),
                "pass":  ("Skip",       skip_cb),
            },
            texture="assets/monopoly_panel.png",
    #        font_path="assets/fonts/sierras_font.ttf",
            scale=0.7
        )

    def _close_popup_and_continue(self):
        # destroy the popup if it hasn't already
        if hasattr(self, 'popup') and self.popup:
            self.popup.destroy()
            self.popup = None

        # now go on to the next phase of your game:
        self._gotoPlayGame(task=None)

    def _highlight_card(self):
        """highlight logic"""
        half = self.visible_slots//2

        if self.actor == "human":
            selected_visible_index = int(round(self.index1))
            # re‐position content in case of clamp at edges
            start1 = min(max(selected_visible_index-half, 0), self.count_monopoly_cards-self.visible_slots)

            self.right_content.setX(-start1*(2.0/self.visible_slots))
            # rescale cards
            for r in self.rects_right:
                r.setScale(1,1,1)
            self.rects_right[selected_visible_index].setScale(1.2,1,1.2)
        else:
            selected_visible_index = int(round(self.index2))
            # re‐position content in case of clamp at edges
            start2 = min(max(selected_visible_index-half, 0), self.count_monopoly_cards-self.visible_slots)

            self.left_content.setX(-start2*(2.0/self.visible_slots))
            # rescale cards
            for r in self.rects_left:
                r.setScale(1,1,1)
            self.rects_left[selected_visible_index].setScale(1.2,1,1.2)

async def main():
    app = Monopoly2d()
    app.run()

if __name__=="__main__":
    asyncio.run( main() ) # this is asyncronously running main.
