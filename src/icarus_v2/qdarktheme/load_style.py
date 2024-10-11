from __future__ import annotations
import os
import re
from dataclasses import dataclass
from icarus_v2.qdarktheme.color import Color
from pathlib import Path


"""Default color values."""
THEME_COLOR_VALUES = {
    "dark": {
        "background": {
            "base": "#2a2a2a",
            "list": {},
            "panel": {"darken": 0.3},
            "popup": {"lighten": 0.3},
            "table": {"darken": 0.5},
            "textarea": {"darken": 0.13},
            "title": {"darken": 0.3},
        },
        "border": {
            "base": "#808080",
            "input": {"transparent": 0},
        },
        "button": {
            "base": "#e4e7eb",
            "button.activeBackground": {"darken": 0.14, "transparent": 0.23},
            "button.hoverBackground": {"darken": 0.1, "transparent": 0.11},
            "defaultButton.activeBackground": {"darken": 0.12},
            "defaultButton.hoverBackground": {"darken": 0.06},
        },
        "foreground": {
            "base": "#e4e7eb",
            "defaultButton.disabledBackground": {"transparent": 0.2},
            "disabled": {"transparent": 0.4},
            "disabledSelectionBackground": {"transparent": 0.2},
            "icon": {"darken": 0.01},
            "icon.unfocused": {"transparent": 0.6},
            "input.placeholder": {"transparent": 0.6},
            "progressBar.disabledBackground": {"transparent": 0.2},
            "slider.disabledBackground": {"transparent": 0.2},
            "sliderTrack.inactiveBackground": {"transparent": 0.1},
        },
        "input.background": "#3f4042",
        "inputButton.hoverBackground": "#ffffff25",
        "linkVisited": "#c58af8",
        "list.alternateBackground": "#ffffff0c",
        "list.hoverBackground": "#ffffff13",
        "menubar.selectionBackground": "#ffffff25",
        "popupItem.checkbox.background": "#ffffff19",
        "popupItem.selectionBackground": "#ffffff22",
        "primary": {
            "base": "#8ab4f7",
            "button.activeBackground": {"darken": 0.14, "transparent": 0.23},
            "button.hoverBackground": {"darken": 0.1, "transparent": 0.11},
            "defaultButton.activeBackground": {"darken": 0.12},
            "defaultButton.hoverBackground": {"darken": 0.06},
            "list.inactiveSelectionBackground": {"lighten": 0.2, "transparent": 0.15},
            "list.selectionBackground": {"darken": 0.2, "transparent": 0.4},
            "progressBar.background": {"darken": 0.1},
            "selection.background": {"darken": 0.2, "lighten": 0.1, "transparent": 0.4},
            "sliderHandle.activeBackground": {"darken": 0.09},
            "table.inactiveSelectionBackground": {"lighten": 0.2, "transparent": 0.18},
            "table.selectionBackground": {"darken": 0.2, "transparent": 0.55},
            "textarea.selectionBackground": {"darken": 0.2, "lighten": 0.1, "transparent": 0.4},
        },
        "scrollbar.background": "#ffffff10",
        "scrollbarSlider.activeBackground": "#ffffff60",
        "scrollbarSlider.background": "#ffffff30",
        "scrollbarSlider.disabledBackground": "#ffffff15",
        "scrollbarSlider.hoverBackground": "#ffffff45",
        "statusBar.background": "#2a2b2e",
        "statusBarItem.activeBackground": "#ffffff34",
        "statusBarItem.hoverBackground": "#ffffff22",
        "tab.activeBackground": "#ffffff00",
        "tab.hoverBackground": "#ffffff18",
        "tabCloseButton.hoverBackground": "#ffffff25",
        "table.alternateBackground": "#ffffff15",
        "tableSectionHeader.background": "#3f4042",
        "textarea.inactiveSelectionBackground": "#ffffff20",
        "toggleButtonOff": {
            "base": "#f45555",
            "button.activeBackground": {"lighten": 0.12},
            "button.hoverBackground": {"lighten": 0.08},
        },
        "toggleButtonOn": {
            "base": "#56bd5d",
            "button.activeBackground": {"lighten": 0.16},
            "button.hoverBackground": {"lighten": 0.08},
        },
        "toolbar.activeBackground": "#ffffff34",
        "toolbar.background": "#2a2a2a",
        "toolbar.hoverBackground": "#ffffff22",
        "tree.inactiveIndentGuidesStroke": "#ffffff35",
        "tree.indentGuidesStroke": "#ffffff60",
        "treeSectionHeader.background": "#3f4042",
    },
    "light": {
        "background": {
            "base": "#f8f9fa",
            "list": {},
            "panel": {"lighten": 0.5},
            "popup": {"lighten": 0.2},
            "table": {"lighten": 0.5},
            "textarea": {"lighten": 0.25},
            "title": {"darken": 0.04},
        },
        "border": {
            "base": "#dadce0",
            "input": {},
        },
        "button": {
            "base": "#4d5157",
            "button.activeBackground": {"darken": 0.14, "transparent": 0.23},
            "button.hoverBackground": {"darken": 0.1, "transparent": 0.11},
            "defaultButton.activeBackground": {"darken": 0.12},
            "defaultButton.hoverBackground": {"darken": 0.06},
        },
        "foreground": {
            "base": "#4d5157",
            "defaultButton.disabledBackground": {"transparent": 0.25},
            "disabled": {"transparent": 0.4},
            "disabledSelectionBackground": {"transparent": 0.25},
            "icon": {"darken": 0.05},
            "icon.unfocused": {"transparent": 0.6},
            "input.placeholder": {"transparent": 0.6},
            "progressBar.disabledBackground": {"transparent": 0.25},
            "slider.disabledBackground": {"transparent": 0.25},
            "sliderTrack.inactiveBackground": {"transparent": 0.2},
        },
        "input.background": "#f8f9fa",
        "inputButton.hoverBackground": "#00000018",
        "linkVisited": "#660098",
        "list.alternateBackground": "#00000009",
        "list.hoverBackground": "#00000013",
        "menubar.selectionBackground": "#00000020",
        "popupItem.checkbox.background": "#00000019",
        "popupItem.selectionBackground": "#00000022",
        "primary": {
            "base": "#1a73e8",
            "button.activeBackground": {"darken": 0.03, "transparent": 0.24},
            "button.hoverBackground": {"darken": 0.03, "transparent": 0.1},
            "defaultButton.activeBackground": {"lighten": 0.3},
            "defaultButton.hoverBackground": {"lighten": 0.1},
            "list.inactiveSelectionBackground": {"darken": 0.43, "transparent": 0.09},
            "list.selectionBackground": {"lighten": 0.2, "transparent": 0.35},
            "progressBar.background": {"lighten": 0.2},
            "selection.background": {"lighten": 0.3, "transparent": 0.5},
            "sliderHandle.activeBackground": {"lighten": 0.2},
            "table.inactiveSelectionBackground": {"darken": 0.43, "transparent": 0.09},
            "table.selectionBackground": {"lighten": 0.1, "transparent": 0.5},
            "textarea.selectionBackground": {"lighten": 0.3, "transparent": 0.5},
        },
        "scrollbar.background": "#00000010",
        "scrollbarSlider.activeBackground": "#00000060",
        "scrollbarSlider.background": "#00000040",
        "scrollbarSlider.disabledBackground": "#00000015",
        "scrollbarSlider.hoverBackground": "#00000050",
        "statusBar.background": "#dfe1e5",
        "statusBarItem.activeBackground": "#00000024",
        "statusBarItem.hoverBackground": "#00000015",
        "tab.activeBackground": "#00000000",
        "tab.hoverBackground": "#00000015",
        "tabCloseButton.hoverBackground": "#00000020",
        "table.alternateBackground": "#00000012",
        "tableSectionHeader.background": "#dadce0",
        "textarea.inactiveSelectionBackground": "#00000015",
        "toggleButtonOff": {
            "base": "#f45555",
            "button.activeBackground": {"lighten": 0.12},
            "button.hoverBackground": {"lighten": 0.08},
        },
        "toggleButtonOn": {
            "base": "#56bd5d",
            "button.activeBackground": {"lighten": 0.16},
            "button.hoverBackground": {"lighten": 0.08},
        },
        "toolbar.activeBackground": "#00000024",
        "toolbar.background": "#ebebeb",
        "toolbar.hoverBackground": "#00000015",
        "tree.inactiveIndentGuidesStroke": "#00000030",
        "tree.indentGuidesStroke": "#00000050",
        "treeSectionHeader.background": "#dadce0",
    },
}
ACCENT_COLORS = {
    "dark": {
        "blue": "#8ab4f7",
        "graphite": "#898a8f",
        "green": "#4caf50",
        "orange": "#ff9800",
        "pink": "#c7457f",
        "purple": "#af52bf",
        "red": "#f6685e",
        "yellow": "#ffeb3b",
    },
    "light": {
        "blue": "#1a73e8",
        "graphite": "#898a8f",
        "green": "#4caf50",
        "orange": "#ff9800",
        "pink": "#c7457f",
        "purple": "#9c27b0",
        "red": "#f44336",
        "yellow": "#f4c65f",
    },
}


