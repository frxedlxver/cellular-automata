from cell_state import CellState
from direction import Direction as dir
from config.input import Input

class Settings:
    SCREENSHOT_DIRECTORY = ".\\screenshots\\"

    SIMULATION_FRAME_RATE = 30
    SAND_FRAME_RATE = 30
    VISUAL_FRAME_RATE = 30

    DEFAULT_MODE = Input.CA_MODE

    # cells
    CELL_HEIGHT = 2
    CELL_WIDTH = 2

    CELL_STATES = [
        CellState('Alive'),
        CellState('Dead')
    ]

    # grid
    GRID_HEIGHT = 200
    GRID_WIDTH = 200
    GRID_SIZE = (GRID_HEIGHT, GRID_WIDTH)

    # visual grid
    VISUAL_GRID_HEIGHT = CELL_HEIGHT * GRID_HEIGHT
    VISUAL_GRID_WIDTH = CELL_WIDTH * GRID_WIDTH

    # window
    WINDOW_MARGIN = {
        dir.Top: 50,
        dir.Right: 50,
        dir.Bottom: 50,
        dir.Left: 50
    }

    WINDOW_HEIGHT = VISUAL_GRID_HEIGHT + WINDOW_MARGIN[dir.Top] + WINDOW_MARGIN[dir.Bottom]
    WINDOW_WIDTH = VISUAL_GRID_WIDTH + WINDOW_MARGIN[dir.Left] + WINDOW_MARGIN[dir.Right]
    INITIAL_LIFE_CHANCE = 0.2

    # sand mode
    SAND_GRAVITY = 1
    SAND_MAX_Y_VEL = -10
