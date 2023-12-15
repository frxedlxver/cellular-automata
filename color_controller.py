from config.settings import Settings

class ColorController:

    def __init__(self):

        # initialize color values
        self._r = 0
        self._g = 0
        self._b = 0

        self._r_bg = 255
        self._g_bg = 255
        self._b_bg = 255

        # amount by which colors change each frame (d = delta)
        self._dr = 4
        self._dg = 2
        self._db = 1

        self.fg = (self._r, self._g, self._b, 255)
        self.bg = (self._r_bg, self._g_bg, self._b_bg, 255)

        self.bg_color_rotation_active = False
        self.fg_color_rotation_active = False
        self.bg_as_inverse_fg_active = False


    def update(self):
        if self.fg_color_rotation_active:
            self.advance_fg_color()
            
        if self.bg_as_inverse_fg_active:
            self.bg_color_to_inverse_fg()
        elif self.bg_color_rotation_active:
            self.advance_bg_color()

    def toggle_fg_color_rotation(self):
        self.fg_color_rotation_active = not self.fg_color_rotation_active

    def toggle_inverse_background_color(self):
        self.bg_as_inverse_fg_active = not self.bg_as_inverse_fg_active

    def toggle_bg_color_rotation(self):
        self.bg_color_rotation_active = not self.bg_color_rotation_active

    def advance_fg_color(self):
        self.set_fg(
            self._r + self._dr,
            self._g + self._dg,
            self._b + self._db
        )

    def advance_bg_color(self):
        self.set_bg(
            self._r_bg + self._dr,
            self._g_bg + self._dg,
            self._b_bg + self._db
        )

    def bg_color_to_inverse_fg(self):
        self.set_bg(
            255 - self._r,
            255 - self._g,
            255 - self._b
        )

    @staticmethod
    def inverse_color(r, g, b):
        r, g, b = ColorController.normalize_color(r, g, b)
        return 255 - r, 255 - g, 255 - b

    
    @staticmethod
    def normalize_color(r, g, b):
        return r % 255, g % 255, b % 255

    def set_fg(self, r, g, b):
        self._r, self._g, self._b = self.normalize_color(r, g, b)
        self.fg = (self._r, self._g, self._b, 255)

    def set_bg(self, r, g, b):
        self._r_bg, self._g_bg, self._b_bg = self.normalize_color(r, g, b)
        self.bg = (self._r_bg, self._g_bg, self._b_bg, 255)


