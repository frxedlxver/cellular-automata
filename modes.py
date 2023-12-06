from neighbourhoods import Neighbourhood
from abc import ABC, abstractmethod
from config import Settings
import numpy as np
from scipy.signal import convolve2d
from config import Settings as cfg

class Mode(ABC):

    def __init__(self, neighbourhood):
        self._neighbourhood = Neighbourhood.get_neighbourhood(neighbourhood)
        self.changed_cells = np.empty((0,2), dtype=int)

    def neighbourhood(self):
        return self._neighbourhood
    
    @abstractmethod
    def update(self, current_data_grid):
        return current_data_grid
    
    def reset_changed_cells(self):
        self.changed_cells = np.empty((0,2), dtype=int)

    def add_to_changed_cells(self, new_changes):
        self.changed_cells = np.unique(np.vstack([self.changed_cells, new_changes]), axis=0)


class SandMode(Mode):
    
    def __init__(self):
        super().__init__(Neighbourhood.ExMoore)
        self.height, self.width = cfg.GRID_HEIGHT, cfg.GRID_WIDTH
        self._y_vel_map = np.zeros((self.height, self.width), dtype=int)
        self.random_bools = np.random.choice(a=[False, True], size=self.height)
        self.rand_idx = 0
        self.max_rand_idx = self.height - 1
        self.gravity = cfg.SAND_GRAVITY
        
        
    
    def update(self, current_grid):
        new_data_grid = np.zeros_like(current_grid)
        new_y_vel_map = np.zeros_like(self._y_vel_map)

        # Use vectorized operations to find living cells
        living_cells = np.argwhere(current_grid)
        
        for y, x in living_cells:


            # initialize new position as old position
            new_y, new_x = y, x

            # if at bottom, dont move down
            if y > 0:
                # can move down if no cell below, or cell below has velocity
                can_move_down = (not current_grid[y-1][x] or new_y_vel_map[y-1, x] > 0)
                
                if can_move_down:
                    # get velocity of current cell and apply gravity
                    velocity = self._y_vel_map[y, x] - self.gravity
                    # check each position in range of velocity, move to furthest open tile
                    for step in range(abs(velocity)):
                        if new_y > 0 and not new_data_grid[new_y - 1][new_x]:
                            new_y -= 1  # Move down if the cell below is empty

                    # slow down if movement is obstructed
                    if new_y > y - velocity:
                        velocity = y - new_y
                
                else: # Check diagonal movement if direct down is blocked
                    move_down_left = new_x > 0 and new_y > 0 and not new_data_grid[new_y - 1][new_x - 1]
                    move_down_right = new_x < cfg.GRID_WIDTH - 1 and new_y > 0 and not new_data_grid[new_y - 1][new_x + 1]

                    if move_down_left and not move_down_right:
                        new_x -= 1
                        new_y -= 1
                    elif move_down_right and not move_down_left:
                        new_x += 1
                        new_y -= 1
                    elif move_down_left and move_down_right:
                        if self.random_bools[(y + self.rand_idx) % self.max_rand_idx]:
                            new_x -= 1
                        else:
                            new_x += 1
                        new_y -= 1
                        self.rand_idx += 1
            else:
                velocity = 0

            
            # Update new grid and velocity map
            new_data_grid[new_y, new_x] = True
            new_y_vel_map[new_y, new_x] = max(velocity, cfg.SAND_MAX_Y_VEL)

        self.changed_cells = np.argwhere(current_grid != new_data_grid)
        self._y_vel_map = new_y_vel_map
        return new_data_grid
    

class WaterMode(Mode):

   
    def __init__(self):
        super().__init__(Neighbourhood.ExVon)
        self.neighbour_threshold = 4

    def update(self, current_data_grid):
        # Define a 3x3 kernel for Moore neighborhood
        kernel = self._neighbourhood

        # Apply convolution to count neighbors
        neighbor_count = convolve2d(current_data_grid, kernel, mode='same', boundary='fill', fillvalue=0)

        # Update the grid based on neighbor count
        new_data_grid = (neighbor_count > self.neighbour_threshold)

        self.changed_cells = np.argwhere(current_data_grid != new_data_grid)

        return new_data_grid


class TrailMode(Mode):

   
    def __init__(self):
        super().__init__(Neighbourhood.Moore)
        self.neighbour_threshold = 4
        self._kernel = np.array([[1, 1, 1], 
                            [1, 0, 1], 
                            [1, 1, 1]])

    def update(self, current_data_grid):

        # Apply convolution to count neighbors
        neighbor_count = convolve2d(current_data_grid, self._kernel, mode='same', boundary='fill', fillvalue=0)

        # Update the grid based on neighbor count
        new_data_grid = (neighbor_count > self.neighbour_threshold)

        self.changed_cells = np.argwhere(current_data_grid != new_data_grid)

        return new_data_grid



class CellularAutomataMode(Mode):

    # dictionary to store preset values.
    # "preset name" : (overcrowding_limit, underpopulation_limit, reproduction_requirement) 
    Presets = {
        "Game of Life" : (2, 3, 3),
        "Draw" : (2, 6, 4),
        "Mold" : (2, 4, 3),
        "Berghain" : (2, 3, 0),
        "Berghain2" : (1, 3, 1),

    }

    def __init__(self):
        super().__init__(Neighbourhood.Moore)
        self._current_preset_index = -1
        self.next_preset()
        self._kernel = np.array([[1, 1, 1], 
                    [1, 0, 1], 
                    [1, 1, 1]])
    
    def update(self, current_data_grid):

        # Apply convolution to count neighbors
        neighbor_count = convolve2d(current_data_grid.astype(int), self._kernel, mode='same', boundary='fill', fillvalue=0)

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