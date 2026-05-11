from __future__ import annotations

import argparse
import textwrap
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle


OUTDIR = Path(__file__).resolve().parent

PALETTE = {
    "navy": "#243b53",
    "slate": "#52606d",
    "teal": "#3a7d7c",
    "gold": "#c5a46d",
    "gray": "#9aa5b1",
    "light_blue": "#d9e2ec",
    "light_teal": "#d3eceb",
    "light_gold": "#efe5d0",
    "light_gray": "#f0f4f8",
    "grid": "#d9e2ec",
    "text": "#1f2933",
    "muted": "#7b8794",
    "rust": "#b85c38",
    "light_rust": "#f6ddd4",
    "green": "#2f855a",
}


FIGURE_SPECS = [
    {
        "filename": "fig_01_journey_timeline.svg",
        "title": "Journey timeline from scaffold to writing convergence",
        "caption": (
            "Timeline of the thesis journey from the first repository scaffold on 2025-10-23 "
            "to the writing push on 2026-04-18. The milestones show the shift from setup and "
            "sensor debugging toward governance hardening, retraining evidence, and final writing convergence."
        ),
        "insertion": "Section 4.1 Timeline Overview",
        "why": (
            "Breaks up the longest section in the memo and gives the reader a fast chronological anchor "
            "before the detailed phase-by-phase narrative."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_02_document_layers.svg",
        "title": "Document layers in the thesis journey memo",
        "caption": (
            "Conceptual view of the memo's three layers: thesis facts, development history, and internal readiness. "
            "The figure clarifies that the support document mixes different text types and should not be pasted directly into thesis body prose."
        ),
        "insertion": "Section 1.5 Document Layers",
        "why": (
            "Helps the reader distinguish between thesis-usable evidence, project-history material, and internal planning content."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_03_scope_map.svg",
        "title": "In-scope versus out-of-scope thesis boundary",
        "caption": (
            "Scope map contrasting the defended thesis boundary with explicitly excluded or reduced ambitions. "
            "It highlights the thesis as an offline-first, single-machine, governed HAR lifecycle rather than a full cloud or clinical deployment."
        ),
        "insertion": "Section 2.3 In Scope vs Out of Scope",
        "why": (
            "Makes the defended scope visible at a glance and reduces the risk that a reader over-reads the contribution."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_04_stage_evolution.svg",
        "title": "Stage evolution from broad design to defended thesis framing",
        "caption": (
            "Comparison of the historical 14-stage design, the thesis presentation target of seven core plus three conditional stages, "
            "and the current 11-stage runtime that still exposes calibration. The figure shows how the project moved from broad ambition to a tighter and more defensible thesis scope."
        ),
        "insertion": "Section 3.2 Current Runtime Shape vs Historical Design Shape",
        "why": (
            "This is one of the key conceptual clarifiers in the memo and helps reconcile differing stage counts across older notes, the runtime, and the thesis framing."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_05_core_vs_conditional_pipeline.svg",
        "title": "Core runtime versus governed mutation branch",
        "caption": (
            "Stage-based architecture showing the seven-stage operational core and the conditional retraining branch for stages 8-10, with calibration shown separately as optional. "
            "The visual makes explicit that model mutation is governed rather than automatic."
        ),
        "insertion": "Section 5.5 Why Stage-Based Orchestration or Section 5.6 Why 7 Core + 3 Conditional Is Better Than a Flat 10 or 14",
        "why": (
            "This is the cleanest visual statement of the thesis identity: observation and assessment happen routinely, while mutation happens only under policy control."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_06_data_pipeline.svg",
        "title": "Train-serve consistent preprocessing pipeline",
        "caption": (
            "Compact data-flow view from raw wrist IMU files through validation, unit conversion, normalization, resampling, and windowing to the saved `production_X.npy` tensor. "
            "The figure explains why preprocessing consistency is a thesis-level engineering concern rather than an implementation detail."
        ),
        "insertion": "Section 6.2 Preprocessing Path",
        "why": (
            "Provides a compact visual explanation of the production preprocessing chain and reduces the need for the reader to reconstruct it from prose alone."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_07_ablation_config_comparison.svg",
        "title": "A/B/C/D preprocessing ablation comparison",
        "caption": (
            "Two aligned bar charts comparing the four preprocessing configurations on mean unique classes predicted and mean hand_tapping share. "
            "Config D gives the strongest class diversity, while Config C shows that gravity removal alone worsened collapse in this setup."
        ),
        "insertion": "Section 7.2 Preprocessing Ablation A/B/C/D",
        "why": (
            "Transforms one of the strongest numerical findings into a fast visual argument about why the chosen configuration is defensible."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_08_trigger_policy_comparison.svg",
        "title": "Trigger policy comparison",
        "caption": (
            "Coordinated policy comparison using precision, tradeoff F1, false alarm rate, and episode recall from the memo's trigger-policy table. "
            "The figure shows why `two_of_three` is the strongest available balance among the tested policies."
        ),
        "insertion": "Section 7.3 Trigger Policy Evaluation",
        "why": (
            "Makes the governance trade-off visible without forcing the reader to scan a dense numerical table."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_09_actual_vs_synthetic.svg",
        "title": "Actual versus synthetic dataset comparison",
        "caption": (
            "Comparison of actual labeled data with two synthetic datasets across accuracy, macro F1, mean confidence, uncertain rate, and drift. "
            "The pattern shows that degraded realism is associated with worse performance and higher uncertainty."
        ),
        "insertion": "Section 7.4 Actual vs Synthetic Comparison",
        "why": (
            "Gives a compact visual explanation of the synthetic-data result without collapsing very different metrics into a less readable radar chart."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_10_old_vs_new_model_comparison.svg",
        "title": "Same-input old versus new model comparison",
        "caption": (
            "Flagship same-input comparison between the historical pretrained model and the retrained model on the same raw pair. "
            "The old model is more overconfident and collapses into a dominant class, whereas the retrained model is less overconfident and behaviorally broader."
        ),
        "insertion": "Section 7.5 Same-Input Old-vs-New Model Comparison",
        "why": (
            "This is one of the cleanest pieces of thesis evidence and should stand out as a major visual result."
        ),
        "internal_only": False,
        "notes": "",
    },
    {
        "filename": "fig_11_challenges_resolutions_matrix.svg",
        "title": "Challenges and resolutions matrix",
        "caption": (
            "Compact engineering map grouping the challenge log into train-serve mismatch, orchestration bugs, model collapse and adaptation, environment drift, and scope control. "
            "The figure underscores that the thesis preserves negative evidence and correction work rather than presenting only final positive claims."
        ),
        "insertion": "Section 8 Challenges and Resolutions Log",
        "why": (
            "Visually reinforces the engineering struggle-and-correction story that makes the memo more credible."
        ),
        "internal_only": False,
        "notes": "Theme grouping is editorial; individual issue and resolution statements come directly from the memo.",
    },
    {
        "filename": "fig_12_thesis_readiness_dashboard.svg",
        "title": "Internal readiness snapshot",
        "caption": (
            "Internal progress view across code, experiments, writing, documentation, and defense preparation using the memo's readiness estimates. "
            "This is a planning figure for supervision and execution, not a thesis-evidence figure."
        ),
        "insertion": "Section 11.1 Practical Internal Completion Estimate by Thesis Component",
        "why": (
            "Useful in the support memo and for supervisor updates because it compresses the planning state into one view."
        ),
        "internal_only": True,
        "notes": "",
    },
    {
        "filename": "fig_13_risk_matrix.svg",
        "title": "Internal risk exposure map",
        "caption": (
            "Risk map based on the memo's internal risk register, grouping risks by stated current level and affected area. "
            "The memo does not provide separate numeric impact and probability scores, so the figure stays at the level explicitly supported by the source text."
        ),
        "insertion": "Section 11.5 Internal Risk Register",
        "why": (
            "Useful for supervision, appendix planning, and defense preparation because it makes completion risks visible without burying them in prose."
        ),
        "internal_only": True,
        "notes": "Separate impact/probability scores are not specified in the memo.",
    },
    {
        "filename": "fig_14_evidence_to_chapter_map.svg",
        "title": "Evidence-to-chapter writing map",
        "caption": (
            "Writing-execution diagram linking the strongest evidence families to their target thesis chapters. "
            "The map turns the memo into a practical drafting aid by showing where architecture, experiments, monitoring, and limitations should land in the manuscript."
        ),
        "insertion": "Section 11.6 Immediate Next Actions or near Section 3.3 Current Thesis Writing Index",
        "why": (
            "Helps convert the memo into a chapter-writing plan and is especially useful for supervisor discussion or internal execution."
        ),
        "internal_only": True,
        "notes": "This is an editorial mapping aid derived from the chapter structure and requested chapter mapping.",
    },
]


ESSENTIAL_SUPPORT = [
    "fig_01_journey_timeline.svg",
    "fig_04_stage_evolution.svg",
    "fig_05_core_vs_conditional_pipeline.svg",
    "fig_07_ablation_config_comparison.svg",
    "fig_10_old_vs_new_model_comparison.svg",
    "fig_14_evidence_to_chapter_map.svg",
]

BEST_FOR_THESIS_BODY = [
    "fig_04_stage_evolution.svg",
    "fig_05_core_vs_conditional_pipeline.svg",
    "fig_07_ablation_config_comparison.svg",
    "fig_10_old_vs_new_model_comparison.svg",
]

INTERNAL_ONLY = [
    "fig_12_thesis_readiness_dashboard.svg",
    "fig_13_risk_matrix.svg",
    "fig_14_evidence_to_chapter_map.svg",
]

PARTIAL_SOURCE_NOTES = {
    "fig_11_challenges_resolutions_matrix.svg": (
        "Theme grouping is editorial. The underlying challenge and resolution statements are taken directly from the memo."
    ),
    "fig_13_risk_matrix.svg": (
        "The memo specifies current risk level but does not provide separate numeric impact and probability scores."
    ),
    "fig_14_evidence_to_chapter_map.svg": (
        "The mapping is an editorial writing aid derived from the memo's chapter structure and the requested chapter-to-evidence mapping."
    ),
}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 10.5,
            "axes.edgecolor": PALETTE["slate"],
            "axes.linewidth": 0.8,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "grid.color": PALETTE["grid"],
            "grid.linewidth": 0.7,
            "grid.alpha": 0.8,
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "text.color": PALETTE["text"],
            "svg.fonttype": "none",
        }
    )


def wrap_text(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def add_box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    facecolor: str,
    edgecolor: str,
    title: str | None = None,
    fontsize: float = 10.0,
    ha: str = "center",
    title_color: str | None = None,
    rounded: bool = True,
    linestyle: str = "-",
) -> None:
    if rounded:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.2,
            linestyle=linestyle,
        )
    else:
        patch = Rectangle(
            (x, y),
            w,
            h,
            transform=ax.transAxes,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=1.2,
            linestyle=linestyle,
        )
    ax.add_patch(patch)

    if title:
        ax.text(
            x + 0.03 * w,
            y + h - 0.08 * h,
            title,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=fontsize + 0.6,
            fontweight="bold",
            color=title_color or edgecolor,
        )
        body_y = y + 0.44 * h
    else:
        body_y = y + 0.5 * h

    x_text = x + (w / 2 if ha == "center" else 0.04 * w)
    ax.text(
        x_text,
        body_y,
        text,
        transform=ax.transAxes,
        ha=ha,
        va="center",
        fontsize=fontsize,
        color=PALETTE["text"],
    )


def add_arrow(ax, start: tuple[float, float], end: tuple[float, float], *, color: str = None, lw: float = 1.5, linestyle: str = "-") -> None:
    patch = FancyArrowPatch(
        start,
        end,
        transform=ax.transAxes,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        linestyle=linestyle,
        color=color or PALETTE["slate"],
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(patch)


def add_callout(ax, x: float, y: float, text: str, *, color: str = None, fontsize: float = 9.3, ha: str = "left") -> None:
    ax.text(
        x,
        y,
        text,
        transform=ax.transAxes,
        ha=ha,
        va="center",
        fontsize=fontsize,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": color or PALETTE["gold"],
            "linewidth": 1.0,
        },
    )


def format_pct(value: float) -> str:
    return f"{value:.1f}%"


def format_num(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}"


def save(fig: plt.Figure, filename: str, *, with_png: bool = False) -> None:
    svg_path = OUTDIR / filename
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    if with_png:
        png_path = svg_path.with_suffix(".png")
        fig.savefig(png_path, format="png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def generate_timeline(with_png: bool) -> None:
    events = [
        ("2025-10-23", "First scaffold and preprocessing foundations"),
        ("2025-11-05", "Accelerometer mismatch discovered"),
        ("2025-12-06", "Unit-conversion solution documented"),
        ("2025-12-08", "First inference and evaluation pipeline"),
        ("2025-12-11", "DVC, MLflow, Docker foundations"),
        ("2026-02-12", "Complete 10-stage pipeline with AdaBN branch"),
        ("2026-02-14", "225/225 tests milestone"),
        ("2026-02-15", "FastAPI and CI/CD"),
        ("2026-02-19", "Governance and monitoring fixes"),
        ("2026-02-22", "Class count corrected to 11"),
        ("2026-03-05", "Cleanup and CI/CD split"),
        ("2026-03-06", "v1.0.0-thesis tag"),
        ("2026-03-27", "Retrained model generated"),
        ("2026-03-28", "Ablation and 26-session comparison"),
        ("2026-04-03", "External review bug wave"),
        ("2026-04-16", "Scope cleanup"),
        ("2026-04-17", "Same-input old-vs-new comparison"),
        ("2026-04-18", "Review fixes and writing push"),
    ]
    dates = [datetime.strptime(date, "%Y-%m-%d") for date, _ in events]
    labels = [label for _, label in events]

    fig, ax = plt.subplots(figsize=(15.5, 6.8))
    ax.axhline(0, color=PALETTE["navy"], linewidth=2.0)

    for idx, (dt, label) in enumerate(zip(dates, labels)):
        ypos = 1.0 if idx % 2 == 0 else -1.0
        ax.plot([dt, dt], [0, ypos * 0.78], color=PALETTE["slate"], linewidth=1.0)
        color = PALETTE["teal"] if dt.year == 2026 and dt.month >= 3 else PALETTE["navy"]
        ax.scatter(dt, 0, s=42, color=color, zorder=3)
        ax.text(
            dt,
            ypos,
            f"{events[idx][0]}\n{wrap_text(label, 28)}",
            ha="center",
            va="bottom" if ypos > 0 else "top",
            fontsize=9.1,
        )

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(-1.5, 1.5)
    ax.set_yticks([])
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.set_title("Fig. 1  Thesis journey timeline", loc="left", pad=16)

    phase_labels = [
        ("Setup", PALETTE["light_blue"]),
        ("Engineering", PALETTE["light_teal"]),
        ("Governance", PALETTE["light_gold"]),
        ("Evidence", PALETTE["light_rust"]),
        ("Writing convergence", PALETTE["light_gray"]),
    ]
    x_cursor = 0.02
    for label, color in phase_labels:
        ax.text(
            x_cursor,
            0.94,
            label,
            transform=ax.transAxes,
            ha="left",
            va="center",
            fontsize=9.4,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": color, "edgecolor": PALETTE["grid"]},
        )
        x_cursor += 0.18

    add_callout(
        ax,
        0.73,
        0.08,
        "Progression: setup -> engineering -> governance -> evidence -> writing convergence",
        color=PALETTE["navy"],
        fontsize=8.9,
    )

    save(fig, "fig_01_journey_timeline.svg", with_png=with_png)


def generate_document_layers(with_png: bool) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 7.2))
    ax.axis("off")
    ax.set_title("Fig. 2  Document layers in the thesis journey memo", loc="left", pad=14)

    add_box(
        ax,
        0.18,
        0.68,
        0.64,
        0.18,
        "Problem framing, scope, architecture,\nexperiments, findings, limitations\n\nBest use: source material for thesis body chapters",
        facecolor=PALETTE["light_blue"],
        edgecolor=PALETTE["navy"],
        title="Layer A  Thesis facts",
        ha="left",
    )
    add_box(
        ax,
        0.18,
        0.42,
        0.64,
        0.18,
        "Timeline, bugs, fixes, scope shifts,\nrepo evolution\n\nBest use: supervision, appendix support, defense preparation",
        facecolor=PALETTE["light_teal"],
        edgecolor=PALETTE["teal"],
        title="Layer B  Development history",
        ha="left",
    )
    add_box(
        ax,
        0.18,
        0.16,
        0.64,
        0.18,
        "Completion estimates, time/risk planning,\nnext actions\n\nBest use: project management and execution only",
        facecolor=PALETTE["light_gold"],
        edgecolor=PALETTE["gold"],
        title="Layer C  Internal readiness",
        ha="left",
    )
    add_arrow(ax, (0.50, 0.68), (0.50, 0.60), color=PALETTE["slate"])
    add_arrow(ax, (0.50, 0.42), (0.50, 0.34), color=PALETTE["slate"])

    add_callout(
        ax,
        0.50,
        0.06,
        "Use the memo as a source document, not as thesis-ready body prose.",
        color=PALETTE["rust"],
        fontsize=10.0,
        ha="center",
    )

    save(fig, "fig_02_document_layers.svg", with_png=with_png)


def generate_scope_map(with_png: bool) -> None:
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.axis("off")
    ax.set_title("Fig. 3  In-scope versus out-of-scope thesis boundary", loc="left", pad=14)

    in_scope = "\n".join(
        [
            "- Offline-first pipeline execution",
            "- Single-machine reproducibility",
            "- HAR classifier governance",
            "- Label-free monitoring signals",
            "- Conditional retraining branch",
            "- Thesis-ready engineering evidence",
            "- Wrist-based Garmin batch and file upload workflow",
        ]
    )
    out_scope = "\n".join(
        [
            "- Full cloud deployment",
            "- Kubernetes / cluster orchestration",
            "- Clinically validated prognosis model",
            "- Fully automated trustworthy self-improving system",
            "- Unrestricted auto-deploy of every new model",
            "- SOTA transformer benchmarking",
            "- End-to-end streaming Garmin Connect production system",
        ]
    )

    add_box(
        ax,
        0.06,
        0.17,
        0.40,
        0.68,
        in_scope,
        facecolor=PALETTE["light_teal"],
        edgecolor=PALETTE["teal"],
        title="Defended scope",
        ha="left",
    )
    add_box(
        ax,
        0.54,
        0.17,
        0.40,
        0.68,
        out_scope,
        facecolor=PALETTE["light_gray"],
        edgecolor=PALETTE["slate"],
        title="Out of scope or intentionally reduced",
        ha="left",
    )
    ax.text(
        0.50,
        0.51,
        "Defensible thesis boundary",
        transform=ax.transAxes,
        rotation=90,
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color=PALETTE["navy"],
    )
    add_callout(
        ax,
        0.50,
        0.07,
        "The thesis centers on governed wearable HAR lifecycle engineering, not cloud scale or clinical prognosis claims.",
        color=PALETTE["navy"],
        ha="center",
    )

    save(fig, "fig_03_scope_map.svg", with_png=with_png)


def draw_stage_grid(ax, x: float, y: float, n_stages: int, *, title: str, subtitle: str, colors: list[str]) -> None:
    ax.text(x, y + 0.26, title, transform=ax.transAxes, fontsize=11.2, fontweight="bold", ha="left")
    ax.text(x, y + 0.22, subtitle, transform=ax.transAxes, fontsize=9.1, color=PALETTE["muted"], ha="left")

    cols = 7
    box_w = 0.045
    box_h = 0.07
    gap_x = 0.008
    gap_y = 0.02
    for idx in range(n_stages):
        row = idx // cols
        col = idx % cols
        bx = x + col * (box_w + gap_x)
        by = y + 0.10 - row * (box_h + gap_y)
        patch = FancyBboxPatch(
            (bx, by),
            box_w,
            box_h,
            transform=ax.transAxes,
            boxstyle="round,pad=0.01,rounding_size=0.015",
            facecolor=colors[idx],
            edgecolor=PALETTE["slate"],
            linewidth=1.0,
        )
        ax.add_patch(patch)
        ax.text(
            bx + box_w / 2,
            by + box_h / 2,
            str(idx + 1),
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=9.3,
            fontweight="bold",
            color=PALETTE["text"],
        )


def generate_stage_evolution(with_png: bool) -> None:
    fig, ax = plt.subplots(figsize=(14.8, 6.6))
    ax.axis("off")
    ax.set_title("Fig. 4  Stage evolution from broad design to defended thesis framing", loc="left", pad=14)

    historical_colors = (
        [PALETTE["light_blue"]] * 7
        + [PALETTE["light_teal"]] * 3
        + [PALETTE["light_gold"]]
        + [PALETTE["light_gray"]] * 3
    )
    thesis_colors = [PALETTE["light_blue"]] * 7 + [PALETTE["light_teal"]] * 3
    runtime_colors = [PALETTE["light_blue"]] * 7 + [PALETTE["light_teal"]] * 3 + [PALETTE["light_gold"]]

    draw_stage_grid(
        ax,
        0.05,
        0.47,
        14,
        title="Historical engineering design",
        subtitle="14 stages in older notes, including advanced / research extensions",
        colors=historical_colors,
    )
    draw_stage_grid(
        ax,
        0.39,
        0.47,
        10,
        title="Thesis presentation target",
        subtitle="7 core stages + 3 conditional retraining stages",
        colors=thesis_colors,
    )
    draw_stage_grid(
        ax,
        0.71,
        0.47,
        11,
        title="Current CLI/runtime",
        subtitle="Stages 1-10 plus calibration still exposed",
        colors=runtime_colors,
    )

    add_arrow(ax, (0.33, 0.56), (0.38, 0.56), color=PALETTE["navy"], lw=1.7)
    add_arrow(ax, (0.66, 0.56), (0.70, 0.56), color=PALETTE["navy"], lw=1.7)

    add_box(
        ax,
        0.05,
        0.08,
        0.90,
        0.18,
        (
            "Interpretation:\n"
            "- Historical design was broader than the final defended thesis scope.\n"
            "- The thesis centers on stages 1-7 as the operational core and stages 8-10 as governed mutation.\n"
            "- Calibration remains visible in runtime but is not part of the core thesis claim."
        ),
        facecolor=PALETTE["light_gray"],
        edgecolor=PALETTE["slate"],
        ha="left",
    )

    save(fig, "fig_04_stage_evolution.svg", with_png=with_png)


def generate_core_vs_conditional(with_png: bool) -> None:
    """Two swim-lane bands: core assessment (S1-S7 gate) vs governed mutation (S8-S10)."""
    fig, ax = plt.subplots(figsize=(16.0, 7.6))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(
        "Fig. 5  Core operational path versus governed mutation path",
        loc="left", pad=12, fontsize=11,
    )

    C_B1_BG = "#DCEEFF"
    C_B1_EDG = "#1F4E79"
    C_B1_BOX = "#A8C8E8"
    C_B2_BG = "#FDEBD0"
    C_B2_EDG = "#8B3A0F"
    C_B2_BOX = "#F0B27A"
    C_GATE_F = "#FDECD2"
    C_GATE_E = "#E76F51"
    C_STOP_F = "#F0F4F8"
    C_STOP_E = "#52606d"
    C_OPT_F = "#FEFCE6"
    C_OPT_E = "#C5A46D"
    C_TXT = PALETTE["text"]

    # ── Band 1: Core Operational Path ────────────────────────────────────────
    B1_Y = 0.51
    B1_H = 0.44
    ax.add_patch(Rectangle((0.0, B1_Y), 1.0, B1_H, transform=ax.transAxes,
                            facecolor=C_B1_BG, edgecolor=C_B1_EDG, linewidth=1.6, zorder=0))
    ax.text(0.012, B1_Y + B1_H - 0.032,
            "CORE OPERATIONAL PATH  ·  Stages 1–7  ·  runs every session",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8.8, fontweight="bold", color=C_B1_EDG, zorder=1)

    # ── Band 2: Governed Mutation Path ───────────────────────────────────────
    B2_Y = 0.05
    B2_H = 0.42
    ax.add_patch(Rectangle((0.0, B2_Y), 1.0, B2_H, transform=ax.transAxes,
                            facecolor=C_B2_BG, edgecolor=C_B2_EDG, linewidth=1.6, zorder=0))
    ax.text(0.012, B2_Y + B2_H - 0.032,
            "GOVERNED MUTATION PATH  ·  Stages 8–10  ·  conditional on Stage 7 policy",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8.8, fontweight="bold", color=C_B2_EDG, zorder=1)

    # ── Stage 1–6 boxes ───────────────────────────────────────────────────────
    CORE_LBLS = ["S1\nIngestion", "S2\nValidation", "S3\nTransform",
                 "S4\nInference", "S5\nEvaluation", "S6\nMonitoring"]
    BW = 0.088
    BH = 0.155
    BY = B1_Y + (B1_H - BH) / 2 - 0.015
    YM = BY + BH / 2
    xs = [0.020 + i * (BW + 0.014) for i in range(6)]

    for i, (x0, lbl) in enumerate(zip(xs, CORE_LBLS)):
        ax.add_patch(FancyBboxPatch((x0, BY), BW, BH,
                                    boxstyle="round,pad=0.012,rounding_size=0.018",
                                    transform=ax.transAxes,
                                    facecolor=C_B1_BOX, edgecolor=C_B1_EDG,
                                    linewidth=1.3, zorder=2))
        ax.text(x0 + BW / 2, YM, lbl, transform=ax.transAxes,
                ha="center", va="center", fontsize=9.0, color=C_TXT, zorder=3)
        if i < 5:
            ax.add_patch(FancyArrowPatch(
                (x0 + BW + 0.002, YM), (xs[i + 1] - 0.002, YM),
                transform=ax.transAxes, arrowstyle="-|>", mutation_scale=10,
                linewidth=1.2, color=C_B1_EDG,
                connectionstyle="arc3,rad=0", zorder=4))

    # ── Stage 7 Decision Diamond (governance gate) ────────────────────────────
    S6_RIGHT = xs[5] + BW   # right edge of S6 box
    DX = 0.77
    DY = YM
    DHW = 0.058
    DHH = 0.088

    ax.add_patch(FancyArrowPatch(
        (S6_RIGHT + 0.003, YM), (DX - DHW - 0.003, YM),
        transform=ax.transAxes, arrowstyle="-|>", mutation_scale=10,
        linewidth=1.2, color=C_B1_EDG,
        connectionstyle="arc3,rad=0", zorder=4))

    D_PTS = np.array([[DX, DY + DHH], [DX + DHW, DY],
                      [DX, DY - DHH], [DX - DHW, DY]])
    ax.add_patch(Polygon(D_PTS, closed=True, transform=ax.transAxes,
                         facecolor=C_GATE_F, edgecolor=C_GATE_E,
                         linewidth=2.2, zorder=5))
    ax.text(DX, DY + 0.012, "S7", transform=ax.transAxes,
            ha="center", va="center", fontsize=9.5,
            fontweight="bold", color=C_GATE_E, zorder=6)
    ax.text(DX, DY - 0.030, "Trigger", transform=ax.transAxes,
            ha="center", va="center", fontsize=8.0, color=C_GATE_E, zorder=6)

    # ── Stop without mutation box (primary exit — most sessions) ─────────────
    SP_X = 0.845
    SP_Y = BY
    SP_W = 0.145
    SP_H = BH
    ax.add_patch(FancyBboxPatch((SP_X, SP_Y), SP_W, SP_H,
                                boxstyle="round,pad=0.012,rounding_size=0.018",
                                transform=ax.transAxes,
                                facecolor=C_STOP_F, edgecolor=C_STOP_E,
                                linewidth=1.3, zorder=2))
    ax.text(SP_X + SP_W / 2, SP_Y + SP_H / 2,
            "Stop without\nmutation\n\nnone / monitor\nreview",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=8.5, color=C_STOP_E, zorder=3)

    ax.add_patch(FancyArrowPatch(
        (DX + DHW + 0.003, DY), (SP_X - 0.003, SP_Y + SP_H / 2),
        transform=ax.transAxes, arrowstyle="-|>", mutation_scale=11,
        linewidth=1.5, color=C_STOP_E,
        connectionstyle="arc3,rad=0.12", zorder=4))
    ax.text((DX + DHW + SP_X) / 2 + 0.01, DY + 0.075,
            "none / monitor / review  →  stop",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=7.5, color=C_STOP_E, style="italic", zorder=4)

    # ── Arrow from S7 bottom into mutation band ───────────────────────────────
    MBW = 0.115
    MBH = 0.185
    MBY = B2_Y + (B2_H - MBH) / 2 - 0.01
    MYM = MBY + MBH / 2
    S8_X = 0.05
    S8_CX = S8_X + MBW / 2

    ax.add_patch(FancyArrowPatch(
        (DX, DY - DHH - 0.003), (S8_CX, MBY + MBH + 0.003),
        transform=ax.transAxes, arrowstyle="-|>", mutation_scale=13,
        linewidth=2.0, color=C_GATE_E,
        connectionstyle="arc3,rad=-0.28", zorder=4))
    ax.text(DX + 0.025, (DY - DHH + MBY + MBH) / 2,
            "queue_retrain\n/ trigger",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=7.5, color=C_GATE_E, style="italic", zorder=4)

    # ── Stage 8–10 boxes ──────────────────────────────────────────────────────
    MUT_LBLS = ["S8\nRetraining", "S9\nRegistration", "S10\nBaseline\nUpdate"]
    MUT_XS = [S8_X, S8_X + MBW + 0.025, S8_X + 2 * (MBW + 0.025)]

    for i, (x0, lbl) in enumerate(zip(MUT_XS, MUT_LBLS)):
        ax.add_patch(FancyBboxPatch((x0, MBY), MBW, MBH,
                                    boxstyle="round,pad=0.012,rounding_size=0.018",
                                    transform=ax.transAxes,
                                    facecolor=C_B2_BOX, edgecolor=C_B2_EDG,
                                    linewidth=1.3, zorder=2))
        ax.text(x0 + MBW / 2, MYM, lbl, transform=ax.transAxes,
                ha="center", va="center", fontsize=9.0, color=C_TXT, zorder=3)
        if i < 2:
            ax.add_patch(FancyArrowPatch(
                (x0 + MBW + 0.002, MYM), (MUT_XS[i + 1] - 0.002, MYM),
                transform=ax.transAxes, arrowstyle="-|>", mutation_scale=10,
                linewidth=1.2, color=C_B2_EDG,
                connectionstyle="arc3,rad=0", zorder=4))

    # ── S11 Optional Calibration (dashed) ─────────────────────────────────────
    S11_X = MUT_XS[2] + MBW + 0.030
    ax.add_patch(FancyBboxPatch((S11_X, MBY), 0.11, MBH,
                                boxstyle="round,pad=0.012,rounding_size=0.018",
                                transform=ax.transAxes,
                                facecolor=C_OPT_F, edgecolor=C_OPT_E,
                                linewidth=1.2, linestyle="--", zorder=2))
    ax.text(S11_X + 0.055, MYM, "S11\nCalibration\n(optional)",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=8.2, color=C_OPT_E, zorder=3)
    ax.add_patch(FancyArrowPatch(
        (MUT_XS[2] + MBW + 0.002, MYM), (S11_X - 0.002, MYM),
        transform=ax.transAxes, arrowstyle="-|>", mutation_scale=9,
        linewidth=1.0, color=C_OPT_E, linestyle="--",
        connectionstyle="arc3,rad=0", zorder=4))

    # ── Bottom callout ────────────────────────────────────────────────────────
    ax.text(0.50, 0.012,
            "Thesis governance argument: Stages 1–7 assess every session  ·  "
            "Stages 8–10 mutate model state only when Stage 7 policy authorises",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5,
            bbox={"boxstyle": "round,pad=0.30", "facecolor": "white",
                  "edgecolor": C_B1_EDG, "linewidth": 0.9},
            zorder=5)

    save(fig, "fig_05_core_vs_conditional_pipeline.svg", with_png=with_png)


def generate_data_pipeline(with_png: bool) -> None:
    fig, ax = plt.subplots(figsize=(15.0, 5.8))
    ax.axis("off")
    ax.set_title("Fig. 6  Train-serve consistent preprocessing pipeline", loc="left", pad=14)

    steps = [
        ("Raw wrist IMU", "Accelerometer + gyroscope"),
        ("Validation", "Schema and range checks"),
        ("Unit conversion", "milliG -> m/s^2"),
        ("Normalization", "Training-time scaler"),
        ("Resampling", "Align to 50 Hz"),
        ("Windowing", "200 samples\n50% overlap"),
        ("Saved tensor", "production_X.npy\nshape (N, 200, 6)"),
    ]
    x_positions = np.linspace(0.03, 0.79, len(steps))
    for idx, (title, body) in enumerate(steps):
        add_box(
            ax,
            x_positions[idx],
            0.48,
            0.12,
            0.18,
            body,
            facecolor=PALETTE["light_blue"] if idx < 2 else PALETTE["light_teal"] if idx < 6 else PALETTE["light_gold"],
            edgecolor=PALETTE["navy"] if idx < 2 else PALETTE["teal"] if idx < 6 else PALETTE["gold"],
            title=title,
            fontsize=9.2,
        )
        if idx < len(steps) - 1:
            add_arrow(ax, (x_positions[idx] + 0.12, 0.57), (x_positions[idx + 1], 0.57), color=PALETTE["slate"])

    add_box(
        ax,
        0.84,
        0.48,
        0.13,
        0.18,
        "Inference\nEvaluation\nMonitoring",
        facecolor=PALETTE["light_gray"],
        edgecolor=PALETTE["slate"],
        title="Downstream stages",
        fontsize=9.3,
    )
    add_arrow(ax, (0.91, 0.48), (0.91, 0.34), color=PALETTE["slate"], lw=1.2)

    add_callout(
        ax,
        0.50,
        0.18,
        "Preprocessing consistency is central because the production tensor must match the model's training-time representation.",
        color=PALETTE["rust"],
        ha="center",
    )

    save(fig, "fig_06_data_pipeline.svg", with_png=with_png)


def add_bar_labels(ax, values, y_positions, *, offset: float, decimals: int = 2, suffix: str = "") -> None:
    for value, y_pos in zip(values, y_positions):
        ax.text(value + offset, y_pos, f"{value:.{decimals}f}{suffix}", va="center", ha="left", fontsize=9.1)


def generate_ablation(with_png: bool) -> None:
    configs = ["A", "B", "C", "D"]
    unique_classes = [7.08, 7.88, 5.32, 9.72]
    hand_share = [78.37, 73.22, 96.72, 50.14]
    colors = [PALETTE["slate"], PALETTE["navy"], PALETTE["rust"], PALETTE["teal"]]
    y = np.arange(len(configs))

    fig, axes = plt.subplots(2, 1, figsize=(11.8, 8.4), sharey=True)
    fig.suptitle("Fig. 7  A/B/C/D preprocessing ablation comparison", x=0.125, y=0.98, ha="left", fontsize=15, fontweight="bold")

    axes[0].barh(y, unique_classes, color=colors, edgecolor="white", height=0.58)
    axes[0].set_xlim(0, 11)
    axes[0].set_yticks(y, configs)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Mean unique classes predicted")
    axes[0].set_title("Higher is better", loc="left", fontsize=11, color=PALETTE["green"])
    axes[0].grid(axis="x")
    add_bar_labels(axes[0], unique_classes, y, offset=0.16)

    axes[1].barh(y, hand_share, color=colors, edgecolor="white", height=0.58)
    axes[1].set_xlim(0, 105)
    axes[1].set_yticks(y, configs)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Mean hand_tapping share (%)")
    axes[1].set_title("Lower is better", loc="left", fontsize=11, color=PALETTE["rust"])
    axes[1].grid(axis="x")
    add_bar_labels(axes[1], hand_share, y, offset=1.4, suffix="%")

    add_callout(
        axes[1],
        0.66,
        0.22,
        "Config C: gravity only worsened collapse",
        color=PALETTE["rust"],
    )
    add_callout(
        axes[0],
        0.66,
        0.18,
        "Config D: gravity + calibration improved class diversity most",
        color=PALETTE["teal"],
    )

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "fig_07_ablation_config_comparison.svg", with_png=with_png)


def generate_trigger_policy(with_png: bool) -> None:
    policies = [
        "single_signal",
        "two_of_three",
        "two_of_three\ncooldown 6h",
        "two_of_three\ncooldown 12h",
        "two_of_three\ncooldown 24h",
    ]
    total_triggers = [251, 164, 42, 24, 14]
    precision = [0.8406, 0.9878, 0.9524, 0.9167, 1.0]
    tradeoff_f1 = [0.9134, 0.9939, 0.9756, 0.9565, 0.9333]
    false_alarm = [0.1389, 0.0069, 0.0069, 0.0069, 0.0]
    episode_recall = [1.0, 1.0, 1.0, 1.0, 0.875]
    y = np.arange(len(policies))

    fig, axes = plt.subplots(2, 1, figsize=(12.8, 8.8), sharey=True)
    fig.suptitle("Fig. 8  Trigger policy comparison", x=0.125, y=0.98, ha="left", fontsize=15, fontweight="bold")

    axes[0].barh(y - 0.16, precision, height=0.28, color=PALETTE["navy"], label="Precision")
    axes[0].barh(y + 0.16, tradeoff_f1, height=0.28, color=PALETTE["teal"], label="Tradeoff F1")
    axes[0].set_xlim(0.0, 1.08)
    axes[0].set_yticks(y, policies)
    axes[0].invert_yaxis()
    axes[0].grid(axis="x")
    axes[0].set_xlabel("Score (0–1)")
    axes[0].legend(frameon=False, loc="lower right")
    for vals, ypos in [(precision, y - 0.16), (tradeoff_f1, y + 0.16)]:
        for value, pos in zip(vals, ypos):
            axes[0].text(value + 0.004, pos, f"{value:.4f}", va="center", ha="left", fontsize=8.8)

    axes[1].barh(y - 0.16, false_alarm, height=0.28, color=PALETTE["rust"], label="False alarm rate")
    axes[1].barh(y + 0.16, episode_recall, height=0.28, color=PALETTE["gold"], label="Episode recall")
    axes[1].set_xlim(0, 1.05)
    axes[1].set_yticks(y, policies)
    axes[1].invert_yaxis()
    axes[1].grid(axis="x")
    axes[1].set_xlabel("Rate")
    axes[1].legend(frameon=False, loc="lower right")
    for vals, ypos, fmt in [(false_alarm, y - 0.16, "{:.4f}"), (episode_recall, y + 0.16, "{:.3f}")]:
        for value, pos in zip(vals, ypos):
            axes[1].text(value + 0.015, pos, fmt.format(value), va="center", ha="left", fontsize=8.8)

    for trigger_count, pos in zip(total_triggers, y):
        axes[0].text(0.01, pos, f"n={trigger_count}", va="center", ha="left", fontsize=8.7, color=PALETTE["muted"])

    add_callout(
        axes[0],
        0.60,
        0.20,
        "two_of_three gives the best balance of high precision, low false alarms, and retained recall.",
        color=PALETTE["navy"],
    )

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "fig_08_trigger_policy_comparison.svg", with_png=with_png)


def generate_monitoring_governance(with_png: bool) -> None:
    """Ch6 post-inference monitoring and governance flow: S5 → S6 signals → S7 → action."""
    fig, ax = plt.subplots(figsize=(15.5, 7.2))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(
        "Post-Inference Monitoring and Governance Flow  (Stages 5–7)",
        loc="left", pad=12, fontsize=11,
    )

    C_INFER_BG = "#DCEEFF"
    C_INFER_E = "#1F4E79"
    C_MON_BG = "#D4EDE8"
    C_MON_E = "#2A7D6E"
    C_MON_BOX = "#A8D8CE"
    C_GOV_BG = "#FDEBD0"
    C_GOV_E = "#8B3A0F"
    C_GOV_BOX = "#F0B27A"
    C_GATE_F = "#FDECD2"
    C_GATE_E = "#E76F51"
    C_TXT = PALETTE["text"]

    # ── Section 1: Inference (S4 + S5) ───────────────────────────────────────
    ax.add_patch(Rectangle((0.00, 0.08), 0.19, 0.84, transform=ax.transAxes,
                            facecolor=C_INFER_BG, edgecolor=C_INFER_E,
                            linewidth=1.5, zorder=0))
    ax.text(0.095, 0.90, "INFERENCE",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=8.8, fontweight="bold", color=C_INFER_E, zorder=1)

    for y0, label, detail in [
        (0.57, "Stage 4\nInference",
         "Per-window softmax\nArgmax class label\nProbability tensor"),
        (0.16, "Stage 5\nEvaluation",
         "Mean confidence\nClass distribution\nDominance check\nEntropy proxy"),
    ]:
        ax.add_patch(FancyBboxPatch((0.01, y0), 0.17, 0.25,
                                    boxstyle="round,pad=0.012,rounding_size=0.015",
                                    transform=ax.transAxes,
                                    facecolor="#B8D4EE", edgecolor=C_INFER_E,
                                    linewidth=1.2, zorder=2))
        ax.text(0.095, y0 + 0.17, label,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=9.0, fontweight="bold", color=C_INFER_E, zorder=3)
        ax.text(0.095, y0 + 0.07, detail,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=7.8, color=C_TXT, zorder=3)

    ax.add_patch(FancyArrowPatch((0.095, 0.57), (0.095, 0.41),
                                  transform=ax.transAxes, arrowstyle="-|>",
                                  mutation_scale=10, linewidth=1.2,
                                  color=C_INFER_E, zorder=4))
    ax.add_patch(FancyArrowPatch((0.19, 0.305), (0.22, 0.305),
                                  transform=ax.transAxes, arrowstyle="-|>",
                                  mutation_scale=11, linewidth=1.3,
                                  color=C_INFER_E, zorder=4))

    # ── Section 2: S6 Three-Signal Monitoring ────────────────────────────────
    ax.add_patch(Rectangle((0.22, 0.08), 0.44, 0.84, transform=ax.transAxes,
                            facecolor=C_MON_BG, edgecolor=C_MON_E,
                            linewidth=1.5, zorder=0))
    ax.text(0.44, 0.90, "Stage 6  POST-INFERENCE MONITORING",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=8.8, fontweight="bold", color=C_MON_E, zorder=1)

    signal_defs = [
        ("Confidence &\nUncertainty",
         "Mean conf < 0.70\nUncertain% > 20%\nTop-two margin\nEntropy proxy",
         0.23),
        ("Temporal\nTransitions",
         "Transition rate > 35%\nDominant share > 85%\nClass switching\npattern",
         0.37),
        ("Drift\n(Baseline Δ)",
         "Drift z-score > 1.8\nRuntime vs training\nbaseline comparison\nMMD audit (branch)",
         0.51),
    ]
    for (sig_title, sig_detail, x0) in signal_defs:
        ax.add_patch(FancyBboxPatch((x0, 0.18), 0.12, 0.60,
                                    boxstyle="round,pad=0.012,rounding_size=0.015",
                                    transform=ax.transAxes,
                                    facecolor=C_MON_BOX, edgecolor=C_MON_E,
                                    linewidth=1.2, zorder=2))
        ax.text(x0 + 0.06, 0.73, sig_title,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=C_MON_E, zorder=3)
        ax.text(x0 + 0.06, 0.48, sig_detail,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=7.7, color=C_TXT, zorder=3)
        ax.add_patch(FancyBboxPatch((x0 + 0.01, 0.20), 0.10, 0.12,
                                    boxstyle="round,pad=0.006",
                                    transform=ax.transAxes,
                                    facecolor="#FEF0EA", edgecolor=C_GATE_E,
                                    linewidth=0.9, zorder=3))
        ax.text(x0 + 0.06, 0.26, "HEALTHY\nWARNING / CRITICAL",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=7.0, color=C_GATE_E, zorder=4)

    ax.add_patch(FancyArrowPatch((0.66, 0.48), (0.69, 0.48),
                                  transform=ax.transAxes, arrowstyle="-|>",
                                  mutation_scale=11, linewidth=1.4,
                                  color=C_GOV_E, zorder=4))

    # ── Section 3: S7 Governance ──────────────────────────────────────────────
    ax.add_patch(Rectangle((0.69, 0.08), 0.31, 0.84, transform=ax.transAxes,
                            facecolor=C_GOV_BG, edgecolor=C_GOV_E,
                            linewidth=1.5, zorder=0))
    ax.text(0.845, 0.90, "Stage 7  TRIGGER EVALUATION",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=8.8, fontweight="bold", color=C_GOV_E, zorder=1)

    gov_steps = [
        ("Two-of-three voting\npolicy", 0.70),
        ("Collapse guard\n(degenerate output check)", 0.55),
        ("Cooldown gate\n(prevent rapid retraining)", 0.40),
    ]
    for step_text, y_ctr in gov_steps:
        ax.add_patch(FancyBboxPatch((0.71, y_ctr - 0.07), 0.26, 0.12,
                                    boxstyle="round,pad=0.010,rounding_size=0.015",
                                    transform=ax.transAxes,
                                    facecolor=C_GOV_BOX, edgecolor=C_GOV_E,
                                    linewidth=1.2, zorder=2))
        ax.text(0.845, y_ctr, step_text,
                transform=ax.transAxes, ha="center", va="center",
                fontsize=8.2, color=C_TXT, zorder=3)

    for y_top, y_bot in [(0.70, 0.55), (0.55, 0.40)]:
        ax.add_patch(FancyArrowPatch((0.845, y_top - 0.07), (0.845, y_bot + 0.05),
                                      transform=ax.transAxes, arrowstyle="-|>",
                                      mutation_scale=9, linewidth=1.1,
                                      color=C_GOV_E, zorder=4))

    ax.add_patch(FancyArrowPatch((0.845, 0.33), (0.845, 0.26),
                                  transform=ax.transAxes, arrowstyle="-|>",
                                  mutation_scale=10, linewidth=1.3,
                                  color=C_GATE_E, zorder=4))

    # Action output box
    ax.add_patch(FancyBboxPatch((0.71, 0.10), 0.26, 0.16,
                                boxstyle="round,pad=0.010,rounding_size=0.015",
                                transform=ax.transAxes,
                                facecolor=C_GATE_F, edgecolor=C_GATE_E,
                                linewidth=1.8, zorder=2))
    ax.text(0.845, 0.20, "action =\nnone / monitor / review\nqueue_retrain / trigger",
            transform=ax.transAxes, ha="center", va="center",
            fontsize=8.2, fontweight="bold", color=C_GATE_E, zorder=3)

    # Key callout
    ax.text(0.50, 0.012,
            "Both defended evidence runs: alert_level = CRITICAL  ·  "
            "should_retrain = false  ·  action = review  "
            "(CRITICAL severity ≠ automatic retraining)",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8.2,
            bbox={"boxstyle": "round,pad=0.28", "facecolor": "white",
                  "edgecolor": C_INFER_E, "linewidth": 0.9},
            zorder=5)

    save(fig, "fig_ch6_monitoring_governance.svg", with_png=with_png)


def generate_abc_comparison(with_png: bool) -> None:
    """Ch7 ABC model comparison: accuracy and mean confidence across two evaluation datasets."""
    models = ["Model A\n(runtime candidate)", "Model B\n(diagnostic reference)", "Model C\n(contract mismatch)"]
    x = np.arange(len(models))
    width = 0.34

    # User 7 external / all_users diagnostic — accuracy and mean confidence
    acc_u7   = [37.6, 43.8,  7.6]
    acc_all  = [42.4, 90.8, 10.6]
    conf_u7  = [0.359, 0.775, 0.748]
    conf_all = [0.378, 0.930, 0.767]
    classes_u7  = [11, 11, 4]
    classes_all = [11, 11, 7]

    C_U7  = PALETTE["navy"]
    C_ALL = PALETTE["teal"]

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.4))
    fig.suptitle(
        "Fig.  ABC Model Comparison  —  accuracy and confidence on two evaluation datasets",
        x=0.06, y=0.98, ha="left", fontsize=12, fontweight="bold",
    )

    # ── Panel 1: Accuracy ─────────────────────────────────────────────────────
    ax = axes[0]
    bars_u7  = ax.bar(x - width / 2, acc_u7,  width, color=C_U7,  label="User 7 external")
    bars_all = ax.bar(x + width / 2, acc_all, width, color=C_ALL, label="all_users diagnostic")
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=9.2)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy", loc="left", fontsize=11)
    ax.grid(axis="y")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=9)

    for bar, val, cls in zip(bars_u7, acc_u7, classes_u7):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.5,
                f"{val:.1f}%\n({cls} cls)", ha="center", va="bottom", fontsize=8.5)
    for bar, val, cls in zip(bars_all, acc_all, classes_all):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.5,
                f"{val:.1f}%\n({cls} cls)", ha="center", va="bottom", fontsize=8.5)

    add_callout(ax, 0.52, 0.85,
                "Model B gap:\n90.8% → 43.8%\n(−47 pp internal→external)",
                color=PALETTE["rust"])
    add_callout(ax, 0.01, 0.28,
                "Model C collapse:\n7.6% (4 classes only)",
                color=PALETTE["rust"])

    # ── Panel 2: Mean confidence ──────────────────────────────────────────────
    ax2 = axes[1]
    bars_u7c  = ax2.bar(x - width / 2, conf_u7,  width, color=C_U7,  label="User 7 external")
    bars_allc = ax2.bar(x + width / 2, conf_all, width, color=C_ALL, label="all_users diagnostic")
    ax2.set_xticks(x)
    ax2.set_xticklabels(models, fontsize=9.2)
    ax2.set_ylim(0, 1.08)
    ax2.set_ylabel("Mean confidence (softmax)")
    ax2.set_title("Mean Confidence", loc="left", fontsize=11)
    ax2.grid(axis="y")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.legend(frameon=False, fontsize=9)

    for bar, val in zip(bars_u7c, conf_u7):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.012,
                 f"{val:.3f}", ha="center", va="bottom", fontsize=8.5)
    for bar, val in zip(bars_allc, conf_all):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.012,
                 f"{val:.3f}", ha="center", va="bottom", fontsize=8.5)

    add_callout(ax2, 0.01, 0.42,
                "Model A: low confidence\n(honest calibration limit;\n"
                "calibration not solved)",
                color=PALETTE["navy"])

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, "fig_ch7_abc_comparison.svg", with_png=with_png)


