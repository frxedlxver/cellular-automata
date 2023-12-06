import numpy as np
import pyglet
from pyglet.window import mouse as mouse
from config import Settings
from config import Controls
from direction import Direction as dir
import modes

class CellularAutomataWindow(pyglet.window.Window):

    def __init__(self):
        super().__init__()
        
        # cached settings
        self.width = Settings.WINDOW_WIDTH
        self.height = Settings.WINDOW_HEIGHT
        self._grid_size = (Settings.GRID_WIDTH, Settings.GRID_HEIGHT)
        self._frames_between_visual_updates = 3
        self._current_frame_in_cycle = 0
        self._alive_color = Settings.CELL_STATES[0].color
        self._dead_color = Settings.CELL_STATES[1].color

        # pyglet
        self._batch = pyglet.graphics.Batch()
        
        # flags
        self.mouse_held = False
        self._paused = False
        self._clear_screen_pressed = False
        
        # modes
        self._modes = {
            'CA'    : modes.CellularAutomataMode(),
            'SAND'  : modes.SandMode(),
            'TRAIL' : modes.TrailMode(),
            'WATER' : modes.WaterMode()
        }
        self._mode = self._modes['CA']
        self._neighbourhood = self._mode.neighbourhood()

        # grid
        self.initialize_data_grid()
        self.initialize_visual_grid()
        self.velocity_map = {}

        # array for tracking cells changed by click, used in updating visual grid
        self.click_changed_cells = np.empty((0, 2), dtype=int)

    
    def update(self, dt):
        self.update_data()
        if self._clear_screen_pressed:
            self.clear_screen()
            self._clear_screen_pressed = False
        self.update_visuals()

    def update_data(self):
        # update data grid every frame
        self._data_grid = self._mode.update(self._data_grid)

    def update_visuals(self):
        changed_cells = np.unique(np.vstack([self._mode.changed_cells, self.click_changed_cells]), axis=0)

        if changed_cells.size > 0:
            # Update only the cells in the changed_cells set
            for y, x in changed_cells:
                self._visual_grid[y, x].color = self._alive_color if self._data_grid[y,x] else self._dead_color

        # Reset the click changes after updating
        self.click_changed_cells = np.empty((0, 2), dtype=int)


    def initialize_data_grid(self):
        self._data_grid = np.random.randint(0, len(Settings.CELL_STATES), size=self._grid_size)
        np.random.randint(0, 3)
        for y in range(Settings.GRID_HEIGHT):
            for x in range(Settings.GRID_WIDTH):
                # set cell as alive if random float falls between 0 and INITIAL_LIFE_CHANCE
                self._data_grid[y][x] = np.random.rand() < Settings.INITIAL_LIFE_CHANCE


    def initialize_visual_grid(self):
        self._visual_grid = np.empty((Settings.GRID_HEIGHT, Settings.GRID_WIDTH), dtype=object)

        adjusted_y_values = np.arange(stop=Settings.VISUAL_GRID_HEIGHT + Settings.CELL_HEIGHT, step=Settings.CELL_HEIGHT) + Settings.WINDOW_MARGIN[dir.Top]
        adjusted_x_values = np.arange(stop=Settings.VISUAL_GRID_WIDTH + Settings.CELL_WIDTH, step=Settings.CELL_WIDTH) + Settings.WINDOW_MARGIN[dir.Left]
        
        for y in range(Settings.GRID_HEIGHT):
            y_pos_in_window = adjusted_y_values[y]
            for x in range(Settings.GRID_WIDTH):
                x_pos_in_window = adjusted_x_values[x]
                cell_state = self._data_grid[y, x]
                color = self._alive_color if cell_state else self._dead_color
                cell = pyglet.shapes.Rectangle(x=x_pos_in_window, y=y_pos_in_window, 
                                               width=Settings.CELL_WIDTH, height=Settings.CELL_HEIGHT, 
                                               color=color, batch=self._batch)
                self._visual_grid[y][x] = cell


    def on_draw(self):
        self.clear()
        self._batch.draw()


    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse_held = True
        self.update_cached_mouse_position(x, y)
 
        # Unschedule any existing task before scheduling a new one
        pyglet.clock.unschedule(self.apply_click_effect)

        # Determine the new cell state based on the button pressed
        new_cell_state = button == mouse.LEFT
        pyglet.clock.schedule_interval(self.apply_click_effect, 1/Settings.SIMULATION_FRAME_RATE, new_cell_state)


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.mouse_held:
            if (abs(self.current_mouse_x - x) >= Settings.CELL_WIDTH or abs(self.current_mouse_y - y) >= Settings.CELL_HEIGHT):
                self.update_cached_mouse_position(x, y)


    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse_held = False
        pyglet.clock.unschedule(self.apply_click_effect)


    def update_cached_mouse_position(self, x, y):
        self.current_mouse_x, self.current_mouse_y = x, y
        self.current_mouse_grid_x, self.current_mouse_grid_y = self.mouse_to_grid_pos(x, y)


    def apply_click_effect(self, dt, new_cell_state):
        for dx, dy in self._mode._neighbourhood:
            nx, ny = self.current_mouse_grid_x + dx, self.current_mouse_grid_y + dy
            if self.in_grid(nx, ny):
                self._data_grid[ny][nx] = new_cell_state
                self.click_changed_cells = np.vstack([self.click_changed_cells, [ny, nx]])

        if self._paused:
            self.update_visuals()



    def in_grid(self, x, y):
        return x >= 0 and x < Settings.GRID_WIDTH and y >= 0 and y < Settings.GRID_HEIGHT


    def on_key_press(self, symbol, modifiers):
        match symbol:
            case Controls.PRINT_BALANCE:
                self.calculate_and_print_sand_balance()
            case Controls.NEXT_PRESET:
                if isinstance(self._mode, modes.CellularAutomataMode):
                    self._mode.next_preset()
            case Controls.CLEAR_SCREEN:
                self._clear_screen_pressed = True
            case Controls.PAUSE:
                if self._paused == False:
                    self.pause()
                else:
                    self.resume()
            case Controls.ADVANCE_FRAME:
                self.update(0)
            case Controls.CA_MODE:
                self.mode_change_key_pressed('CA', modifiers)
            case Controls.SAND_MODE:
                self.mode_change_key_pressed('SAND', modifiers)
            case Controls.WATER_MODE:
                self.mode_change_key_pressed('WATER', modifiers)
            case Controls.SMOOTH:
                self.smooth()

    def smooth(self):
        # cache mode to switch back after update
        cached_mode = self._mode

        # switch to trail mode and update one frame
        self._mode = self._modes['TRAIL']
        self.update(0)

        # switch back to original mode
        self._mode = cached_mode

    def mode_change_key_pressed(self, mode_key, modifiers):
        self._mode = self._modes[mode_key]

        # if shift is pressed, advance one frame
        if (modifiers & pyglet.window.key.MOD_SHIFT):
            self.update(0)
            
    def clear_screen(self):
        self._data_grid = np.zeros_like(self._data_grid, dtype=bool)
        self._mode.changed_cells = np.argwhere(self._data_grid == False)


    def pause(self):
        pyglet.clock.unschedule(self.update)
        self._paused = True
    
    def resume(self):
        pyglet.clock.schedule(self.update)
        self._paused = False

    def calculate_and_print_sand_balance(self):
        width, height = Settings.GRID_WIDTH, Settings.GRID_HEIGHT
        left_side_count = 0
        right_side_count = 0

        # Iterate through each column to count sand cells
        for x in range(width):
            column_count = sum(1 for y in range(height) if self._data_grid[y][x])

            if x < width // 2:  # Left side
                left_side_count += column_count
            else:  # Right side
                right_side_count += column_count

        # Calculate averages
        left_avg = left_side_count / (width // 2)
        right_avg = right_side_count / (width - width // 2)

        # Print the difference
        print("Difference in averages (left - right):", left_avg - right_avg)
        print("Left side count: ", left_side_count)
        print("Right side count:", right_side_count)


    def mouse_to_grid_pos(self, mouse_x, mouse_y):
        grid_x = (mouse_x - Settings.WINDOW_MARGIN[dir.Left]) // Settings.CELL_WIDTH 
        grid_y = (mouse_y - Settings.WINDOW_MARGIN[dir.Top]) // Settings.CELL_HEIGHT 
        return grid_x, grid_y

if __name__ == '__main__':
    window = CellularAutomataWindow()
    pyglet.clock.schedule_interval(window.update, interval=1/Settings.SIMULATION_FRAME_RATE)
    pyglet.app.run()