def color(color_info: str | dict[str, str | dict], state: str | None = None) -> Color:
    """Filter for template engine. This filter convert color info data to color object."""
    if isinstance(color_info, str):
        return Color.from_hex(color_info)

    base_color_format: str = color_info["base"]  # type: ignore
    color = Color.from_hex(base_color_format)

    if state is None:
        return color

    transforms = color_info[state]
    return Color.from_hex(transforms) if isinstance(transforms, str) else _transform(color, transforms)


def url(color: Color, id: str, rotate: int = 0) -> str:
    """Filter for template engine. This filter create url for svg and output svg file."""
    svg_path = Path(__file__).parent.parent / "resources" / "svg" / f"{id}_{color._to_hex()}_{rotate}.svg"
    url = f"url({svg_path.as_posix()})"
    return url


def env(
    text, value: str, version: str | None = None, qt: str | None = None, os: str | None = None
) -> str:
    return value.replace("${}", str(text))


def corner(corner_shape: str, size: str) -> str:
    """Filter for template engine. This filter manage corner shape."""
    return size if corner_shape == "rounded" else "0"


def _transform(color: Color, color_state: dict[str, float]) -> Color:
    if color_state.get("transparent"):
        color = color.transparent(color_state["transparent"])
    if color_state.get("darken"):
        color = color.darken(color_state["darken"])
    if color_state.get("lighten"):
        return color.lighten(color_state["lighten"])
    return color


