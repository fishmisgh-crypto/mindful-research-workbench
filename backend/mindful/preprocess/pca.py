"""PCA fitted on reference bins only, matching MATLAB `pca` + `MINDFUL.PCAtransform`.

MATLAB centres by the column mean, uses the SVD, and flips each component so its
largest-magnitude loading is positive. Projection: (X - mu) @ coeff[:, :k]. No whitening.
"""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


@dataclass(frozen=True)
class PcaModel:
    mean: FloatArray  # (n_features,)
    components: FloatArray  # (n_features, n_components), columns = PCs
    explained_pct: FloatArray  # variance explained by every component, sums to 100
    n_reference_bins: int

    def transform(self, x: FloatArray, n_dim: int) -> FloatArray:
        if n_dim > self.components.shape[1]:
            raise ValueError(f"requested {n_dim} PCs, model has {self.components.shape[1]}")
        out: FloatArray = (x - self.mean) @ self.components[:, :n_dim]
        return out


def fit_pca(reference: FloatArray) -> PcaModel:
    """Fit on reference bins (rows) only."""
    x = np.asarray(reference, dtype=np.float64)
    if x.shape[0] < 2:
        raise ValueError("PCA needs at least two reference bins")
    mean = x.mean(axis=0)
    _, s, vt = np.linalg.svd(x - mean, full_matrices=False)
    coeff = vt.T
    largest = np.argmax(np.abs(coeff), axis=0)
    signs = np.sign(coeff[largest, np.arange(coeff.shape[1])])
    signs[signs == 0] = 1.0
    coeff = coeff * signs
    var = s**2
    total = var.sum()
    explained = 100.0 * var / total if total > 0 else np.zeros_like(var)
    return PcaModel(
        mean=mean, components=coeff, explained_pct=explained, n_reference_bins=x.shape[0]
    )
