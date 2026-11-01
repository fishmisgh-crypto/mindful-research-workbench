"""Angular error between intended and decoded 2-D directions."""

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


def angle_between_deg(a: FloatArray, b: FloatArray) -> FloatArray:
    """Unsigned angle in degrees, in [0, 180], row by row. NaN where either vector is zero."""
    norm_a = np.linalg.norm(a, axis=1)
    norm_b = np.linalg.norm(b, axis=1)
    valid = (norm_a > 0) & (norm_b > 0)
    out = np.full(a.shape[0], np.nan)
    cos = np.einsum("ij,ij->i", a[valid], b[valid]) / (norm_a[valid] * norm_b[valid])
    out[valid] = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
    return out
