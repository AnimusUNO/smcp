#!/usr/bin/env python3
"""
Utility functions for Vibing Plugin
"""

import math


def round_to_step(value: float, step: float) -> float:
    """Round value down to nearest step to satisfy LOT_SIZE stepSize."""
    if step <= 0:
        return value
    precision = max(0, len(str(step).split('.')[-1]))
    stepped = math.floor(value / step) * step
    return round(stepped, precision)

