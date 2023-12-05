from neighbourhoods import Neighbourhood
from enum import Enum
from abc import ABC, abstractmethod, abstractproperty
from config import Config
import numpy as np
from scipy.signal import convolve2d

class Mode(ABC):

    def __init__(self, neighbourhood):
        self._neighbourhood = Neighbourhood.get_neighbourhood(neighbourhood)
        self.changed_cells = None

    def neighbourhood(self):
        return self._neighbourhood
    
    @abstractmethod
    def update(self, current_data_grid):
        return current_data_grid


class SandMode(Mode):
    
    def __init__(self):
        super().__init__(Neighbourhood.ExMoore)
        self._velocity_map = np.zeros((Config.GRID_HEIGHT, Config.GRID_WIDTH), dtype=int)
        self.random_bools = np.random.choice(a=[False, True], size=10)
        self.rand_idx = 0

    def update(self, current_data_grid):
        width, height = Config.GRID_WIDTH, Config.GRID_HEIGHT
        new_data_grid = np.zeros_like(current_data_grid)
        new_velocity_map = np.zeros_like(current_data_grid)

        # Find the indices of all living cells
        living_cells= np.argwhere(current_data_grid)

        
        for y, x in living_cells:

                # Apply the negative velocity to move downwards
                new_x, new_y = x, y
                velocity = max(self._velocity_map[y][x] - 1, -15)

                if new_y > 0:
                    for step in range(abs(velocity)):
                        cell_below = new_data_grid[new_y - 1][new_x]
                        if new_y > 0 and not cell_below:
                            new_y -= 1  # Move down if the cell below is empty
                        else:
                            break

                    if cell_below:
                        # Check diagonal movement if direct down is blocked
                        move_down_left = new_x > 0 and new_y > 0 and not new_data_grid[new_y - 1][new_x - 1]
                        move_down_right = new_x < Config.GRID_WIDTH - 1 and new_y > 0 and not new_data_grid[new_y - 1][new_x + 1]

                        if move_down_left and not move_down_right:
                            new_x -= 1
                            new_y -= 1
                        elif move_down_right and not move_down_left:
                            new_x += 1
                            new_y -= 1
                        elif move_down_left and move_down_right:
                            if self.random_bools[(y + self.rand_idx) % 10]:
                                new_x -= 1
                            else:
                                new_x += 1
                            new_y -= 1

                new_data_grid[new_y][new_x] = True

                if new_y == 0 or y == 0 or cell_below:
                    velocity = min(velocity + 1, 0)
                else:
                    velocity -= 1
                
                new_velocity_map[new_y][new_x] = velocity

        self.changed_cells = np.argwhere(new_data_grid != current_data_grid)
        self._velocity_map = new_velocity_map
        return new_data_grid


class CellularAutomataMode(Mode):

    # dictionary to store preset values.
    # "preset name" : (overcrowding_limit, underpopulation_limit, reproduction_requirement) 
    Presets = {
        "Game of Life" : (2, 3, 3),
        "Draw" : (2, 6, 4),
        "Mold" : (2, 4, 3),
        "Berghain" : (2, 3, 0),
    }

    def __init__(self):
        super().__init__(Neighbourhood.Moore)
        self._current_preset_index = -1
        self.next_preset()
    
    def update(self, current_data_grid):

        # Define the kernel for counting neighbors
        kernel = np.array([[1, 1, 1], 
                            [1, 0, 1], 
                            [1, 1, 1]])

        # Apply convolution to count neighbors
        neighbor_count = convolve2d(current_data_grid.astype(int), kernel, mode='same', boundary='fill', fillvalue=0)

        # Apply rules
        born = (neighbor_count == self._reproduction_requirement) & ~current_data_grid
        survive = ((neighbor_count >= self._underpopulation_limit) & 
                   (neighbor_count <= self._overpopulation_limit) & 
                   current_data_grid)

        # Update grid based on rules
        new_grid = np.where(born | survive, 1, 0)

        
        # Find changed cells
        self.changed_cells = np.argwhere(new_grid != current_data_grid)

        return new_grid
    
    def load_preset(self, preset_name):
        if preset_name not in self.Presets:
            preset_name = "Game of Life"

        self._underpopulation_limit, self._overpopulation_limit, self._reproduction_requirement = self.Presets.get(preset_name)

    def next_preset(self):
        if self._current_preset_index >= len(list(self.Presets.keys())) or self._current_preset_index < 0:
            self._current_preset_index = 0
        
        next_key = list(self.Presets.keys())[self._current_preset_index]

        self.load_preset(next_key)

        self._current_preset_index += 1
    
    def save_preset(self, name):
        if len(name) == 0:
            name = "NewPreset"
        
        i = 0
        unique_name = name
        while unique_name in self.Presets:
            unique_name = f"{name}{i}"
            i += 1
            
        self.Presets[name] = (self._underpopulation_limit, self._overpopulation_limit, self._reproduction_requirement)