def generate_actual_vs_synthetic(with_png: bool) -> None:
    datasets = ["Actual labeled", "Synth Codex", "Synth Other"]
    accuracy = [98.9, 70.4, 34.6]
    macro_f1 = [98.9, 71.1, 31.7]
    confidence = [98.6, 86.8, 77.7]
    uncertain = [0.2, 6.5, 14.5]
    drift = [0.0000, 0.0010, 0.0090]
    colors = [PALETTE["navy"], PALETTE["teal"], PALETTE["rust"]]

    fig, axes = plt.subplots(2, 1, figsize=(12.2, 8.6), gridspec_kw={"height_ratios": [3.0, 1.25]})
    fig.suptitle("Fig. 9  Actual versus synthetic dataset comparison", x=0.125, y=0.98, ha="left", fontsize=15, fontweight="bold")

    metric_names = ["Accuracy", "Macro F1", "Mean confidence", "Uncertain rate"]
    metric_values = np.array([accuracy, macro_f1, confidence, uncertain])
    x = np.arange(len(metric_names))
    width = 0.24
    for idx, (dataset, color) in enumerate(zip(datasets, colors)):
        values = metric_values[:, idx]
        bars = axes[0].bar(x + (idx - 1) * width, values, width=width, color=color, label=dataset)
        for bar, value in zip(bars, values):
            axes[0].text(bar.get_x() + bar.get_width() / 2, value + 1.2, f"{value:.1f}", ha="center", va="bottom", fontsize=8.8)

    axes[0].set_xticks(x, metric_names)
    axes[0].set_ylim(0, 110)
    axes[0].set_ylabel("Percent")
    axes[0].grid(axis="y")
    axes[0].legend(frameon=False, ncol=3, loc="upper right")

    drift_x = np.arange(len(datasets))
    bars = axes[1].bar(drift_x, drift, color=colors, width=0.55)
    for bar, value in zip(bars, drift):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 0.00025, f"{value:.4f}", ha="center", va="bottom", fontsize=8.8)
    axes[1].set_xticks(drift_x, datasets)
    axes[1].set_ylabel("Drift")
    axes[1].set_ylim(0, 0.0105)
    axes[1].grid(axis="y")

    add_callout(
        axes[0],
        0.03,
        0.15,
        "As realism drops, uncertainty rises and performance degrades.",
        color=PALETTE["rust"],
    )

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "fig_09_actual_vs_synthetic.svg", with_png=with_png)


