from config.settings import Settings
from config.input import Input
import numpy as np
import modes

class CellDataController:
    def __init__(self):
        self.initialize_data_grid()

        self._modes = {
            Input.CA_MODE        : modes.CellularAutomataMode(),
            Input.SAND_MODE      : modes.SandMode(),
            Input.EXPAND_MODE    : modes.ExpandMode(),
            Input.ZEBRA_MODE     : modes.ZebraMode(),
            Input.TRAIL_MODE     : modes.SmoothMode()
        }

        self.set_mode(Input.CA_MODE)
        self._cells_changed_by_click = np.empty((0, 2), dtype=int)

        self._cached_mode = None
        
    
    def update(self):
        # update data grid every frame
        self._data_grid = self._mode.update(self._data_grid)

    def initialize_data_grid(self):
        self._data_grid = np.random.randint(0, 2,
                                            size=(Settings.GRID_HEIGHT, Settings.GRID_WIDTH))
        np.random.randint(0, 3)
        for y in range(Settings.GRID_HEIGHT):
            for x in range(Settings.GRID_WIDTH):
                # set cell as alive if random float falls between 0 and INITIAL_LIFE_CHANCE
                self._data_grid[y][x] = np.random.rand() < Settings.INITIAL_LIFE_CHANCE

    def set_mode(self, mode_key):
        self._mode = self._modes[mode_key]

    def set_temporary_mode(self, mode_key):
        # cache current mode
        self._cached_mode = self._mode

        self.set_mode(mode_key)

    def exit_temporary_mode(self):
        if self._cached_mode != None:
            self._mode = self._cached_mode
            
            # clear the cache
            self._cached_mode = None

    def next_ca_preset(self):
        self._modes[Input.CA_MODE].next_preset()

    def get_changed_cells(self):
        result = np.unique(np.vstack([self._mode.changed_cells, self._cells_changed_by_click]), axis=0)
        self._cells_changed_by_click = np.empty((0, 2), dtype=int)
        return result

    def state_at(self, y, x):
        return self._data_grid[y, x]

    def set_cell_states(self, cells, state):
        for y, x in cells:
            if self.in_grid(y, x):
                self._data_grid[y,x] = state
                self._cells_changed_by_click = np.vstack([self._cells_changed_by_click, [y, x]])
    
    def clear_screen(self):
        self._data_grid = np.zeros_like(self._data_grid, dtype=bool)
        self._mode.changed_cells = np.argwhere(self._data_grid == False)


    @staticmethod   
    def in_grid(y, x):
        0 <= y < Settings.GRID_HEIGHT and 0 <= x < Settings.GRID_WIDTH