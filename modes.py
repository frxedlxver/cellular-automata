from neighbourhoods import Neighbourhood
from abc import ABC, abstractmethod
import numpy as np
from scipy.signal import convolve2d
from config import Settings as cfg


class Mode(ABC):

    def __init__(self, neighbourhood):
        self._neighbourhood = Neighbourhood.get_neighbourhood(neighbourhood)
        self.changed_cells = np.empty((0, 2), dtype=int)

    def neighbourhood(self):
        return self._neighbourhood

    @abstractmethod
    def update(self, current_data_grid):
        return current_data_grid

    def reset_changed_cells(self):
        self.changed_cells = np.empty((0, 2), dtype=int)

    def add_to_changed_cells(self, new_changes):
        self.changed_cells = np.unique(np.vstack([self.changed_cells, new_changes]), axis=0)

    @property
    def get_neighbourhood(self):
        return self._neighbourhood


class SandMode(Mode):

    def __init__(self):
        super().__init__(Neighbourhood.ExMoore)
        self.height, self.width = cfg.GRID_HEIGHT, cfg.GRID_WIDTH
        self._y_vel_map = np.zeros((self.height, self.width), dtype=int)
        self.random_directions = np.random.choice(a=[1, -1], size=self.height)
        self.rand_idx = 0
        self.max_rand_idx = self.height - 1
        self.gravity = cfg.SAND_GRAVITY

    def update(self, current_grid):
        new_data_grid = np.zeros_like(current_grid)
        new_y_vel_map = np.zeros_like(self._y_vel_map)

        # Use vectorized operations to find living cells
        # allows us to speed up processing by only checking cells with sand in them
        living_cells = np.argwhere(current_grid)

        # Sort living cells in zigzag order based on their x-coordinates
        # This removes the directional bias introduced by checking side-to-side
        living_cells = sorted(living_cells, key=lambda cell: (cell[0], cell[1] if cell[1] % 2 == 0 else -cell[1]))

        for y, x in living_cells:
            new_y, new_x = y, x  # Initialize new position as old position

            velocity = self._y_vel_map[y, x] - self.gravity  # Apply gravity

            step = 0
            while step < abs(velocity):
                can_move_down = not new_data_grid[new_y - 1, new_x]  # Move down if possible

                if new_y == 0 or (velocity == 0 and not can_move_down):
                    break
                else:
                    if (new_x == x and velocity < -2) or not can_move_down:  # Check diagonal movements
                        can_move_left = new_x > 0 and new_y > 0 and not new_data_grid[new_y - 1, new_x - 1]
                        can_move_right = new_x < cfg.GRID_WIDTH - 1 and new_y > 0 and not new_data_grid[
                            new_y - 1, new_x + 1]

                        if can_move_left and can_move_right:
                            new_x += self.random_directions[(y + self.rand_idx) % self.height]
                            new_y -= 1
                            step += 2
                        elif can_move_left:
                            new_x -= 1
                            new_y -= 1
                            step += 2
                        elif can_move_right:
                            new_x += 1
                            new_y -= 1
                            step += 2
                        else:
                            velocity = 0
                            break
                    else:
                        new_y -= 1
                        step += 1

                    self.rand_idx += 1
            # Update new grid and velocity map
            new_data_grid[new_y, new_x] = True
            new_y_vel_map[new_y, new_x] = max(velocity, cfg.SAND_MAX_Y_VEL)

        np.random.shuffle(self.random_directions)
        self.changed_cells = np.argwhere(current_grid != new_data_grid)
        self._y_vel_map = new_y_vel_map
        return new_data_grid


class ZebraMode(Mode):

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


class ExpandMode(Mode):

    def __init__(self):
        super().__init__(Neighbourhood.Moore)
        self.neighbour_threshold = 7
        self._kernel = np.array([
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1],
            [1, 1, 0, 1, 1],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1]])

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
        "Game of Life": (2, 3, 3),
        "Draw": (2, 6, 4),
        "Mold": (2, 4, 3),
        "Berghain": (2, 3, 0),
        "Berghain2": (1, 3, 1),

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
        neighbor_count = convolve2d(current_data_grid.astype(int), self._kernel, mode='same', boundary='fill',
                                    fillvalue=0)

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

        self._underpopulation_limit, self._overpopulation_limit, self._reproduction_requirement = self.Presets.get(
            preset_name)

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


class SmoothMode(Mode):

    def __init__(self):
        super().__init__(Neighbourhood.Moore)
        self.neighbour_threshold = 4
        self._kernel = np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]])

    def update(self, current_data_grid):
        # Apply convolution to count neighbors
        neighbor_count = convolve2d(current_data_grid, self._kernel, mode='same', boundary='fill', fillvalue=0)

        # Update the grid based on neighbor count
        new_data_grid = (neighbor_count > self.neighbour_threshold)

        self.changed_cells = np.argwhere(current_data_grid != new_data_grid)

        return new_data_grid
