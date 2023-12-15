from datetime import datetime
import numpy as np
import pyglet
from pyglet.window import mouse as mouse
from neighbourhoods import Neighbourhood
from config.settings import Settings
from config.input import Input
from direction import Direction as dir
from gui import GuiManager
from color_controller import ColorController
from cell_data_controller import CellDataController
import modes


class CellularAutomataWindow(pyglet.window.Window):

    def __init__(self):

        # pyglet stuff
        super().__init__()

        self.fps = pyglet.window.FPSDisplay(self)
        self._batch = pyglet.graphics.Batch()
        self.width = Settings.WINDOW_WIDTH
        self.height = Settings.WINDOW_HEIGHT

        # cached data
        self._current_mouse_y = None
        self._current_mouse_grid_y = None
        self._current_mouse_grid_x = None
        self._current_mouse_x = None
        self._cells_changed_by_click = np.empty((0, 2), dtype=int)
        self._brush = Neighbourhood.get_neighbourhood(Neighbourhood.ExMoore)
        self._grid_width = Settings.GRID_WIDTH
        self._grid_height = Settings.GRID_HEIGHT

        # flags
        self._mouse_held = False
        self._paused = False
        self._clear_screen_pressed = False
        self._repopulate_pressed = False

        # array for tracking cells changed by click, used in updating visual grid
        self._color_ctrl = ColorController()

        # grid
        self._data_controller = CellDataController()
        self._data_controller.initialize_data_grid()
        self.initialize_visual_grid()

 

        # flag used outside of color thread to cause color loop to break
        self._color_rotation_active = False
        self._inverse_background_color_active = False
        
        self._gui_manager = GuiManager(self, self._batch)
        self._gui_manager.initialize_elements()

    def toggle_color_rotation(self):
        self._color_rotation_active = not self._color_rotation_active

    def toggle_inverse_background_color(self):
        self._inverse_background_color_active = not self._inverse_background_color_active


    def update(self, dt):
        self._data_controller.update()
        self.update_intermediates()
        self.update_visualization()

    # anything that needs to be done between data and visual updates
    def update_intermediates(self):
        self._color_ctrl.update()
        if self._clear_screen_pressed:
            self._data_controller.clear_screen()
            self._clear_screen_pressed = False
        if self._repopulate_pressed:
            self._data_controller.clear_screen()
            self._data_controller.initialize_data_grid()
            self._repopulate_pressed = False
        
    def update_visualization(self):
        # cache values for faster access
        fg = self._color_ctrl.fg
        bg = self._color_ctrl.bg

        changed_cells = self._data_controller.get_changed_cells()

        if changed_cells.size > 0:
            # Update only the cells in the changed_cells set
            for y, x in changed_cells:
                self._visual_grid[y, x].color = fg if self._data_controller._data_grid[y, x] else bg


    def initialize_visual_grid(self):
        self._visual_grid = np.empty((Settings.GRID_HEIGHT, Settings.GRID_WIDTH), dtype=object)

        adjusted_y_values = np.arange(stop=Settings.VISUAL_GRID_HEIGHT + Settings.CELL_HEIGHT,
                                      step=Settings.CELL_HEIGHT) + Settings.WINDOW_MARGIN[dir.Top]
        adjusted_x_values = np.arange(stop=Settings.VISUAL_GRID_WIDTH + Settings.CELL_WIDTH, step=Settings.CELL_WIDTH) + \
                            Settings.WINDOW_MARGIN[dir.Left]

        fg = self._color_ctrl.fg
        bg = self._color_ctrl.bg

        for y in range(Settings.GRID_HEIGHT):
            y_pos_in_window = adjusted_y_values[y]
            for x in range(Settings.GRID_WIDTH):
                x_pos_in_window = adjusted_x_values[x]
                cell_state = self._data_controller.state_at(y, x)
                color = fg if cell_state else bg
                cell = pyglet.shapes.Rectangle(x=x_pos_in_window, y=y_pos_in_window,
                                               width=Settings.CELL_WIDTH, height=Settings.CELL_HEIGHT,
                                               color=color, batch=self._batch)
                self._visual_grid[y][x] = cell

    def on_draw(self):
        self.clear()
        self._batch.draw()
        self.fps.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        self._mouse_held = True
        self.update_cached_mouse_position(x, y)

        # Unschedule any existing task before scheduling a new one
        pyglet.clock.unschedule(self.apply_click_effect)

        # Determine the new cell state based on the button pressed
        new_cell_state = button == mouse.LEFT
        pyglet.clock.schedule_interval(self.apply_click_effect, 1 / Settings.SIMULATION_FRAME_RATE, new_cell_state)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self._mouse_held:
            if (abs(self._current_mouse_x - x) >= Settings.CELL_WIDTH or abs(
                    self._current_mouse_y - y) >= Settings.CELL_HEIGHT):
                self.update_cached_mouse_position(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self._mouse_held = False
        pyglet.clock.unschedule(self.apply_click_effect)

    def update_cached_mouse_position(self, x, y):
        self._current_mouse_x, self._current_mouse_y = x, y
        self._current_mouse_grid_x, self._current_mouse_grid_y = self.convert_mouse_to_grid_pos(x, y)

    def apply_click_effect(self, dt, new_cell_state):
        cells_to_update = []

        for dx, dy in self._brush:
            nx, ny = self._current_mouse_grid_x + dx, self._current_mouse_grid_y + dy
            if self._data_controller.in_grid(nx, ny):  # Assuming in_grid is a method that checks if the cell is within the grid bounds
                cells_to_update.append((ny, nx))

        self._data_controller.set_cell_states(cells_to_update, new_cell_state)

        if self._paused:
            self.update_visualization()

    def in_grid(self, x, y):
        return 0 <= x < self._grid_width and 0 <= y < self._grid_height

    def on_key_press(self, symbol, modifiers):

        # tracks if user has pressed a button associated with a mode
        # if they have, we then check to see if they are holding MOD_KEY
        # if MOD_KEY is held, the rules of the mode will be applied for one frame
        # else, switch to the mode
        mode_button_pressed = False
        mod_key_held = False
        if modifiers & Input.MOD_KEY:
            mod_key_held = True

        # initialize string for label
        # if key pressed is not a command, label will receive an empty string
        command_description = ''
        command_key = pyglet.window.key.symbol_string(symbol)

        match symbol:
            # cellular automata mode only
            case Input.NEXT_PRESET:
                command_description = 'P - NEXT CELLULAR AUTOMATA PRESET'
                self._data_controller.next_ca_preset()

            # all modes
            case Input.CLEAR_SCREEN:
                command_description = 'CLEAR SCREEN'
                self._clear_screen_pressed = True
            case Input.REPOPULATE:
                command_description = 'RANDOM REPOPULATION'
                self._repopulate_pressed = True
            case Input.SCREENSHOT:
                command_description = 'SCREENSHOT'
                self.save_screenshot()
            case Input.TOGGLE_PAUSE:
                if not self._paused:
                    self.pause()
                    command_description = 'PAUSE'
                else:
                    self.resume()
                    command_description = 'RESUME'
            case Input.ADVANCE_FRAME:
                command_description = 'NEXT FRAME'
                if not self._paused:
                    self.pause()
                self.update(0)

            # colors
            case Input.TOGGLE_FG_COLOR_ROTATION:
                command_description = 'TOGGLE FG COLOR CHANGE'
                if not self._color_ctrl.fg_color_rotation_active:
                    command_description += '(ON)'
                else:
                    command_description += '(OFF)'
                self._color_ctrl.toggle_fg_color_rotation()

            case Input.TOGGLE_BG_COLOR_ROTATION:
                command_description = 'TOGGLE BG COLOR CHANGE'
                if not self._color_ctrl.bg_color_rotation_active:
                    command_description += '(ON)'
                else:
                    command_description += '(OFF)'
                self._color_ctrl.toggle_bg_color_rotation()

                if self._color_ctrl.bg_as_inverse_fg_active:
                    self._color_ctrl.toggle_inverse_background_color()

            case Input.TOGGLE_INVERSE_BG_COLOR:
                command_description = 'TOGGLE INVERSE BG COLOR'
                if not self._color_ctrl.bg_as_inverse_fg_active:
                    command_description += '(ON)'
                else:
                    command_description += '(OFF)'
                self._color_ctrl.toggle_inverse_background_color()

                if self._color_ctrl.bg_color_rotation_active:
                    self._color_ctrl.toggle_bg_color_rotation()


            # mode changing
            case Input.CA_MODE:
                command_description = 'CELLULAR AUTOMATA MODE'
                mode_button_pressed = True
            case Input.SAND_MODE:
                command_description = 'SAND MODE'
                mode_button_pressed = True
            case Input.ZEBRA_MODE:
                command_description = 'ZEBRA MODE'
                mode_button_pressed = True
            case Input.EXPAND_MODE:
                command_description = 'EXPAND MODE'
                mode_button_pressed = True
            case Input.TRAIL_MODE:
                command_description = 'TRAIL_MODE'
                mode_button_pressed = True
            case Input.SMOOTH:
                command_description = 'APPLY SMOOTHING'
                self.apply_smoothing()

        # add command key to command description
        command_description = command_key + ' - ' + command_description

        # if the button pressed was a mode button, check if we should apply only one frame, or 
        if mode_button_pressed:
            if mod_key_held:
                # modify description if ctrl is held
                command_description = pyglet.window.key.symbol_string(Input.MOD_KEY) + command_description + ' (ONE FRAME)'
                self.apply_one_frame_from_mode(symbol)
            else:
                self._data_controller.set_mode(symbol)

        self._gui_manager.update_command_label(command_description)


    @staticmethod
    def save_screenshot():
        now = datetime.now().strftime("%d%m%Y_%H-%M-%S")
        image_path = Settings.SCREENSHOT_DIRECTORY + "screenshot_" + now + ".png"
        pyglet.image.get_buffer_manager().get_color_buffer().save(image_path)

    def apply_smoothing(self):
        # applying trail mode for a single frame has a smoothing effect
        self.apply_one_frame_from_mode(Input.TRAIL_MODE)

    def apply_one_frame_from_mode(self, mode_key):
        self._data_controller.set_temporary_mode(mode_key)
        self.update(0)
        self._data_controller.exit_temporary_mode()

    def change_mode(self, mode_key):
        self._mode = self._modes[mode_key]

    # todo: move to data controller

    def pause(self):
        self.running = False
        pyglet.clock.unschedule(self.update)
        self._paused = True

    def resume(self):
        self.running = True
        pyglet.clock.schedule(self.update)
        self._paused = False

    def convert_mouse_to_grid_pos(self, mouse_x, mouse_y):
        grid_x = (mouse_x - Settings.WINDOW_MARGIN[dir.Left]) // Settings.CELL_WIDTH
        grid_y = (mouse_y - Settings.WINDOW_MARGIN[dir.Top]) // Settings.CELL_HEIGHT
        return grid_x, grid_y


if __name__ == '__main__':
    window = CellularAutomataWindow()
    pyglet.clock.schedule_interval(window.update, interval=1 / Settings.SIMULATION_FRAME_RATE)
    pyglet.app.run()
