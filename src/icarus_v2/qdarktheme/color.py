from __future__ import annotations
import math
from icarus_v2.qdarktheme.rgba import RGBA
from icarus_v2.qdarktheme.hsla import HSLA


class Color:
    """Class handling color code(RGBA and HSLA)."""

    def __init__(self, color_code: RGBA | HSLA) -> None:
        """Initialize color code."""
        self._hsla, self._hsva = None, None
        if isinstance(color_code, RGBA):
            self._rgba = color_code
        elif isinstance(color_code, HSLA):
            self._hsla = color_code
            self._rgba = self._hsla.to_rgba()

    @property
    def rgba(self) -> RGBA:
        """Return rgba."""
        return self._rgba

    @property
    def hsla(self) -> HSLA:
        """Return hsla."""
        return self._hsla if self._hsla else HSLA.from_rgba(self.rgba)

    def __str__(self) -> str:
        """Format Color class.

        e.g. rgba(100, 100, 100, 0.5).
        """
        return str(self.rgba)

    @staticmethod
    def _check_hex_format(hex_format: str) -> None:
        """Check if string is hex format."""
        try:
            hex = hex_format.lstrip("#")
            if not len(hex) in (3, 4, 6, 8):
                raise ValueError
            int(hex, 16)
        except ValueError:
            raise ValueError(
                f'invalid hex color format: "{hex_format}". '
                "Only support following hexadecimal notations: #RGB, #RGBA, #RRGGBB and #RRGGBBAA. "
                "R (red), G (green), B (blue), and A (alpha) are hexadecimal characters "
                "(0-9, a-f or A-F)."
            ) from None

    @staticmethod
    def from_rgba(r: int, g: int, b: int, a: int) -> Color:
        """Convert rgba to Color object."""
        rgba = RGBA(r, g, b, a / 255)
        return Color(rgba)

    @staticmethod
    def from_hex(hex: str) -> Color:
        """Convert hex string to Color object.

        Args:
            color_hex: Color hex string.

        Returns:
            Color: Color object converted from hex.
        """
        Color._check_hex_format(hex)
        hex = hex.lstrip("#")
        r, g, b, a = 255, 0, 0, 1
        if len(hex) == 3:  # #RGB format
            r, g, b = (int(char, 16) for char in hex)
            r, g, b = 16 * r + r, 16 * g + g, 16 * b + b
        if len(hex) == 4:  # #RGBA format
            r, g, b, a = (int(char, 16) for char in hex)
            r, g, b = 16 * r + r, 16 * g + g, 16 * b + b
            a = (16 * a + a) / 255
        if len(hex) == 6:  # #RRGGBB format
            r, g, b = bytes.fromhex(hex)
            a = 1
        elif len(hex) == 8:  # #RRGGBBAA format
            r, g, b, a = bytes.fromhex(hex)
            a = a / 255
        return Color(RGBA(r, g, b, a))

    def _to_hex(self) -> str:
        """Convert Color object to hex(#RRGGBBAA).

        Args:
            color: Color object.

        Returns:
            str: Hex converted from Color object.
        """
        r, g, b, a = self.rgba.r, self.rgba.g, self.rgba.b, self.rgba.a
        hex_color = f"{math.floor(r):02x}{math.floor(g):02x}{math.floor(b):02x}"
        if a != 1:
            hex_color += f"{math.floor(a*255):02x}"
        return hex_color

    def to_hex_argb(self) -> str:
        """Convert Color object to hex(#AARRGGBB).

        Args:
            color: Color object.

        Returns:
            str: Hex converted from Color object.
        """
        r, g, b, a = self.rgba.r, self.rgba.g, self.rgba.b, self.rgba.a
        hex_color = "" if a == 1 else f"{math.floor(a*255):02x}"
        hex_color += f"{math.floor(r):02x}{math.floor(g):02x}{math.floor(b):02x}"
        return hex_color

    def to_svg_tiny_color_format(self) -> str:
        """Convert Color object to string for svg.

        QtSvg does not support #RRGGBBAA format.
        Therefore, we need to set the alpha value to `fill-opacity` instead.

        Returns:
            str: RGBA format.
        """
        r, g, b, a = self.rgba
        if a == 1:
            return f'fill="#{self._to_hex()}"'
        return f'fill="rgb({r},{g},{b})" fill-opacity="{a}"'

    def lighten(self, factor: float) -> Color:
        """Lighten color."""
        return Color(HSLA(self.hsla.h, self.hsla.s, self.hsla.l + self.hsla.l * factor, self.hsla.a))

    def darken(self, factor: float) -> Color:
        """Darken color."""
        return Color(HSLA(self.hsla.h, self.hsla.s, self.hsla.l - self.hsla.l * factor, self.hsla.a))

    def transparent(self, factor: float) -> Color:
        """Make color transparent."""
        return Color(RGBA(self.rgba.r, self.rgba.g, self.rgba.b, self.rgba.a * factor))
