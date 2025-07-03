from direct.showbase.DirectObject import DirectObject
import sys

class SettingsPage(DirectObject):
    def __init__(self, base, on_start_game):
        super().__init__()
        self.base = base
        self.on_start_game = on_start_game
        print("SettingsPage init - press enter again")
        # Example: user sets config, then presses Enter
        self.accept("enter", self.start_game)
        self.accept("escape", sys.exit)

        # You can add sliders, buttons, etc. here

    def start_game(self):
        print("Starting game from settings...")
        self.cleanup()
        self.on_start_game()

    def cleanup(self):
        self.ignoreAll()
        # Remove any created UI nodes if needed
