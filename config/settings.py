from cell_state import CellState
from direction import Direction as dir


class Settings:
    SCREENSHOT_DIRECTORY = ".\\screenshots\\"

    SIMULATION_FRAME_RATE = 30
    SAND_FRAME_RATE = 30
    VISUAL_FRAME_RATE = 30

    # cells
    CELL_HEIGHT = 4
    CELL_WIDTH = 4
    CELL_STATES = [
        CellState('Alive', (120, 120, 30, 255)),
        CellState('Dead', (40, 40, 40, 255))
    ]

    # grid
    GRID_HEIGHT = 180
    GRID_WIDTH = 320
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