def generate_old_vs_new(with_png: bool) -> None:
    # Third bar = old model re-run on the SAME input as the new model.
    # Near-identical to "Old model" column, confirming collapse is a model property.
    labels = ["Old model", "New model", "Old model\n(control rerun)"]
    colors = [PALETTE["rust"], PALETTE["teal"], PALETTE["gold"]]

    metrics = {
        "Mean confidence": [0.876, 0.7897, 0.8762],
        "Uncertain rate (%)": [4.4, 15.0, 4.40],
        "Top-class share (%)": [85.6, 29.0, 85.64],
        "Classes fired": [9, 11, 9],
    }
    limits = {
        "Mean confidence": 1.0,
        "Uncertain rate (%)": 20,
        "Top-class share (%)": 100,
        "Classes fired": 12,
    }

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 8.8))
    fig.suptitle(
        "Fig. 10  Same-input old versus new model comparison\n"
        "(control rerun confirms collapse is a model property, not an input property)",
        x=0.06, y=0.98, ha="left", fontsize=13, fontweight="bold",
    )

    for ax, (metric, values) in zip(axes.flat, metrics.items()):
        bars = ax.bar(labels, values, color=colors, width=0.52)
        for bar, value in zip(bars, values):
            if metric == "Mean confidence":
                text = f"{value:.4f}"
            elif metric == "Classes fired":
                text = f"{int(value)}"
            else:
                text = f"{value:.1f}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 0.02 * limits[metric],
                text,
                ha="center", va="bottom", fontsize=9.0,
            )
        ax.set_ylim(0, limits[metric])
        ax.set_title(metric, loc="left", fontsize=11)
        ax.grid(axis="y")
        ax.spines[["top", "right"]].set_visible(False)

    add_callout(
        axes[0, 1],
        0.05,
        0.80,
        "Old top class: hand_tapping  ·  New top class: hand_scratching\n"
        "Control rerun top class: hand_tapping  (same collapse pattern as Old)",
        color=PALETTE["navy"],
    )
    add_callout(
        axes[1, 0],
        0.05,
        0.12,
        "Old model and control rerun are near-identical on the same input;\n"
        "New model spans all 11 classes.  Model choice — not input — drives the difference.",
        color=PALETTE["rust"],
    )

    fig.tight_layout(rect=(0, 0, 1, 0.93))
    save(fig, "fig_10_old_vs_new_model_comparison.svg", with_png=with_png)


