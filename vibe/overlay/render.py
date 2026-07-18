from __future__ import annotations

import html

from vibe.core.pawgress.events import Criterion, IslandState, IslandStatus

ORANGE = "#FF8205"
GREEN = "#2ecc71"
RED = "#e74c3c"
AMBER = "#f1c40f"
BLUE = "#5aa9e6"
MUTED = "#8a8a8a"
FG = "#e6e6e6"

_STATE_STYLE: dict[IslandStatus, tuple[str, str, str]] = {
    IslandStatus.WORKING: ("working", "", ORANGE),
    IslandStatus.VERIFYING: ("verifying", "[...]", BLUE),
    IslandStatus.WAITING: ("Vibe needs you", "!", AMBER),
    IslandStatus.BLOCKED: ("blocked", "✗", RED),
    IslandStatus.PAUSED: ("paused", "zZ", MUTED),
    IslandStatus.COMPLETED: ("complete", "✓", GREEN),
}


def _parse_fraction(text: str | None) -> tuple[int, int] | None:
    if not text or "/" not in text:
        return None
    left, _, right = text.partition("/")
    if left.strip().isdigit() and right.strip().isdigit():
        return int(left), int(right)
    return None


def progress_bar(current: int, total: int, width: int = 10) -> str:
    if total <= 0:
        return "░" * width
    filled = min(width, round(width * current / total))
    return "█" * filled + "░" * (width - filled)


def _verification_fraction(state: IslandState) -> tuple[int, int] | None:
    for criterion in state.criteria:
        frac = _parse_fraction(criterion.progress)
        if frac is not None:
            return frac
    return None


def _criterion_marker(criterion: Criterion) -> str:
    if criterion.done:
        return "✓"
    if criterion.progress:
        return "●"
    return "○"


def _meta_line(state: IslandState) -> str:
    parts: list[str] = []
    if state.iteration:
        parts.append(f"iter {state.iteration}")
    if state.cost is not None and state.budget is not None:
        parts.append(f"${state.cost:.2f}/${state.budget:.2f}")
    return " · ".join(parts)


def render_island(state: IslandState, cat_frame: str) -> str:
    label, symbol, _ = _STATE_STYLE[state.state]
    lines: list[str] = []
    head = f"\U0001f43e Pawgress · {label}"
    if symbol:
        head += f"  {symbol}"
    lines.append(head)
    lines.append(state.goal)

    frac = _verification_fraction(state)
    bar = f"   {progress_bar(*frac)} {frac[0]}/{frac[1]}" if frac is not None else ""
    cat_lines = cat_frame.splitlines() or [""]
    mid = len(cat_lines) // 2
    for i, cat_line in enumerate(cat_lines):
        lines.append(f" {cat_line}{bar if i == mid else ''}")

    for criterion in state.criteria:
        suffix = (
            f"  {criterion.progress}"
            if criterion.progress and not criterion.done
            else ""
        )
        lines.append(f"{_criterion_marker(criterion)} {criterion.label}{suffix}")

    meta = _meta_line(state)
    if meta:
        lines.append(meta)

    if state.state is IslandStatus.COMPLETED:
        for item in state.evidence:
            lines.append(f"✓ {item}")

    if state.state is IslandStatus.WAITING:
        lines.append("[Open Vibe]")
    else:
        lines.append("[Pause] [Stop] [Open Vibe]")
    return "\n".join(lines)


def render_collapsed(state: IslandState) -> str:
    label, symbol, _ = _STATE_STYLE[state.state]
    frac = _verification_fraction(state)
    tail = f" {frac[0]}/{frac[1]}" if frac is not None else ""
    sym = f" {symbol}" if symbol else ""
    return f"\U0001f43e Pawgress · {label}{tail}{sym}"


def _span(text: str, color: str) -> str:
    return f'<span style="color:{color}">{html.escape(text)}</span>'


_DECOR_FRAMES: dict[IslandStatus, tuple[str, ...]] = {
    IslandStatus.WORKING: ("✦", "✧", " "),
    IslandStatus.VERIFYING: ("[.  ]", "[.. ]", "[...]"),
    IslandStatus.WAITING: ("!", " "),
    IslandStatus.BLOCKED: ("✗",),
    IslandStatus.PAUSED: ("zZ", "z "),
    IslandStatus.COMPLETED: ("+ ✦ +", " ✦✦ "),
}
_RETRY_FRAMES = ("↻", "⟳")


def _is_retrying(state: IslandState) -> bool:
    frac = _verification_fraction(state)
    return (
        state.state is IslandStatus.WORKING
        and frac is not None
        and 0 < frac[0] < frac[1]
    )


def _decoration(state: IslandState, tick: int) -> str:
    if _is_retrying(state):
        return _RETRY_FRAMES[(tick // 3) % len(_RETRY_FRAMES)]
    frames = _DECOR_FRAMES[state.state]
    return frames[(tick // 3) % len(frames)]


def render_island_html(state: IslandState, cat_frame: str, tick: int = 0) -> str:
    label, symbol, color = _STATE_STYLE[state.state]
    if _is_retrying(state):
        label, color = "trying another fix", BLUE
    rows: list[str] = []
    head = f"\U0001f43e Pawgress · {label}"
    if symbol:
        head += f"  {symbol}"
    rows.append(_span(head, color) + "  " + _button("[×]", "quit", MUTED))
    rows.append(_span(state.goal, FG))

    frac = _verification_fraction(state)
    bar = ""
    if frac is not None:
        bar = "   " + _span(f"{progress_bar(*frac)} {frac[0]}/{frac[1]}", color)
    cat_lines = cat_frame.splitlines() or [""]
    mid = len(cat_lines) // 2
    decor = "  " + _span(_decoration(state, tick), color)
    for i, cat_line in enumerate(cat_lines):
        suffix = bar if i == mid else (decor if i == 0 else "")
        rows.append(_span(f" {cat_line}", ORANGE) + suffix)

    for criterion in state.criteria:
        marker = _criterion_marker(criterion)
        mark_color = (
            GREEN if criterion.done else (color if criterion.progress else MUTED)
        )
        suffix = (
            f"  {criterion.progress}"
            if criterion.progress and not criterion.done
            else ""
        )
        rows.append(
            _span(marker, mark_color) + " " + _span(criterion.label + suffix, FG)
        )

    meta = _meta_line(state)
    if meta:
        rows.append(_span(meta, MUTED))

    if state.state is IslandStatus.COMPLETED:
        for item in state.evidence:
            rows.append(_span(f"✓ {item}", GREEN))

    rows.append(_buttons_html(state))
    return "<br>".join(rows)


def _button(label: str, href: str, color: str) -> str:
    return f'<a href="{href}" style="color:{color};text-decoration:none">{html.escape(label)}</a>'


def _buttons_html(state: IslandState) -> str:
    if state.state is IslandStatus.WAITING:
        return _button("[Open Vibe]", "focus_vibe", BLUE)
    return " ".join([
        _button("[Pause]", "pause", MUTED),
        _button("[Stop]", "stop", RED),
        _button("[Open Vibe]", "focus_vibe", BLUE),
    ])
