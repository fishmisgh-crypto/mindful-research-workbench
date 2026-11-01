"""SYNTHETIC — NOT STUDY DATA. MAT loading: v5 via scipy and v7.3 (HDF5) via h5py agree."""

from pathlib import Path

import h5py
import numpy as np
import scipy.io as sio

from mindful.io.matfile import is_hdf5_mat, load_mat


def write_v73_like(path: Path, arrays: dict[str, np.ndarray], text: dict[str, str]) -> None:
    """HDF5 file laid out like MATLAB v7.3: column-major, so arrays are stored transposed."""
    with h5py.File(path, "w") as f:
        for key, arr in arrays.items():
            ds = f.create_dataset(key, data=arr.T)
            ds.attrs["MATLAB_class"] = np.bytes_("logical" if arr.dtype == bool else "double")
        for key, s in text.items():
            ds = f.create_dataset(key, data=np.array([[ord(c)] for c in s], dtype=np.uint16).T)
            ds.attrs["MATLAB_class"] = np.bytes_("char")


def test_v5_and_v73_give_identical_arrays(tmp_path: Path) -> None:
    rng = np.random.default_rng(1)
    nctx = rng.normal(size=(50, 192))
    flags = rng.random((7, 1)) > 0.5
    sio.savemat(tmp_path / "v5.mat", {"nctx": nctx, "flags": flags, "name": "Fitts"})
    write_v73_like(tmp_path / "v73.mat", {"nctx": nctx, "flags": flags}, {"name": "Fitts"})

    assert not is_hdf5_mat(tmp_path / "v5.mat")
    assert is_hdf5_mat(tmp_path / "v73.mat")
    v5, v73 = load_mat(tmp_path / "v5.mat"), load_mat(tmp_path / "v73.mat")

    assert v73["nctx"].shape == (50, 192)  # rows = bins after transposing back
    np.testing.assert_array_equal(v5["nctx"], v73["nctx"])
    np.testing.assert_array_equal(v5["flags"].astype(bool), v73["flags"])
    assert v73["flags"].dtype == bool
    assert v73["name"] == "Fitts"
    assert str(v5["name"][0]) == "Fitts"


def test_header_entries_are_dropped(tmp_path: Path) -> None:
    sio.savemat(tmp_path / "a.mat", {"x": np.arange(3)})
    assert set(load_mat(tmp_path / "a.mat")) == {"x"}
