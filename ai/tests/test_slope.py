"""Tests for slope classification helpers."""

from ai.src.slope import get_slope_level


def test_get_slope_level_gentle() -> None:
    assert get_slope_level(2.0) == "완만"


def test_get_slope_level_normal() -> None:
    assert get_slope_level(5.0) == "보통"


def test_get_slope_level_caution() -> None:
    assert get_slope_level(7.0) == "주의"


def test_get_slope_level_steep() -> None:
    assert get_slope_level(9.0) == "급경사"
