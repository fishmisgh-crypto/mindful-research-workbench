"""Standalone, self-contained HTML reproduction report (aggregates only).

CLI: python -m mindful.export_report <dataset_root> <processed_dir> <output.html>

Everything is read from the cached reproduction report and analyses; nothing is
recomputed or typed in by hand. No external fonts, scripts or images.
"""

import html
import json
import sys
from pathlib import Path
from typing import Any

from mindful.analysis import ANALYSIS_PRESETS
from mindful.reproduce import ensure_report
from mindful.runs import ensure_analysis

FEATURE_LABEL = {
    "pca5": "PCA-5",
    "extended9": "9-D",
    "velocity2": "Velocity",
    "velocity4": "Velocity + lag",
}
INK, INK3, RULE, ACCENT = "#161513", "#77736a", "#dcd7cb", "#8a2b1f"

CSS = """
:root{--paper:#f6f4ee;--ink:#161513;--ink2:#45423b;--ink3:#77736a;--rule:#dcd7cb;--rule2:#b9b3a5;--accent:#8a2b1f}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:0 auto;padding:56px 24px 80px}
h1,h2{font-family:"Instrument Serif","Iowan Old Style",Charter,Georgia,serif;font-weight:400;letter-spacing:-.01em}
h1{font-size:44px;line-height:1.05;margin:0 0 16px}
h2{font-size:26px;margin:48px 0 12px;padding-top:24px;border-top:1px solid var(--rule)}
p{max-width:70ch;color:var(--ink2)}
.lede{font-size:17px}
.meta{color:var(--ink3);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}
th{font-weight:400;color:var(--ink3);text-align:left;border-bottom:1px solid var(--rule2);padding:6px 10px 6px 0;white-space:nowrap}
td{border-bottom:1px solid var(--rule);padding:6px 10px 6px 0;vertical-align:top}
td.n,th.n{text-align:right;font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace;white-space:nowrap}
.within{color:var(--ink)}.differs{color:var(--accent)}
figure{margin:16px 0 8px}figcaption{color:var(--ink3);font-size:12.5px;margin-top:4px;max-width:90ch}
.scroll{overflow-x:auto}
dl{display:grid;grid-template-columns:14rem 1fr;gap:6px 16px;font-size:13.5px}dt{color:var(--ink3)}dd{margin:0;font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace;word-break:break-word}
@media (max-width:640px){dl{grid-template-columns:1fr}h1{font-size:34px}}
"""


def e(x: Any) -> str:
    return html.escape(str(x))


def f3(v: float | None) -> str:
    return "—" if v is None else f"{v:.3f}"


def sg(v: float | None) -> str:
    return "—" if v is None else f"{v:+.3f}".replace("-", "−")


def comparison_table(
    rows: list[dict[str, Any]], with_preset: bool, with_varies: bool = False
) -> str:
    head = (
        ["Participant", "Features"]
        + (["Preset"] if with_preset else [])
        + (["Change from upstream"] if with_varies else [])
    )
    nums = ["Windows", "r", "published", "Δr", "ρ", "published", "Δρ"]
    out = ["<div class=scroll><table><thead><tr>"]
    out += (
        [f"<th>{h}</th>" for h in head]
        + [f'<th class="n">{h}</th>' for h in nums]
        + ["<th>±0.02</th></tr></thead><tbody>"]
    )
    for r in rows:
        pub = r["published"] or {}
        verdict = {"within tolerance": "within", "differs": "differs"}.get(
            r["verdict"], "no target"
        )
        cells = [e(r["participant"]), e(FEATURE_LABEL[r["feature_set"]])]
        cells += [e(r["preset"])] if with_preset else []
        cells += [e(r["varies"])] if with_varies else []
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells))
        for v in (
            r["n_used"],
            f3(r["pearson_r"]),
            f3(pub.get("pearson")),
            sg(r["delta_r"]),
            f3(r["spearman_rho"]),
            f3(pub.get("spearman")),
            sg(r["delta_rho"]),
        ):
            out.append(f'<td class="n">{e(v)}</td>')
        out.append(f'<td class="{verdict}">{verdict}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def _poly(
    values: list[float | None], x0: float, w: float, top: float, h: float, vmax: float
) -> str:
    n = max(1, len(values) - 1)
    d, pen = [], False
    for i, v in enumerate(values):
        if v is None:
            pen = False
            continue
        d.append(f"{'L' if pen else 'M'}{x0 + i / n * w:.1f},{top + (1 - v / vmax) * h:.1f}")
        pen = True
    return "".join(d)


