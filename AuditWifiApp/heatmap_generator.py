"""Utilities to generate WiFi signal heatmaps."""

from __future__ import annotations

from typing import List, Tuple, Optional, Dict

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
from typing import cast

from models.wifi_record import WifiRecord


def _parse_coordinates(tag: str, tag_map: Optional[Dict[str, Tuple[float, float]]] = None) -> Optional[Tuple[float, float]]:
    """Return X/Y coordinates parsed from a location tag.

    The tag may contain comma separated numeric coordinates (e.g. ``"10,20"``).
    If this direct parsing fails and ``tag_map`` is provided, the tag will be
    looked up in the mapping.
    """
    if not tag:
        return None
    try:
        x_str, y_str = tag.split(",")
        return float(x_str), float(y_str)
    except Exception:
        pass
    if tag_map:
        coords = tag_map.get(tag)
        if coords is not None:
            return coords
    return None


def generate_heatmap(
    records: List[WifiRecord],
    grid_size: int = 100,
    *,
    tag_map: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Figure:
    """Create a signal heatmap from ``records``.

    Parameters
    ----------
    records:
        Collection of :class:`WifiRecord` instances.
    grid_size:
        Resolution used for the heatmap generation.
    tag_map:
        Optional mapping from arbitrary location tags to ``(x, y)`` coordinates.
        When provided, tags that do not directly contain numeric coordinates will
        be resolved using this mapping.

    Returns
    -------
    :class:`matplotlib.figure.Figure`
        The created heatmap figure.

    Raises
    ------
    ValueError
        If no usable coordinates can be resolved from the records.
    """
    coords: List[Tuple[float, float]] = []
    values: List[float] = []

    for rec in records:
        parsed = _parse_coordinates(rec.location_tag, tag_map)
        if parsed is None or rec.wifi_measurement is None:
            continue
        coords.append(parsed)
        values.append(rec.wifi_measurement.signal_dbm)

    if not coords:
        raise ValueError("No valid coordinates found to generate heatmap.")

    xs, ys = zip(*coords)
    xi = np.linspace(min(xs), max(xs), grid_size)
    yi = np.linspace(min(ys), max(ys), grid_size)
    heatmap = np.full((grid_size, grid_size), np.nan)

    for (x, y), val in zip(coords, values):
        ix = int((x - min(xs)) / (max(xs) - min(xs)) * (grid_size - 1))
        iy = int((y - min(ys)) / (max(ys) - min(ys)) * (grid_size - 1))
        if np.isnan(heatmap[iy, ix]):
            heatmap[iy, ix] = val
        else:
            heatmap[iy, ix] = (heatmap[iy, ix] + val) / 2

        fig, ax = plt.subplots()
    cax = ax.imshow(
        heatmap,
        origin="lower",
        extent=(min(xs), max(xs), min(ys), max(ys)),  # Convert list to tuple
        aspect="auto",
        interpolation="nearest"
    )
    fig.colorbar(cax, ax=ax, label="Signal (dBm)")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("WiFi Signal Heatmap")

    return fig

