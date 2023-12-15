import pyglet
from config.settings import Settings
from config.gui_settings import GuiSettings

class GuiManager:
    def __init__(self, pyglet_window, pyglet_batch):
        self._pyglet_window = pyglet_window
        self._batch = pyglet_batch

    def initialize_elements(self):
        self.initialize_color_labels()
        self.initialize_command_label()

        
    def initialize_color_labels(self):

        color_square_size = GuiSettings.COLOR_SQUARE_SIZE
        fg_label_x_pos = GuiSettings.COLOR_DISPLAY_X_OFFSET
        color_display_y_pos = self._pyglet_window.height + GuiSettings.COLOR_DISPLAY_Y_OFFSET
        fg_square_x_pos = fg_label_x_pos + color_square_size
        bg_label_x_pos = fg_square_x_pos + color_square_size + color_square_size
        bg_square_x_pos = bg_label_x_pos + color_square_size
        font_sz = GuiSettings.COLOR_DISPLAY_FONT_SIZE

        self._fg_color_label = pyglet.text.Label('fg:',
                                                font_name='Times New Roman',
                                                font_size=GuiSettings.COLOR_DISPLAY_FONT_SIZE,
                                                x=fg_label_x_pos, y=color_display_y_pos,
                                                anchor_x='center', anchor_y='bottom',
                                                batch=self._batch)

        self._fg_color_square = pyglet.shapes.Rectangle(x=fg_square_x_pos, y=color_display_y_pos,
                                    width= color_square_size, height=color_square_size,
                                    color=(0,0,0,255), batch=self._batch)


        
        self._bg_color_label = pyglet.text.Label('bg:',
                                                font_name='Times New Roman',
                                                font_size=GuiSettings.COLOR_DISPLAY_FONT_SIZE,
                                                x=bg_label_x_pos, y=color_display_y_pos,
                                                anchor_x='center', anchor_y='bottom',
                                                batch=self._batch)
        
        self._bg_color_square = pyglet.shapes.Rectangle(x=bg_square_x_pos, y=color_display_y_pos,
                                    width=color_square_size, height=color_square_size,
                                    color=(0,0,0,255), batch=self._batch)

    def initialize_command_label(self):
        x_pos = self._pyglet_window.width // 2
        self._command_label = pyglet.text.Label('',
                                                font_name='Times New Roman',
                                                font_size=GuiSettings.COMMAND_DISPLAY_FONT_SIZE,
                                                x=x_pos, y=GuiSettings.COMMAND_DISPLAY_Y_POS,
                                                anchor_x='center', anchor_y='bottom',
                                                batch=self._batch)
    
    def update_command_label(self, label_text):
        self._command_label.text = label_text

    def update_fg_color(self, color):
        self._fg_color_square.color = color

    def update_bg_color(self, color):
        self._bg_color_square.color = color