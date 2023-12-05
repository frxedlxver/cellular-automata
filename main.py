import numpy as np
import pyglet
from pyglet.window import mouse as mouse
from config import Config
import modes

class CellularAutomataWindow(pyglet.window.Window):

    def __init__(self):
        super().__init__()
        self.width = Config.WINDOW_WIDTH
        self.height = Config.WINDOW_HEIGHT
        self._batch = pyglet.graphics.Batch()
        self.mouse_held = False
        self._CA_mode = modes.CellularAutomataMode()
        self._sand_mode = modes.SandMode()
        self._mode = self._CA_mode
        self._neighbourhood = self._mode.neighbourhood()
        self.initialize_data_grid()
        self._visual_grid = []
        self.initialize_visual_grid()
        self.velocity_map = {}
        self._paused = False
    
        
    def update(self, dt):
        self._data_grid = self._mode.update(self._data_grid)
        self.update_visual_grid()


    def get_cell_color(self, cell_state):
        return Config.RGB_ALIVE if cell_state else Config.RGB_DEAD
        

    def initialize_data_grid(self):
        self._data_grid = np.zeros((Config.GRID_HEIGHT, Config.GRID_WIDTH), dtype=bool)
        for y in range(Config.GRID_HEIGHT):
            for x in range(Config.GRID_WIDTH):
                # set cell as alive if random float falls between 0 and INITIAL_LIFE_CHANCE
                self._data_grid[y][x] = np.random.rand() < Config.INITIAL_LIFE_CHANCE


    def initialize_visual_grid(self):
        for y in range(Config.GRID_HEIGHT):
            row = []
            for x in range(Config.GRID_WIDTH):
                is_alive = self._data_grid[y][x]
                
                color = Config.RGB_ALIVE if is_alive else Config.RGB_DEAD

                # create cell and add to batch
                cell = pyglet.shapes.Rectangle(x=x * Config.CELL_SIZE, y=y * Config.CELL_SIZE, 
                                            width=Config.CELL_SIZE, height=Config.CELL_SIZE, 
                                            color=color, batch=self._batch)
                
                # add cell to visual grid for updating
                row.append(cell)
            self._visual_grid.append(row)


    def update_visual_grid(self):
            for (y, x) in self._mode.changed_cells:
                # Update the visual representation for the changed cell
                self._visual_grid[y][x].color = self.get_cell_color(self._data_grid[y][x])

                

    def update_cell_color(self, x, y, new_cell_color):
        self._visual_grid[y][x].color = new_cell_color


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
        pyglet.clock.schedule_interval(self.apply_click_effect, 1/Config.TARGET_FRAME_RATE, new_cell_state)


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.mouse_held:
            if (abs(self.current_mouse_x - x) >= Config.CELL_SIZE or abs(self.current_mouse_y - y) >= Config.CELL_SIZE):
                self.update_cached_mouse_position(x, y)
            if (buttons & mouse.LEFT):
                self.apply_click_effect(0, True)
            elif(buttons & mouse.RIGHT):
                self.apply_click_effect(0, False)


    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse_held = False
        pyglet.clock.unschedule(self.apply_click_effect)


    def update_cached_mouse_position(self, x, y):
        self.current_mouse_x, self.current_mouse_y = x, y
        self.current_mouse_grid_x, self.current_mouse_grid_y = self.window_pos_to_grid_pos(x, y)


    def apply_click_effect(self, dt, new_cell_state):
        for dx, dy in self._mode._neighbourhood:
            nx, ny = self.current_mouse_grid_x + dx, self.current_mouse_grid_y + dy
            if self.in_grid(nx, ny):
                self._data_grid[ny][nx] = new_cell_state


    def in_grid(self, x, y):
        return x >= 0 and x < Config.GRID_WIDTH and y >= 0 and y < Config.GRID_HEIGHT


    def on_key_press(self, symbol, modifiers):
        match symbol:
            case Config.KB_PRINT_BALANCE:
                self.calculate_and_print_sand_balance()
            case Config.KB_SWITCH_MODE:
                # Code to switch modes goes here
                if isinstance(self._mode, modes.SandMode):
                    self._mode = self._CA_mode
                else:
                    self._mode = self._sand_mode
            case Config.KB_NEXT_PRESET:
                if isinstance(self._mode, modes.CellularAutomataMode):
                    self._mode.next_preset()
            case Config.KB_CLEAR_SCREEN:
                self.clear_screen()
            case Config.KB_PAUSE:
                if self._paused == False:
                    self.pause()
                else:
                    self.resume()

    def clear_screen(self):
        self._data_grid = np.zeros_like(self._data_grid)


    def pause(self):
        pyglet.clock.unschedule(self.update)
        self._paused = True
    
    def resume(self):
        pyglet.clock.schedule(self.update)
        self._paused = False

    def calculate_and_print_sand_balance(self):
        width, height = Config.GRID_WIDTH, Config.GRID_HEIGHT
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


    def window_pos_to_grid_pos(self, click_x, click_y):
        cell_size = Config.CELL_SIZE
        return click_x // cell_size, click_y // cell_size


if __name__ == '__main__':
    window = CellularAutomataWindow()
    pyglet.clock.schedule_interval(window.update, interval=1/Config.TARGET_FRAME_RATE)
    pyglet.app.run()