def draw_issue_column(ax, x: float, theme: str, theme_color: str, items: list[tuple[str, str]]) -> None:
    add_box(
        ax,
        x,
        0.80,
        0.17,
        0.11,
        "",
        facecolor=theme_color,
        edgecolor=PALETTE["slate"],
        title=theme,
        ha="left",
    )
    item_y = 0.63
    for issue, resolution in items:
        text = f"Issue: {issue}\nResolution: {resolution}"
        add_box(
            ax,
            x,
            item_y,
            0.17,
            0.13,
            wrap_text(text, 24),
            facecolor="white",
            edgecolor=PALETTE["grid"],
            fontsize=8.5,
            ha="left",
        )
        item_y -= 0.15


def generate_challenges(with_png: bool) -> None:
    fig, ax = plt.subplots(figsize=(15.4, 9.2))
    ax.axis("off")
    ax.set_title("Fig. 11  Challenges and resolutions matrix", loc="left", pad=14)

    columns = [
        (
            "Train-serve mismatch",
            PALETTE["light_blue"],
            [
                ("Unit mismatch between training and production data", "Explicit unit conversion and preprocessing documentation"),
                ("Gravity removal absent during original training", "Formalized A/B/C/D matrix; baseline gravity removal kept disabled"),
                ("Synthetic-vs-real schema mismatch", "Projected and mapped comparison file used"),
            ],
        ),
        (
            "Orchestration bugs",
            PALETTE["light_teal"],
            [
                ("Threshold inconsistency across stages", "Threshold audits and consistency tests"),
                ("Stage 1 labels not reaching Stage 5 evaluation", "Fixed in April review pass"),
                ("`reused_existing` field missing", "Field restored in artifact summaries"),
            ],
        ),
        (
            "Model collapse and adaptation",
            PALETTE["light_gold"],
            [
                ("Hand-tapping dominance on production sessions", "Same-input old-vs-new comparison isolated the model effect"),
                ("AdaBN instability on free-living data", "Kept as optional negative-result evidence"),
                ("Rollback/deployment path mismatch", "Flagged in audit and partially cleaned later"),
            ],
        ),
        (
            "Environment drift",
            PALETTE["light_rust"],
            [
                ("Current workspace no longer reproduces the documented green suite", "Exact thesis environment still needs pinning and restabilization"),
            ],
        ),
        (
            "Scope control",
            PALETTE["light_gray"],
            [
                ("Stages 12-14 risked narrative bloat", "Removed from core thesis scope and reframed as historical or optional"),
                ("Smaller consistency issues accumulated", "Constants consolidated; argument order cleaned up"),
            ],
        ),
    ]

    x_positions = [0.03, 0.23, 0.43, 0.63, 0.83]
    for x_pos, column in zip(x_positions, columns):
        draw_issue_column(ax, x_pos, column[0], column[1], column[2])

    add_callout(
        ax,
        0.50,
        0.06,
        "Theme grouping is editorial. The challenge and resolution statements themselves come directly from the memo.",
        color=PALETTE["gold"],
        ha="center",
    )

    save(fig, "fig_11_challenges_resolutions_matrix.svg", with_png=with_png)


