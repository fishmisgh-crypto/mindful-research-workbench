"""Read MATLAB .mat files into plain numpy / scipy.sparse objects.

v5–v7 files go through `scipy.io.loadmat`, which keeps MATLAB's row/column
layout. v7.3 files are HDF5; h5py returns them transposed (MATLAB is
column-major), so every array is transposed back here.
"""

from pathlib import Path
from typing import Any

import h5py
import numpy as np
import scipy.io as sio


def is_hdf5_mat(path: Path) -> bool:
    return bool(h5py.is_hdf5(path))


def _hdf5_value(node: Any) -> Any:
    data = node[()]
    matlab_class = node.attrs.get("MATLAB_class", b"")
    if isinstance(matlab_class, bytes):
        matlab_class = matlab_class.decode()
    if matlab_class == "char":
        return "".join(chr(c) for c in np.asarray(data).T.ravel())
    if matlab_class == "logical":
        return np.asarray(data).T.astype(bool)
    return np.asarray(data).T


def _load_hdf5(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as f:
        return {
            key: _hdf5_value(f[key])
            for key in f
            if not key.startswith("#") and isinstance(f[key], h5py.Dataset)
        }


def load_mat(path: Path) -> dict[str, Any]:
    """Return the variables in a .mat file, without MATLAB header entries."""
    if is_hdf5_mat(path):
        return _load_hdf5(path)
    raw = sio.loadmat(path, spmatrix=False)
    return {k: v for k, v in raw.items() if not k.startswith("__")}