def _nice(v: float) -> float:
    import math

    if v <= 0:
        return 1.0
    p = 10 ** math.floor(math.log10(v))
    return float(next(f * p for f in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10) if f * p >= v))


def drift_svg(windows: dict[str, list[Any]], title: str) -> str:
    """Stacked KLD and median-AE panels on one window axis; NaN windows are gaps."""
    W, L, R, T, PH, G, B = 900, 56, 10, 26, 150, 28, 40
    H = T + 2 * PH + G + B
    w = W - L - R
    kld, ae, sess, day = (
        windows["kld"],
        windows["median_ae"],
        windows["session_index"],
        windows["day"],
    )
    kmax = _nice(max(v for v in kld if v is not None))
    amax = min(180.0, _nice(max(v for v in ae if v is not None)))
    n = max(1, len(kld) - 1)
    parts = [
        f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{e(title)}" font-family="system-ui,sans-serif">'
    ]
    for i in range(len(sess)):
        if i == 0 or sess[i] != sess[i - 1]:
            x = L + i / n * w
            if i:
                parts.append(
                    f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T - 4}" y2="{T + 2 * PH + G}" stroke="#b9b3a5" stroke-width="1"/>'
                )
            parts.append(
                f'<text x="{x + 2:.1f}" y="{T - 8}" font-size="9" fill="{INK3}" font-family="Consolas,monospace">{day[i]}</text>'
            )
    for top, vmax, label, vals, color in (
        (T, kmax, "KLD (nats)", kld, ACCENT),
        (T + PH + G, amax, "Median AE (°)", ae, INK),
    ):
        for k in range(5):
            v = vmax * k / 4
            y = top + (1 - k / 4) * PH
            parts.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{RULE}"/>')
            parts.append(
                f'<text x="{L - 6}" y="{y + 3:.1f}" font-size="9" text-anchor="end" fill="{INK3}" font-family="Consolas,monospace">{v:g}</text>'
            )
        parts.append(
            f'<path d="{_poly(vals, L, w, top, PH, vmax)}" fill="none" stroke="{color}" stroke-width="1.1"/>'
        )
        parts.append(
            f'<text transform="translate(14 {top + PH / 2}) rotate(-90)" font-size="11" text-anchor="middle" fill="{INK}">{label}</text>'
        )
    parts.append(
        f'<text x="{L + w / 2}" y="{H - 8}" font-size="11" text-anchor="middle" fill="{INK}">Window index (60-s windows; sessions labelled by trial day)</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def scatter_svg(mean_ae: list[float | None], kld: list[float | None], title: str) -> str:
    W, H, L, R, T, B = 420, 260, 52, 10, 10, 40
    pts = [(x, y) for x, y in zip(mean_ae, kld, strict=True) if x is not None and y is not None]
    ymax = _nice(max(y for _, y in pts))
    w, h = W - L - R, H - T - B
    parts = [
        f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:420px" role="img" aria-label="{e(title)}" font-family="system-ui,sans-serif">'
    ]
    for k in range(5):
        y = T + (1 - k / 4) * h
        parts.append(
            f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{RULE}"/><text x="{L - 6}" y="{y + 3:.1f}" font-size="9" text-anchor="end" fill="{INK3}" font-family="Consolas,monospace">{ymax * k / 4:g}</text>'
        )
    for t in (0, 45, 90, 135, 180):
        parts.append(
            f'<text x="{L + t / 180 * w:.1f}" y="{T + h + 14}" font-size="9" text-anchor="middle" fill="{INK3}" font-family="Consolas,monospace">{t}</text>'
        )
    parts += [
        f'<circle cx="{L + x / 180 * w:.1f}" cy="{T + (1 - y / ymax) * h:.1f}" r="2.6" fill="{ACCENT}"/>'
        for x, y in pts
    ]
    parts.append(
        f'<text x="{L + w / 2}" y="{H - 6}" font-size="11" text-anchor="middle" fill="{INK}">Mean angular error of bin (°)</text>'
    )
    parts.append(
        f'<text transform="translate(12 {T + h / 2}) rotate(-90)" font-size="11" text-anchor="middle" fill="{INK}">KLD (nats)</text></svg>'
    )
    return "".join(parts)


def largest_gap(rows: list[dict[str, Any]]) -> float:
    """Largest absolute difference from the published r or rho over the given runs."""
    return float(max(abs(d) for r in rows for d in (r["delta_r"], r["delta_rho"]) if d is not None))


def build_html(root: Path, processed: Path) -> str:
    rep = ensure_report(root, processed)
    rows = rep["rows"]
    max_p = max(max(r["pearson_p"], r["spearman_p"]) for r in rows)
    p_text = (
        "Every p-value underflows to 0 in double precision (p < 1e-300)."
        if max_p == 0
        else f"Largest p-value in the matrix: {max_p:.1e}."
    )
    primary = [r for r in rows if r["group"] == "primary"]
    up = [r for r in primary if r["preset"] == "upstream"]
    n_within = sum(r["verdict"] == "within tolerance" for r in up)
    t11_kept = [
        r for r in rows if r["participant"] == "T11" and r["id"].endswith("excluded_trials")
    ]
    t11_up = [r for r in rows if r["participant"] == "T11" and r["preset"] == "upstream"]
    analyses = {
        p: ensure_analysis(root, processed, p, ANALYSIS_PRESETS["upstream"]) for p in ("T11", "T5")
    }
    manifest = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "REPRODUCIBILITY_MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )

    body = [
        "<h1>MINDFUL, reproduced</h1>",
        '<p class="lede">An independent Python reproduction of the MINDFUL neural-instability measure '
        "(Pun et al., <i>Communications Biology</i> 7, 1363, 2024) from the released recordings and code. "
        "MINDFUL compares each minute of intracortical activity with a reference day using the Kullback–Leibler "
        "divergence (KLD) and asks how closely that drift tracks the cursor's angular error.</p>",
        f'<p class="meta">Generated {e(rep["generated_at"])} · run matrix {e(rep["specs_digest"])} · '
        f"reference code ewinapun/MINDFUL @ {e(rep['upstream_commit'][:7])} · aggregates only, no neural data.</p>",
        "<h2>Summary</h2>",
        f"<p>With the released code's settings (<b>upstream</b> preset), <b>{n_within} of {len(up)}</b> primary results "
        f"are within ±{rep['match_tolerance']} of the published Pearson r and Spearman ρ, and the angular-error-binned "
        "result (Fig. 1b) reproduces to three decimals.</p>",
        f"<p>For participant T11, keeping the outlier trials that the released script removes puts all four feature "
        f"sets within {largest_gap(t11_kept):.3f} of the published values (largest difference {largest_gap(t11_up):.3f} without them). "
        "This suggests the published T11 figures included those trials. It is evidence, not proof; the presets are left "
        "as specified and the change is reported below as a single-parameter run.</p>",
        "<p>A correlation describes how closely KLD tracks decoder error; it is not an accuracy. KLD is a divergence "
        "in nats, not a percentage.</p>",
        f"<h2>Primary results</h2><p class=meta>Fig. 1c (PCA-5) and Fig. 2c (9-D). {e(p_text)}</p>",
        comparison_table(primary, with_preset=True),
    ]
    for p in ("T11", "T5"):
        a = analyses[p]
        days = a["session_days"]
        title = f"{p}: KLD from reference and median angular error per window"
        body.append(
            f"<figure>{drift_svg(a['feature_sets']['pca5']['windows'], title)}<figcaption>{e(title)}. "
            f"{p}, trial days {days[0]}–{days[-1]}, upstream preset (uncentred covariance, windows every 10 s), "
            f"PCA-5. Reference: trial day {' + '.join(map(str, a['reference_days']))}, bins with angular error below 4°. "
            "Gaps are session-end windows, set to NaN as in the original code.</figcaption></figure>"
        )
    body += [
        "<h2>Single-parameter changes</h2><p>Each row changes one setting from the upstream preset.</p>",
        comparison_table(
            [r for r in rows if r["group"] == "ablation"], with_preset=False, with_varies=True
        ),
        "<h2>Velocity-only feature sets</h2><p class=meta>Fig. 2a and 2b, upstream preset.</p>",
        comparison_table([r for r in rows if r["group"] == "secondary"], with_preset=False),
        "<h2>KLD grouped by angular error (Fig. 1b)</h2>",
        "<p>Reference: every kept-trial bin with angular error below 4° across all sessions. The released script "
        "computes 44 bins of 4° (its loop skips 176–180°); the paper states 45. Both are reported.</p>",
    ]
    for r in rep["ae_binned"]:
        if r["n_bins"] == 44:
            t = f"{r['participant']}: KLD of each 4° angular-error bin"
            body.append(
                f"<figure>{scatter_svg(r['bins']['mean_ae'], r['bins']['kld'], t)}<figcaption>{e(t)}; "
                f"r = {f3(r['pearson_r'])} (published {f3((r['published'] or {}).get('pearson'))}).</figcaption></figure>"
            )
    body.append(
        "<table><thead><tr><th>Participant</th><th>Variant</th><th class=n>r</th><th class=n>published</th><th class=n>Δr</th></tr></thead><tbody>"
    )
    for r in rep["ae_binned"]:
        body.append(
            f"<tr><td>{e(r['participant'])}</td><td>{e(r['variant'])}</td><td class=n>{f3(r['pearson_r'])}</td>"
            f"<td class=n>{f3((r['published'] or {}).get('pearson'))}</td><td class=n>{sg(r['delta_r'])}</td></tr>"
        )
    body.append("</tbody></table>")
    ds = manifest["dataset"]
    body += [
        "<h2>Provenance</h2><dl>",
        f"<dt>Paper</dt><dd>{e(manifest['paper']['doi'])}</dd>",
        f"<dt>Reference code</dt><dd>{e(manifest['upstream_code']['url'])} @ {e(manifest['upstream_code']['commit'])}</dd>",
        f"<dt>Dataset</dt><dd>Dryad doi:{e(ds['doi'])} (version {e(ds['dryad_version'])})</dd>",
        f"<dt>Dataset content digest</dt><dd>sha256 {e(ds['extracted_content_digest']['value'])}</dd>",
        f"<dt>Correlation</dt><dd>{e(rep['correlation_method'])}</dd>",
        f"<dt>Tolerance</dt><dd>±{e(rep['match_tolerance'])} on r and ρ (a reporting threshold, not a tuning target)</dd>",
        f"<dt>Published values</dt><dd>{e(rep['source'])}; comparison only, never used in a calculation</dd>",
        "</dl>",
    ]
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>MINDFUL reproduction report</title>"
        f"<style>{CSS}</style></head><body><main>{''.join(body)}</main></body></html>"
    )


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    out = Path(argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(Path(argv[0]), Path(argv[1])), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
