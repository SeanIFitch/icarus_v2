from __future__ import annotations


def _round_float(number: float, decimal_points: int = 3) -> float:
    decimal = 10**decimal_points
    return round(number * decimal) / decimal


class RGBA:
    """Class handling RGBA color code."""

    def __init__(self, r: int, g: int, b: int, a: float = 1) -> None:
        """Initialize rgba value.

        Args:
            r: Red(0~255).
            g: Green(0~255).
            b: Blue(0~255).
            a: Alpha(0~1). Defaults to 1.
        """
        self._r = min(255, max(0, r)) | 0
        self._g = min(255, max(0, g)) | 0
        self._b = min(255, max(0, b)) | 0
        self._a = _round_float(max(min(1, a), 0))

    def __str__(self) -> str:
        """Format RGBA class.

        e.g. rgba(100, 100, 100, 0.5).
        """
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a:.3f})"

    def __getitem__(self, item: int) -> int | float:
        """Unpack to (r, g, b, a)."""
        return [self.r, self.g, self.b, self.a][item]

    def __eq__(self, other: RGBA) -> bool:
        """Returns true if `r`, `g`, `b` and `a` are all the same."""
        return [self.r, self.g, self.b, self.a] == [other.r, other.g, other.b, other.a]

    @property
    def r(self) -> int:
        return self._r

    @property
    def g(self) -> int:
        return self._g

    @property
    def b(self) -> int:
        return self._b

    @property
    def a(self) -> float:
        return self._a
