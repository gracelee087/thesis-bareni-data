"""Render descriptive STUDY-E-1 figures from the stored final analyses.

No model calls, outcome edits, or additional statistical tests. Run from repository root.
"""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "studies/study_e_redesign/private/final125_v1/reports_final_2026-09-08"
OUT = ROOT / "figures"
DATA = {c: json.loads((REPORTS / f"{c}_analysis.json").read_text(encoding="utf-8"))
        for c in ("natural", "mixed")}
plt.rcParams.update({"font.family": "Malgun Gothic", "font.size": 10.5,
                     "axes.unicode_minus": False, "svg.fonttype": "none",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.facecolor": "white"})

fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.9))
fig.subplots_adjust(top=.78, bottom=.23, left=.09, right=.98, wspace=.35)
fig.suptitle("STUDY-E-1: Per-task production cost by condition", fontsize=16, y=.96)
for ax, cond, title, color in zip(axes, DATA,
        ["Natural condition · full production + Curator", "Mixed condition · new revision path"],
        ["#216A8D", "#AC5E22"]):
    d = DATA[cond]
    vals = sorted(i["known_usage_cost_usd"] for i in d["items"])
    assert len(vals) == 125
    assert abs(np.mean(vals) - d["h2"]["per_task_production_cost_descriptive_usd"]["mean"]) < 1e-10
    ax.scatter(range(1, 126), vals, s=14, color=color, alpha=.82)
    ax.axhline(np.mean(vals), color="#303A44", lw=1, ls="--", label="Mean")
    ax.set_title(title + f"\nn=125 · CV={d['h2']['cv']:.5f}", fontsize=11, pad=12)
    ax.set_xlabel("Cost rank within condition")
    ax.set_ylabel("Production cost per task (USD)")
    ax.set_xlim(0, 126)
    ax.set_xticks([1, 25, 50, 75, 100, 125])
    ax.grid(axis="y", color="#DCE2E7", alpha=.7)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
fig.text(.5, .08,
         "Vertical axis ranges differ by panel. Cost scopes differ, so the conditions are not compared as savings.\n"
         "Excludes independent evaluation · includes failures and retries · usage × frozen rates, distinct from final invoices",
         ha="center", fontsize=9.5, color="#3F4E5B")
for ext in ["svg", "png"]:
    fig.savefig(OUT / f"study-e1-production-cost.{ext}", dpi=180)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.6))
fig.subplots_adjust(top=.80, bottom=.23, left=.10, right=.96, wspace=.45)
fig.suptitle("STUDY-E-1: Initial and final quality transitions", fontsize=16, y=.96)
for ax, cond, title in zip(axes, DATA, ["Natural condition", "Mixed condition"]):
    d = DATA[cond]["h3"]["valid_pairs_descriptive"]
    counts = np.array([[d["stayed_low"], d["repaired"]], [d["harmed"], d["stayed_pass"]]])
    assert int(counts.sum()) == 125
    colors = np.array([[[.97,.88,.86], [.84,.92,.88]], [[.97,.88,.86], [.84,.92,.88]]])
    ax.imshow(colors, aspect="equal")
    ax.set_xticks([0, 1], ["Final low quality", "Final pass"])
    ax.set_yticks([0, 1], ["Initial low quality", "Initial pass"])
    ax.set_title(f"{title} · 125 pairs", fontsize=12, pad=16)
    for row in range(2):
        for col in range(2):
            ax.text(col, row, f"{counts[row,col]}", ha="center", va="center", fontsize=24, color="#172D3D")
    ax.set_xticks(np.arange(-.5, 2, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 2, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=4)
    ax.tick_params(which="both", length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
fig.text(.5, .07,
         "Low quality: any of four dimensions below 3. Transitions are observed counts, not an additional test.\n"
         "Both conditions use the same 125 source tasks and are shown separately, not pooled as N = 250.",
         ha="center", fontsize=9.5, color="#3F4E5B")
for ext in ["svg", "png"]:
    fig.savefig(OUT / f"study-e1-h3-transitions.{ext}", dpi=180)
plt.close(fig)

manifest = {"description": "Descriptive visualisations only; stored final analyses are unchanged.",
            "sources": {str((REPORTS / f"{c}_analysis.json").relative_to(ROOT)).replace("\\", "/"):
                        hashlib.sha256((REPORTS / f"{c}_analysis.json").read_bytes()).hexdigest() for c in DATA},
            "outputs": [f"figures/study-e1-{s}.{e}" for s in ("production-cost", "h3-transitions")
                        for e in ("svg", "png")]}
(OUT / "study-e1-figure-sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