def generate_readiness(with_png: bool) -> None:
    labels = [
        "Code / pipeline",
        "Experiments / evidence",
        "Data collection / protocol",
        "Writing",
        "Defense preparation",
    ]
    values = [88, 76, 58, 42, 18]
    colors = [PALETTE["navy"], PALETTE["teal"], PALETTE["gold"], PALETTE["slate"], PALETTE["gray"]]
    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(11.6, 6.8))
    ax.barh(y, values, color=colors, height=0.56)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percent complete")
    ax.grid(axis="x")
    ax.set_title("Fig. 12  Internal readiness snapshot", loc="left", pad=14)
    ax.axvline(70, color=PALETTE["rust"], linewidth=1.4, linestyle="--")
    ax.text(70.5, 4.35, "Overall internal estimate: 70%", color=PALETTE["rust"], fontsize=9.2)
    for value, pos in zip(values, y):
        ax.text(value + 1.2, pos, f"{value}%", va="center", ha="left", fontsize=9.2)

    add_callout(
        ax,
        0.98,
        0.08,
        "Internal planning view,\nnot thesis evidence.",
        color=PALETTE["rust"],
        ha="right",
    )
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "fig_12_thesis_readiness_dashboard.svg", with_png=with_png)


def generate_risk_matrix(with_png: bool) -> None:
    fig, ax = plt.subplots(figsize=(11.8, 7.8))
    ax.axis("off")
    ax.set_title("Fig. 13  Internal risk exposure map", loc="left", pad=14)

    cols = ["High current level", "Medium current level"]
    rows = ["Writing / evidence", "Method / reproducibility", "Scope / claims"]

    x_edges = [0.16, 0.52]
    y_edges = [0.62, 0.38, 0.14]
    cell_w = 0.28
    cell_h = 0.18

    for col_idx, col_label in enumerate(cols):
        add_box(
            ax,
            x_edges[col_idx],
            0.84,
            cell_w,
            0.08,
            "",
            facecolor=PALETTE["light_blue"] if col_idx == 0 else PALETTE["light_gold"],
            edgecolor=PALETTE["slate"],
            title=col_label,
        )
    for row_idx, row_label in enumerate(rows):
        ax.text(0.03, y_edges[row_idx] + cell_h / 2, row_label, transform=ax.transAxes, ha="left", va="center", fontsize=10.0, fontweight="bold")

    cells = {
        (0, 0): "writing lags code",
        (0, 1): "Garmin protocol\nunder-documentation",
        (1, 0): "environment drift\nsubject-wise evaluation criticism",
        (1, 1): "",
        (2, 0): "",
        (2, 1): "AdaBN limitation pushback\noverclaiming scope",
    }

    for row_idx in range(len(rows)):
        for col_idx in range(len(cols)):
            face = PALETTE["light_rust"] if col_idx == 0 else PALETTE["light_gray"]
            add_box(
                ax,
                x_edges[col_idx],
                y_edges[row_idx],
                cell_w,
                cell_h,
                cells[(row_idx, col_idx)] or " ",
                facecolor=face,
                edgecolor=PALETTE["grid"],
                fontsize=9.3,
            )

    add_callout(
        ax,
        0.50,
        0.04,
        "The memo provides current risk level but not separate impact / probability scores; this figure therefore groups risks by stated level and affected area.",
        color=PALETTE["gold"],
        ha="center",
    )

    save(fig, "fig_13_risk_matrix.svg", with_png=with_png)


