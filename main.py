from datetime import datetime
import numpy as np
import pyglet
from pyglet.window import mouse as mouse
from neighbourhoods import Neighbourhood
from config.settings import Settings
from config.input import Controls
from direction import Direction as dir
from gui import GuiManager
import modes


class CellularAutomataWindow(pyglet.window.Window):

    def __init__(self):
        super().__init__()

        self._gui_manager = GuiManager(self)


        # cached settings
        self._current_mouse_y = None
        self._current_mouse_grid_y = None
        self._current_mouse_grid_x = None
        self._current_mouse_x = None
        self._brush = Neighbourhood.get_neighbourhood(Neighbourhood.ExMoore)

        self._data_grid = None
        self._visual_grid = None
        self.width = Settings.WINDOW_WIDTH
        self.height = Settings.WINDOW_HEIGHT
        self._grid_width = Settings.GRID_WIDTH
        self._grid_height = Settings.GRID_HEIGHT

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
            Controls.CA_MODE        : modes.CellularAutomataMode(),
            Controls.SAND_MODE      : modes.SandMode(),
            Controls.EXPAND_MODE    : modes.ExpandMode(),
            Controls.ZEBRA_MODE     : modes.ZebraMode(),
            Controls.TRAIL_MODE    : modes.SmoothMode()
        }
        self._mode = self._modes[Controls.CA_MODE]
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
        self._dr = 4
        self._dg = 2
        self._db = 1

        # flag used outside of color thread to cause color loop to break
        self._color_rotation_active = False
        self._inverse_background_color_active = False

        # separate flag that is used by the thread to indicate whether it has exited
        self._currently_rotating = False

        #debug command display
        self._command_label = self._gui_manager.new_command_display(self._batch)
        color_square_size = 10
        fg_label_x_pos = 25
        fg_square_x_pos = fg_label_x_pos + color_square_size
        bg_label_x_pos = fg_square_x_pos + color_square_size + color_square_size
        bg_square_x_pos = bg_label_x_pos + color_square_size
        color_display_y_pos = self._height - 25

        self._fg_color_label = pyglet.text.Label('fg:',
                                                font_name='Times New Roman',
                                                font_size=10,
                                                x=fg_label_x_pos, y=color_display_y_pos,
                                                anchor_x='center', anchor_y='bottom',
                                                batch=self._batch)

        self._fg_color_square = pyglet.shapes.Rectangle(x=fg_square_x_pos, y=color_display_y_pos,
                                    width= color_square_size, height=color_square_size,
                                    color=self._alive_color, batch=self._batch)


        
        self._bg_color_label = pyglet.text.Label('bg:',
                                                font_name='Times New Roman',
                                                font_size=10,
                                                x=bg_label_x_pos, y=color_display_y_pos,
                                                anchor_x='center', anchor_y='bottom',
                                                batch=self._batch)
        
        self._bg_color_square = pyglet.shapes.Rectangle(x=bg_square_x_pos, y=color_display_y_pos,
                                    width=10, height=10,
                                    color=self._dead_color, batch=self._batch)

    def toggle_color_rotation(self):
        self._color_rotation_active = not self._color_rotation_active

    def toggle_inverse_background_color(self):
        self._inverse_background_color_active = not self._inverse_background_color_active

    def rotate_to_next_color(self):
        self._r = (self._r + self._dr) % 255
        self._g = (self._g + self._dg) % 255
        self._b = (self._b + self._db) % 255
        self._alive_color = (self._r, self._g, self._b, 255)
        self._fg_color_square.color = self._alive_color

    def bg_color_to_inverse_fg(self):
        self._dead_color = (
            255 - self._r,
            255 - self._g,
            255 - self._b,
            255
        )
        self._bg_color_square.color = self._dead_color


    def update(self, dt):
        self.update_data()
        if self._clear_screen_pressed:
            self.clear_screen()
            self._clear_screen_pressed = False
        if self._color_rotation_active:
            self.rotate_to_next_color()
            if self._inverse_background_color_active:
                self.bg_color_to_inverse_fg()
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

        # tracks if user has pressed a button associated with a mode
        # if they have, we then check to see if they are holding MOD_KEY
        # if MOD_KEY is held, the rules of the mode will be applied for one frame
        # else, switch to the mode
        mode_button_pressed = False
        mod_key_held = False
        if modifiers & Controls.MOD_KEY:
            mod_key_held = True

        # initialize string for label
        # if key pressed is not a command, label will receive an empty string
        command_description = ''
        command_key = pyglet.window.key.symbol_string(symbol)

        match symbol:
            # cellular automata mode only
            case Controls.NEXT_PRESET:
                command_description = 'P - NEXT CELLULAR AUTOMATA PRESET'
                if isinstance(self._mode, modes.CellularAutomataMode):
                    self._mode.next_preset()

            # all modes
            case Controls.CLEAR_SCREEN:
                command_description = 'CLEAR SCREEN'
                self._clear_screen_pressed = True
            case Controls.SCREENSHOT:
                command_description = 'SCREENSHOT'
                self.save_screenshot()
            case Controls.TOGGLE_PAUSE:
                if not self._paused:
                    self.pause()
                    command_description = 'PAUSE'
                else:
                    self.resume()
                    command_description = 'RESUME'
            case Controls.ADVANCE_FRAME:
                command_description = 'NEXT FRAME'
                if not self._paused:
                    self.pause()
                self.advance_one_frame()

            # colors
            case Controls.TOGGLE_COLOR_ROTATION:
                command_description = 'TOGGLE COLOR CHANGE'
                if not self._color_rotation_active:
                    command_description += '(ON)'
                else:
                    command_description += '(OFF)'
                self.toggle_color_rotation()
            case pyglet.window.key.O:
                command_description = 'TOGGLE BG COLOR CHANGE'
                self.toggle_inverse_background_color()

            # mode changing
            case Controls.CA_MODE:
                command_description = 'CELLULAR AUTOMATA MODE'
                mode_button_pressed = True
            case Controls.SAND_MODE:
                command_description = 'SAND MODE'
                mode_button_pressed = True
            case Controls.ZEBRA_MODE:
                command_description = 'ZEBRA MODE'
                mode_button_pressed = True
            case Controls.EXPAND_MODE:
                command_description = 'EXPAND MODE'
                mode_button_pressed = True
            case Controls.TRAIL_MODE:
                command_description = 'TRAIL_MODE'
                mode_button_pressed = True
            case Controls.SMOOTH:
                command_description = 'APPLY SMOOTHING'
                self.apply_smoothing()

        # add command key to command description
        command_description = command_key + ' - ' + command_description

        # if the button pressed was a mode button, check if we should apply only one frame, or 
        if mode_button_pressed:
            if mod_key_held:
                # modify description if ctrl is held
                command_description = pyglet.window.key.symbol_string(Controls.MOD_KEY) + command_description + ' (ONE FRAME)'
                self.apply_one_frame_from_mode(symbol)
            else:
                self.change_mode(symbol)

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
        # applying trail mode for a single frame has a smoothing effect
        self.apply_one_frame_from_mode(Controls.TRAIL_MODE)

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
