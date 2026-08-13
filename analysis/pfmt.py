"""One p-value renderer, shared by everything that prints a p-value.

This module exists because the same defect was fixed three times in three
places and reappeared in a fourth. A p-value cannot be zero, but
``f"{p:.3f}"`` renders any p below 0.0005 as ``0.000``, and
``round(p, 4)`` writes any p below 5e-05 to disk as exactly ``0.0``.

Two distinct situations have to be told apart, and conflating them is how
the defect kept coming back:

* **Small but known.** The full-precision value survives in the source
  file. Render it at one significant figure so the magnitude is visible:
  ``p_fmt(2.268e-06) -> '2e-06'``.
* **Censored.** An older version of the producing script rounded at write
  time, so the true value is *gone* -- all that is recoverable is the
  bound implied by the rounding that destroyed it. The source records the
  bound and sets a companion ``<col>_is_upper_bound`` flag; render it as
  an inequality: ``p_bound_fmt(5e-05) -> '<0.0001'``. Reporting a bound as
  though it were a measurement would overstate what is known.

Every renderer and every checker imports from here, so the manuscript and
the gate that validates the manuscript cannot disagree about what a
p-value looks like.
"""

from __future__ import annotations

# round(p, 4) -- the write-time rounding that destroyed these values --
# maps everything below this to exactly 0.0.
CENSOR_BOUND = 5e-05


def p_fmt(v, places: int = 3) -> str:
    """Render a known p-value without collapsing a small one to zero.

    Motivating defect (2026-08-12): the raw p of the headline 1%-label
    contrast is 0.0002 and printed as 'p = 0.000' under a fixed 3-decimal
    format -- a value no p-value can take. Below the smallest magnitude
    the requested precision can represent we switch to one significant
    figure so the magnitude survives.

    ``places`` exists because different tables in this project were
    written at 3 and at 4 decimals. The guard against rendering a zero
    has to hold at *every* precision, so it is expressed relative to
    ``places`` rather than hard-coded to one of them.
    """
    v = float(v)
    floor = 10.0 ** (-places)
    return f"{v:.{places}f}" if v >= floor else f"{v:.1g}"


def p_bound_fmt(v=CENSOR_BOUND) -> str:
    """Render a censored p-value as the inequality it actually is."""
    return f"<{float(v):.4f}".rstrip("0") if float(v) >= 1e-04 else "<0.0001"


def p_render(value, is_bound=False, places: int = 3) -> str:
    """Render either kind, dispatching on the source's own bound flag."""
    if is_bound in (True, "True", "true", 1, "1"):
        return p_bound_fmt(value)
    return p_fmt(value, places)