def generate_evidence_map(with_png: bool) -> None:
    fig, ax = plt.subplots(figsize=(13.4, 8.0))
    ax.axis("off")
    ax.set_title("Fig. 14  Evidence-to-chapter writing map", loc="left", pad=14)

    evidence_boxes = [
        ("Architecture and stage framing", 0.08, 0.78, PALETTE["light_blue"]),
        ("Data pipeline and model foundations", 0.08, 0.61, PALETTE["light_teal"]),
        ("Pipeline implementation and runtime behavior", 0.08, 0.44, PALETTE["light_gold"]),
        ("Monitoring, drift, and trigger policy", 0.08, 0.27, PALETTE["light_rust"]),
        ("Ablation, synthetic comparison, old-vs-new evidence", 0.08, 0.10, PALETTE["light_gray"]),
    ]
    chapter_boxes = [
        ("Chapter 3\nArchitecture", 0.68, 0.78),
        ("Chapter 4\nData and model", 0.68, 0.61),
        ("Chapter 5\nImplementation", 0.68, 0.44),
        ("Chapter 6\nMonitoring and trigger policy", 0.68, 0.27),
        ("Chapter 7\nExperiments and evaluation", 0.68, 0.10),
    ]

    for label, x_pos, y_pos, color in evidence_boxes:
        add_box(
            ax,
            x_pos,
            y_pos,
            0.23,
            0.10,
            wrap_text(label, 24),
            facecolor=color,
            edgecolor=PALETTE["slate"],
            fontsize=9.4,
        )

    for label, x_pos, y_pos in chapter_boxes:
        add_box(
            ax,
            x_pos,
            y_pos,
            0.20,
            0.10,
            label,
            facecolor="white",
            edgecolor=PALETTE["navy"],
            fontsize=9.5,
        )

    for idx in range(len(evidence_boxes)):
        add_arrow(
            ax,
            (0.31, evidence_boxes[idx][2] + 0.05),
            (0.68, chapter_boxes[idx][2] + 0.05),
            color=PALETTE["navy"],
        )

    add_box(
        ax,
        0.40,
        0.38,
        0.17,
        0.16,
        "Discussion,\nlimitations,\nand future work\n\n-> Chapter 8",
        facecolor=PALETTE["light_gray"],
        edgecolor=PALETTE["slate"],
        fontsize=9.7,
    )
    add_arrow(ax, (0.57, 0.46), (0.68, 0.18), color=PALETTE["slate"], lw=1.2)

    add_callout(
        ax,
        0.50,
        0.03,
        "Writing aid: use the strongest artifact families first, then translate them into chapter prose and figures.",
        color=PALETTE["navy"],
        ha="center",
    )

    save(fig, "fig_14_evidence_to_chapter_map.svg", with_png=with_png)


