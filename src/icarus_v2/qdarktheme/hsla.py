from __future__ import annotations
import colorsys
from icarus_v2.qdarktheme.rgba import RGBA


def _round_float(number: float, decimal_points: int = 3) -> float:
    decimal = 10**decimal_points
    return round(number * decimal) / decimal


class HSLA:
    def __init__(self, h: int, s: float, l: float, a: float = 1) -> None:  # noqa: E741
        self._h = max(min(360, h), 0) | 0
        self._s = _round_float(max(min(1, s), 0))
        self._l = _round_float(max(min(1, l), 0))
        self._a = _round_float(max(min(1, a), 0))

    def __eq__(self, other: HSLA) -> bool:
        """Returns true if `h`, `s`, `l` and `a` are all the same."""
        return [self.h, self.s, self.l, self.a] == [other.h, other.s, other.l, other.a]

    @property
    def h(self) -> int:
        return self._h

    @property
    def s(self) -> float:
        return self._s

    @property
    def l(self) -> float:  # noqa: E741, E743
        return self._l

    @property
    def a(self) -> float:
        return self._a

    @staticmethod
    def from_rgba(rgba: RGBA) -> HSLA:
        hls = colorsys.rgb_to_hls(rgba.r / 255, rgba.g / 255, rgba.b / 255)
        return HSLA(int(hls[0] * 360), hls[2], hls[1], rgba.a)

    def to_rgba(self) -> RGBA:
        rgb = colorsys.hls_to_rgb(self.h / 360, self.l, self.s)
        return RGBA(round(rgb[0] * 255), round(rgb[1] * 255), round(rgb[2] * 255), self.a)