@dataclass(unsafe_hash=True, frozen=True)
class _Placeholder:
    match_text: str
    value: str | int | float
    filters: tuple[str]


class Template:
    """Class that handles template text like jinja2."""

    _PLACEHOLDER_RE = re.compile(r"{{.*?}}")
    _STRING_RE = re.compile(r"""(('([^'\\]*(?:\\.[^'\\]*)*)'|"([^"\\]*(?:\\.[^"\\]*)*)"){1,3})""", re.S)

    def __init__(self, text: str, filters: dict):
        """Initialize Template class."""
        self._target_text = text
        self._filters = filters

    @staticmethod
    def _to_py_value(text: str):
        try:
            return int(text)
        except ValueError:
            try:
                return float(text)
            except ValueError:
                return text

    @staticmethod
    def _parse_placeholders(text: str):
        placeholders: set[_Placeholder] = set()
        for match in re.finditer(Template._PLACEHOLDER_RE, text):
            match_text = match.group()
            contents, *filters = match_text.strip("{}").replace(" ", "").split("|")
            value = Template._to_py_value(contents)
            placeholders.add(_Placeholder(match_text, value, tuple(filters)))
        return placeholders

    def _run_filter(self, value: str | int | float, filter_text: str):
        contents = filter_text.split("(")
        if len(contents) == 1:
            filter_name = contents[0]
            # Ignore 'url' filter or any other missing filters
            if filter_name not in self._filters:
                return value  # Simply return the value as-is
            return self._filters[filter_name](value)

        filter_name, arg_text = contents[0], contents[1].rstrip(")")

        # Ignore 'url' filter or any other missing filters
        if filter_name not in self._filters:
            return value  # Simply return the value as-is

        # Split arguments by commas, then key-value pairs by '='
        arguments = {}
        if arg_text:
            for arg in arg_text.split(","):
                arg = arg.strip()
                if "=" in arg:
                    # Ensure there is exactly one '=' and split by it
                    key_val_pair = arg.split("=", 1)
                    key = key_val_pair[0].strip()
                    val = key_val_pair[1].strip().strip('"').strip("'")  # Handle string values
                    arguments[key] = val
                else:
                    # Handle positional arguments if needed
                    arguments[arg] = True

        return self._filters[filter_name](value, **arguments)

    def render(self, replacements: dict) -> str:
        """Render replacements."""
        placeholders = Template._parse_placeholders(self._target_text)
        new_replacements: dict[str, str] = {}
        for placeholder in placeholders:
            value = placeholder.value
            if type(value) is str and len(value) != 0:
                value = replacements.get(value)
            if value is None:
                raise AssertionError(
                    f"There is no replacements for: {placeholder.value} in {placeholder.match_text}"
                )
            for filter in placeholder.filters:
                value = self._run_filter(value, filter)
            new_replacements[placeholder.match_text] = str(value)
        return multi_replace(self._target_text, new_replacements)


def multi_replace(target: str, replacements: dict[str, str]) -> str:
    """Given a string and a replacement map, it returns the replaced string.

    See https://gist.github.com/bgusach/a967e0587d6e01e889fd1d776c5f3729.

    Args:
        target: String to execute replacements on.
        replacements: Replacement dictionary {value to find: value to replace}.

    Returns:
        str: Target string that replaced with `replacements`.
    """
    if len(replacements) == 0:
        return target

    replacements_sorted = sorted(replacements, key=len, reverse=True)
    replacements_escaped = [re.escape(i) for i in replacements_sorted]
    pattern = re.compile("|".join(replacements_escaped))
    return pattern.sub(lambda match: replacements[match.group()], target)


def _color_values(theme: str) -> dict[str, str | dict]:
    try:
        return THEME_COLOR_VALUES[theme]
    except KeyError:
        raise ValueError(f'invalid argument, not a dark, light or auto: "{theme}"') from None


def load_stylesheet(theme: str = "dark", corner_shape: str = "rounded",) -> str:
    color_values = _color_values(theme)
    stylesheet = load_base_stylesheet()

    # Build stylesheet
    template = Template(
        stylesheet,
        {"color": color, "corner": corner, "env": env},
    )
    replacements = dict(color_values, **{"corner-shape": corner_shape})
    return template.render(replacements)


def load_base_stylesheet():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'styles.qss')
    with open(file_path, 'r') as f:
        return f.read()
