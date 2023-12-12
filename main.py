import time
from datetime import datetime
import numpy as np
import pyglet
from pyglet.window import mouse as mouse
from threading import Thread
from neighbourhoods import Neighbourhood
from config import Settings
from config import Controls
from direction import Direction as dir
import modes


class CellularAutomataWindow(pyglet.window.Window):

    def __init__(self):
        super().__init__()

        # cached settings
        self._current_mouse_y = None
        self._current_mouse_grid_y = None
        self._current_mouse_grid_x = None
        self._current_mouse_x = None
        self._brush = Neighbourhood.get_neighbourhood(Neighbourhood.ExMoore)

        self._color_thread = None
        self._data_grid = None
        self._visual_grid = None
        self.width = Settings.WINDOW_WIDTH
        self.height = Settings.WINDOW_HEIGHT
        self._grid_width = Settings.GRID_WIDTH
        self._grid_height = Settings.GRID_HEIGHT
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
            'CA': modes.CellularAutomataMode(),
            'SAND': modes.SandMode(),
            'RE': modes.ExpandMode(),
            'ZEBRA': modes.ZebraMode(),
            'SMOOTH': modes.SmoothMode()
        }
        self._mode = self._modes['CA']
        self._neighbourhood = self._mode._neighbourhood

        # grid
        self.initialize_data_grid()
        self.initialize_visual_grid()
        self.velocity_map = {}

        # array for tracking cells changed by click, used in updating visual grid
        self._cells_changed_by_click = np.empty((0, 2), dtype=int)

        # current color values
        self._r = 0
        self._g = 0
        self._b = 0

        # amount by which colors change each frame (d = delta)
        self._dr = 1
        self._dg = 2
        self._db = 3

        # flag used outside of color thread to cause color loop to break
        self._color_rotation_active = False

        # separate flag that is used by the thread to indicate whether it has exited
        self._currently_rotating = False

        #debug command display
        self._command_label = pyglet.text.Label('',
                                                font_name='Times New Roman',
                                                font_size=20,
                                                x=self.width // 2, y=25,
                                                anchor_x='center', anchor_y='bottom',
                                                batch=self._batch)

    def toggle_color_rotation(self):
        if not self._color_rotation_active and not self._currently_rotating:
            self._color_rotation_active = True;
            self._color_thread = Thread(target=self.rotate_color_threaded)
            self._color_thread.start()
        else:
            self._color_rotation_active = False

    def rotate_color_threaded(self):
        self._currently_rotating = True
        while self._color_rotation_active:
            if not self._paused:
                time.sleep(0.05)
                self.rotate_to_next_color()

        self._currently_rotating = False

    def rotate_to_next_color(self):
        self._r += 1
        self._g += 2
        self._b += 3
        self._alive_color = (self._r, self._g, self._b, 255)

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
        changed_cells = np.unique(np.vstack([self._mode.changed_cells, self._cells_changed_by_click]), axis=0)

        if changed_cells.size > 0:
            # Update only the cells in the changed_cells set
            for y, x in changed_cells:
                self._visual_grid[y, x].color = self._alive_color if self._data_grid[y, x] else self._dead_color

        # Reset the click changes after updating
        self._cells_changed_by_click = np.empty((0, 2), dtype=int)

    def initialize_data_grid(self):
        self._data_grid = np.random.randint(0, len(Settings.CELL_STATES),
                                            size=(Settings.GRID_HEIGHT, Settings.GRID_WIDTH))
        np.random.randint(0, 3)
        for y in range(Settings.GRID_HEIGHT):
            for x in range(Settings.GRID_WIDTH):
                # set cell as alive if random float falls between 0 and INITIAL_LIFE_CHANCE
                self._data_grid[y][x] = np.random.rand() < Settings.INITIAL_LIFE_CHANCE

    def initialize_visual_grid(self):
        self._visual_grid = np.empty((Settings.GRID_HEIGHT, Settings.GRID_WIDTH), dtype=object)

        adjusted_y_values = np.arange(stop=Settings.VISUAL_GRID_HEIGHT + Settings.CELL_HEIGHT,
                                      step=Settings.CELL_HEIGHT) + Settings.WINDOW_MARGIN[dir.Top]
        adjusted_x_values = np.arange(stop=Settings.VISUAL_GRID_WIDTH + Settings.CELL_WIDTH, step=Settings.CELL_WIDTH) + \
                            Settings.WINDOW_MARGIN[dir.Left]

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
        pyglet.clock.schedule_interval(self.apply_click_effect, 1 / Settings.SIMULATION_FRAME_RATE, new_cell_state)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.mouse_held:
            if (abs(self._current_mouse_x - x) >= Settings.CELL_WIDTH or abs(
                    self._current_mouse_y - y) >= Settings.CELL_HEIGHT):
                self.update_cached_mouse_position(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse_held = False
        pyglet.clock.unschedule(self.apply_click_effect)

    def update_cached_mouse_position(self, x, y):
        self._current_mouse_x, self._current_mouse_y = x, y
        self._current_mouse_grid_x, self._current_mouse_grid_y = self.mouse_to_grid_pos(x, y)

    def apply_click_effect(self, dt, new_cell_state):
        for dx, dy in self._brush:
            nx, ny = self._current_mouse_grid_x + dx, self._current_mouse_grid_y + dy
            if self.in_grid(nx, ny):
                self._data_grid[ny][nx] = new_cell_state
                self._cells_changed_by_click = np.vstack([self._cells_changed_by_click, [ny, nx]])

        if self._paused:
            self.update_visuals()

    def in_grid(self, x, y):
        return 0 <= x < self._grid_width and 0 <= y < self._grid_height

    def on_key_press(self, symbol, modifiers):

        # initializing flags
        mode_button_pressed = False
        ctrl_held = False
        if modifiers & pyglet.window.key.MOD_CTRL:
            ctrl_held = True

        command_description = ''

        match symbol:

            # sand mode only
            case Controls.PRINT_BALANCE:
                self.calculate_and_print_sand_balance()

            # cellular automata mode only
            case Controls.NEXT_PRESET:
                command_description = 'P - NEXT CELLULAR AUTOMATA PRESET'
                if isinstance(self._mode, modes.CellularAutomataMode):
                    self._mode.next_preset()

            # all modes
            case Controls.CLEAR_SCREEN:
                command_description = 'BACKSPACE - CLEAR SCREEN'
                self._clear_screen_pressed = True
            case Controls.SCREENSHOT:
                command_description = 'S - SCREENSHOT'
                self.save_screenshot()
            case Controls.TOGGLE_PAUSE:
                if not self._paused:
                    self.pause()
                    command_description = 'SPACE - PAUSE'
                else:
                    self.resume()
                    command_description = 'SPACE - RESUME'
            case Controls.ADVANCE_FRAME:
                command_description = 'ENTER - NEXT FRAME'
                if not self._paused:
                    self.pause()
                self.advance_one_frame()
            case Controls.TOGGLE_COLOR_ROTATION:
                command_description = 'C - TOGGLE COLOR CHANGING'
                if not self._color_rotation_active:
                    command_description += '(ON)'
                else:
                    command_description += '(OFF)'
                self.toggle_color_rotation()

            # mode changing
            case Controls.CA_MODE:
                command_description = '1 - CELLULAR AUTOMATA MODE'
                mode_button_pressed = True
                mode_key = 'CA'
            case Controls.SAND_MODE:
                command_description = '2 - SAND MODE'
                mode_button_pressed = True
                mode_key = 'SAND'
            case Controls.ZEBRA_MODE:
                command_description = '3 - ZEBRA MODE'
                mode_button_pressed = True
                mode_key = 'ZEBRA'
            case Controls.EXPAND_MODE:
                command_description = '4 - EXPAND MODE'
                mode_button_pressed = True
                mode_key = 'RE'
            case Controls.SMOOTH:
                command_description = 'SHIFT - APPLY SMOOTHING'
                self.apply_smoothing()

        if mode_button_pressed:
            if ctrl_held:
                command_description = "CTRL + " + command_description + " (ONE FRAME)"
                self.apply_one_frame_from_mode(mode_key)
            else:
                self.change_mode(mode_key)

        self._command_label.text = command_description


    @staticmethod
    def save_screenshot():
        now = datetime.now().strftime("%d%m%Y_%H-%M-%S")
        image_path = Settings.SCREENSHOT_DIRECTORY + "screenshot_" + now + ".png"
        pyglet.image.get_buffer_manager().get_color_buffer().save(image_path)

    def advance_one_frame(self):
        if self._color_rotation_active:
            self.rotate_to_next_color()
        self.update(0)

    def apply_smoothing(self):
        self.apply_one_frame_from_mode('SMOOTH')

    def expand(self):
        self.apply_one_frame_from_mode('RANDOMENCOUNTER')

    def apply_one_frame_from_mode(self, mode_key):
        # cache mode to switch back after update
        cached_mode = self._mode

        # switch to trail mode and update one frame
        self._mode = self._modes[mode_key]
        self.update(0)

        # switch back to original mode
        self._mode = cached_mode

    def change_mode(self, mode_key):
        self._mode = self._modes[mode_key]

    def clear_screen(self):
        self._data_grid = np.zeros_like(self._data_grid, dtype=bool)
        self._mode.changed_cells = np.argwhere(self._data_grid == False)

    def pause(self):
        self.running = False
        pyglet.clock.unschedule(self.update)
        self._paused = True

    def resume(self):
        self.running = True
        pyglet.clock.schedule(self.update)
        self._paused = False

    def mouse_to_grid_pos(self, mouse_x, mouse_y):
        grid_x = (mouse_x - Settings.WINDOW_MARGIN[dir.Left]) // Settings.CELL_WIDTH
        grid_y = (mouse_y - Settings.WINDOW_MARGIN[dir.Top]) // Settings.CELL_HEIGHT
        return grid_x, grid_y


if __name__ == '__main__':
    window = CellularAutomataWindow()
    pyglet.clock.schedule_interval(window.update, interval=1 / Settings.SIMULATION_FRAME_RATE)
    pyglet.app.run()