def write_index_files() -> None:
    index_lines = [
        "# Figure Index",
        "",
        "This index lists the thesis journey figure pack, suggested insertion points, and paste-ready captions.",
        "",
        "| Filename | Title | Suggested insertion point | Internal only |",
        "| --- | --- | --- | --- |",
    ]
    for spec in FIGURE_SPECS:
        internal = "Yes" if spec["internal_only"] else "No"
        index_lines.append(f"| `{spec['filename']}` | {spec['title']} | {spec['insertion']} | {internal} |")

    index_lines.extend(
        [
            "",
            "## Detailed entries",
            "",
        ]
    )
    for idx, spec in enumerate(FIGURE_SPECS, start=1):
        index_lines.extend(
            [
                f"### Fig. {idx} - {spec['title']}",
                f"- Filename: `{spec['filename']}`",
                f"- Suggested insertion point: {spec['insertion']}",
                f"- Why it helps: {spec['why']}",
                f"- Caption: {spec['caption']}",
                f"- Internal only: {'Yes' if spec['internal_only'] else 'No'}",
            ]
        )
        if spec["notes"]:
            index_lines.append(f"- Note: {spec['notes']}")
        index_lines.append("")

    index_lines.extend(
        [
            "## Recommendation summary",
            "",
            "### Six essential figures for the thesis-support memo",
        ]
    )
    for filename in ESSENTIAL_SUPPORT:
        spec = next(item for item in FIGURE_SPECS if item["filename"] == filename)
        index_lines.append(f"- `{filename}` - {spec['title']}")

    index_lines.extend(
        [
            "",
            "### Four figures best suited to the thesis body",
        ]
    )
    for filename in BEST_FOR_THESIS_BODY:
        spec = next(item for item in FIGURE_SPECS if item["filename"] == filename)
        index_lines.append(f"- `{filename}` - {spec['title']}")

    index_lines.extend(
        [
            "",
            "### Internal-only figures",
        ]
    )
    for filename in INTERNAL_ONLY:
        spec = next(item for item in FIGURE_SPECS if item["filename"] == filename)
        index_lines.append(f"- `{filename}` - {spec['title']}")

    index_lines.extend(
        [
            "",
            "### Figures with partially inferred structure or incomplete source fields",
        ]
    )
    for filename, note in PARTIAL_SOURCE_NOTES.items():
        index_lines.append(f"- `{filename}` - {note}")

    (OUTDIR / "FIGURE_INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")

    guide_lines = [
        "# Captions And Insertion Guide",
        "",
        "This file gives paste-ready captions and insertion guidance for the thesis journey figure pack.",
        "",
    ]
    for idx, spec in enumerate(FIGURE_SPECS, start=1):
        guide_lines.extend(
            [
                f"## Fig. {idx} - {spec['title']}",
                f"Filename: `{spec['filename']}`",
                f"Suggested insertion point: {spec['insertion']}",
                f"Why it helps: {spec['why']}",
                "",
                "Caption:",
                "",
                spec["caption"],
                "",
            ]
        )
        if spec["notes"]:
            guide_lines.extend(
                [
                    f"Note: {spec['notes']}",
                    "",
                ]
            )

    guide_lines.extend(
        [
            "## Recommendation summary",
            "",
            "### Six essential figures for the thesis-support memo",
        ]
    )
    for filename in ESSENTIAL_SUPPORT:
        spec = next(item for item in FIGURE_SPECS if item["filename"] == filename)
        guide_lines.append(f"- {spec['title']} (`{filename}`)")

    guide_lines.extend(
        [
            "",
            "### Four figures best suited to the thesis body",
        ]
    )
    for filename in BEST_FOR_THESIS_BODY:
        spec = next(item for item in FIGURE_SPECS if item["filename"] == filename)
        guide_lines.append(f"- {spec['title']} (`{filename}`)")

    guide_lines.extend(
        [
            "",
            "### Internal-only figures",
        ]
    )
    for filename in INTERNAL_ONLY:
        spec = next(item for item in FIGURE_SPECS if item["filename"] == filename)
        guide_lines.append(f"- {spec['title']} (`{filename}`)")

    guide_lines.extend(
        [
            "",
            "### Partial-source notes",
        ]
    )
    for filename, note in PARTIAL_SOURCE_NOTES.items():
        guide_lines.append(f"- `{filename}` - {note}")

    (OUTDIR / "CAPTIONS_AND_INSERTION_GUIDE.md").write_text("\n".join(guide_lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate thesis journey figure pack.")
    parser.add_argument("--with-png", action="store_true", help="Also export PNG copies next to the SVG files.")
    args = parser.parse_args()

    apply_style()
    generate_timeline(args.with_png)
    generate_document_layers(args.with_png)
    generate_scope_map(args.with_png)
    generate_stage_evolution(args.with_png)
    generate_core_vs_conditional(args.with_png)
    generate_data_pipeline(args.with_png)
    generate_ablation(args.with_png)
    generate_trigger_policy(args.with_png)
    generate_monitoring_governance(args.with_png)
    generate_abc_comparison(args.with_png)
    generate_actual_vs_synthetic(args.with_png)
    generate_old_vs_new(args.with_png)
    generate_challenges(args.with_png)
    generate_readiness(args.with_png)
    generate_risk_matrix(args.with_png)
    generate_evidence_map(args.with_png)
    write_index_files()


if __name__ == "__main__":
    main()
