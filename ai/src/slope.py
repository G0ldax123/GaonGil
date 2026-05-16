"""Slope helpers and future provider extension points."""

from __future__ import annotations


def get_slope_level(slope_percent: float) -> str:
    """Convert numeric slope percent to the fixed Korean label."""

    if slope_percent <= 3:
        return "완만"
    if slope_percent <= 6:
        return "보통"
    if slope_percent <= 8:
        return "주의"
    return "급경사"


class VWorldSlopeProvider:
    """Placeholder interface for future live VWorld slope integration."""

    def get_slope_percent(self, latitude: float, longitude: float) -> float:
        raise NotImplementedError("TODO: integrate live VWorld slope provider")
