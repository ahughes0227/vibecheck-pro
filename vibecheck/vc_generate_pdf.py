"""PDF generation utilities for VibeCheck Pro.

This module exposes helper functions used when building PDF reports.
Only the pieces required by the test suite are implemented here.
"""

from typing import Dict, Iterable, Optional
import numpy as np


def _lowest_vc_passed(values: Iterable[float], thresholds: Dict[str, float]) -> Optional[str]:
    """Return the lowest VC key that all values satisfy.

    Parameters
    ----------
    values : Iterable[float]
        Sequence of vibration levels.
    thresholds : Dict[str, float]
        Mapping of VC level names to threshold values.

    Returns
    -------
    Optional[str]
        The name of the lowest VC level that all values are below,
        or ``None`` if none are satisfied.
    """
    arr = np.asarray(list(values), dtype=float)
    for level, limit in sorted(thresholds.items(), key=lambda x: x[1]):
        if np.all(arr <= limit):
            return level
    return None
