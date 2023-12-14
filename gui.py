import pyglet

class GuiManager:
    def __init__(self, pyglet_window):
        self._pyglet_window = pyglet_window

    def new_command_display(self, pyglet_batch):
        return pyglet.text.Label('',
                                                font_name='Times New Roman',
                                                font_size=20,
                                                x=self._pyglet_window.width // 2, y=25,
                                                anchor_x='center', anchor_y='bottom',
                                                batch=pyglet_batch)