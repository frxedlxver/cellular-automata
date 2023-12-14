from pyglet.window import key

class Controls:
    # CELLULAR AUTOMATA MODE ONLY
    NEXT_PRESET = key.P
    SMOOTH = key.RSHIFT

    # ALL MODES
    CLEAR_SCREEN = key.BACKSPACE
    TOGGLE_PAUSE = key.SPACE
    ADVANCE_FRAME = key.ENTER
    SCREENSHOT = key.S
    MOD_KEY = key.MOD_CTRL

    # MODE SELECTION
    CA_MODE = key._1
    SAND_MODE = key._2
    ZEBRA_MODE = key._3
    EXPAND_MODE = key._4
    TRAIL_MODE = key._5

    # COLORS
    TOGGLE_COLOR_ROTATION = key.C
    TOGGLE_BACKGROUND_COLOR_ROTATION = key.B