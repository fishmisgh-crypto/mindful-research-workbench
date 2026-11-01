"""SYNTHETIC — NOT STUDY DATA. Standalone report building blocks."""

from mindful.export_report import comparison_table, drift_svg

ROW = {
    "participant": "T11",
    "feature_set": "pca5",
    "preset": "upstream",
    "varies": "<script>alert(1)</script>",
    "n_used": 10,
    "pearson_r": 0.9,
    "spearman_rho": 0.8,
    "published": {"pearson": 0.91, "spearman": 0.9},
    "delta_r": -0.01,
    "delta_rho": -0.1,
    "verdict": "differs",
}


def test_table_escapes_text_and_marks_verdict() -> None:
    html = comparison_table([ROW], with_preset=True, with_varies=True)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert 'class="differs"' in html
    assert "−0.100" in html  # typographic minus for negative differences


def test_drift_svg_leaves_nan_windows_as_gaps() -> None:
    windows = {
        "kld": [0.1, 0.2, None, None, 0.3, 0.4],
        "median_ae": [10.0, 20.0, None, None, 30.0, 40.0],
        "session_index": [1, 1, 1, 2, 2, 2],
        "day": [5, 5, 5, 9, 9, 9],
    }
    svg = drift_svg(windows, "synthetic")
    paths = [p.split('"')[0] for p in svg.split('<path d="')[1:]]
    assert len(paths) == 2
    assert all(p.count("M") == 2 for p in paths)  # two segments each: the gap is not bridged
