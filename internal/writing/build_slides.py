"""
Build defense_slides.pptx from the 18-slide outline.
Run from repo root:  python internal/writing/build_slides.py
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

# Colour palette
DARK_BLUE   = RGBColor(0x1A, 0x37, 0x5E)   # slide backgrounds / title bar
MID_BLUE    = RGBColor(0x21, 0x5A, 0x9C)   # accent headings
LIGHT_BLUE  = RGBColor(0xD6, 0xE4, 0xF7)   # highlight boxes
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GREY  = RGBColor(0xF4, 0xF6, 0xFA)
DARK_GREY   = RGBColor(0x33, 0x33, 0x33)
GREEN_ACC   = RGBColor(0x1A, 0x7A, 0x4A)
RED_ACC     = RGBColor(0xA0, 0x20, 0x20)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

FIG_BASE = r"d:\study apply\ML Ops\MasterArbeit_MLops\thesis\figures\thesis_journey"

FIGURES = {
    "scope_map":       os.path.join(FIG_BASE, "fig_03_scope_map.png"),
    "pipeline":        os.path.join(FIG_BASE, "fig_05_core_vs_conditional_pipeline.png"),
    "abc":             os.path.join(FIG_BASE, "fig_ch7_abc_comparison.png"),
    "monitoring":      os.path.join(FIG_BASE, "fig_ch6_monitoring_governance.png"),
    "trigger":         os.path.join(FIG_BASE, "fig_08_trigger_policy_comparison.png"),
    "ablation":        os.path.join(FIG_BASE, "fig_07_ablation_config_comparison.png"),
    "old_vs_new":      os.path.join(FIG_BASE, "fig_10_old_vs_new_model_comparison.png"),
}


def new_prs():
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def blank_layout(prs):
    return prs.slide_layouts[6]  # completely blank


def add_bg(slide, color=DARK_BLUE):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, fill_color, line_color=None):
    shape = slide.shapes.add_shape(1, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape


def txb(slide, text, left, top, width, height,
        font_size=20, bold=False, color=WHITE, align=PP_ALIGN.LEFT,
        wrap=True, font_name="Calibri"):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font_name
    return tb


def add_title_bar(slide, title_text, subtitle_text=None):
    """Dark blue bar at top with title."""
    bar = add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.4), DARK_BLUE)
    txb(slide, title_text,
        Inches(0.4), Inches(0.15), Inches(12.5), Inches(0.8),
        font_size=28, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    if subtitle_text:
        txb(slide, subtitle_text,
            Inches(0.4), Inches(0.9), Inches(12.5), Inches(0.4),
            font_size=14, bold=False, color=LIGHT_BLUE, align=PP_ALIGN.LEFT)


def add_figure(slide, fig_key, left, top, width, height):
    path = FIGURES.get(fig_key)
    if path and os.path.exists(path):
        slide.shapes.add_picture(path, left, top, width, height)
    else:
        ph = add_rect(slide, left, top, width, height, LIGHT_BLUE, MID_BLUE)
        txb(slide, f"[Figure: {fig_key}]",
            left + Inches(0.1), top + height // 2 - Pt(12),
            width, Inches(0.4),
            font_size=12, color=MID_BLUE, align=PP_ALIGN.CENTER)


def set_notes(slide, text):
    notes = slide.notes_slide
    tf = notes.notes_text_frame
    tf.text = text


def content_area():
    """Returns (left, top, width, height) for the main content area below title bar."""
    return Inches(0.4), Inches(1.55), Inches(12.53), Inches(5.65)


# ==============================================================================
# SLIDES
# ==============================================================================

def slide_01_title(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, DARK_BLUE)
    # centre title block
    txb(slide,
        "Offline-First, Scalable, and Monitored MLOps Pipeline\nfor Wearable Human Activity Recognition",
        Inches(1.0), Inches(1.5), Inches(11.3), Inches(1.8),
        font_size=32, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txb(slide,
        "Master's Thesis Defense",
        Inches(1.0), Inches(3.5), Inches(11.3), Inches(0.5),
        font_size=20, bold=False, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    txb(slide,
        "Shalin Vachheta  -  Matriculation 1701359",
        Inches(1.0), Inches(4.1), Inches(11.3), Inches(0.4),
        font_size=16, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    txb(slide,
        "University of Siegen  -  Faculty of Engineering  -  Chair of Embedded Systems",
        Inches(1.0), Inches(4.6), Inches(11.3), Inches(0.4),
        font_size=14, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    txb(slide,
        "First Supervisor: Prof. Dr.-Ing. Roman Obermaisser  -  Second Examiner: M.Sc. Ugonna Oleh",
        Inches(1.0), Inches(5.1), Inches(11.3), Inches(0.4),
        font_size=12, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    txb(slide,
        "15 June 2026",
        Inches(1.0), Inches(5.7), Inches(11.3), Inches(0.4),
        font_size=14, color=WHITE, align=PP_ALIGN.CENTER)
    set_notes(slide,
        "This thesis is about what happens after a wearable HAR model is trained. "
        "Not the model itself - the lifecycle around it: how you run it reliably, "
        "how you detect when something is wrong, and how you decide whether to change anything.")


def slide_02_gap(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "The Gap: What HAR Papers Skip",
                  "Published HAR papers stop at offline accuracy. This thesis starts there.")
    L, T, W, H = content_area()
    # left column
    add_rect(slide, L, T, Inches(5.8), H, WHITE, MID_BLUE)
    txb(slide, "Standard wearable HAR paper",
        L + Inches(0.2), T + Inches(0.15), Inches(5.4), Inches(0.4),
        font_size=14, bold=True, color=MID_BLUE)
    txb(slide,
        "Train  ->  Evaluate  ->  Report accuracy\n\n(model development, once, offline)",
        L + Inches(0.2), T + Inches(0.65), Inches(5.4), Inches(1.5),
        font_size=15, color=DARK_GREY)
    txb(slide,
        "What happens next?\n\n- Different user\n- Different sensor session\n- Weeks or months later\n- No ground-truth labels at runtime",
        L + Inches(0.2), T + Inches(2.3), Inches(5.4), Inches(2.5),
        font_size=13, color=DARK_GREY)
    # right column
    RX = L + Inches(6.3)
    add_rect(slide, RX, T, Inches(6.0), H, DARK_BLUE)
    txb(slide, "This thesis",
        RX + Inches(0.2), T + Inches(0.15), Inches(5.6), Inches(0.4),
        font_size=14, bold=True, color=LIGHT_BLUE)
    txb(slide,
        "Train  ->  Execute  ->  Monitor\n->  Govern  ->  Decide\n\n"
        "offline-first - single-machine - reproducible\n\n"
        "- 7-stage operational assessment path\n"
        "- 3-stage gated mutation path\n"
        "- Multi-signal monitoring without labels\n"
        "- Retraining as a deliberate act, not automatic",
        RX + Inches(0.2), T + Inches(0.65), Inches(5.6), Inches(4.6),
        font_size=14, color=WHITE)
    set_notes(slide,
        "Most wearable HAR papers train a model, measure accuracy on a held-out test, and publish. "
        "That is necessary. But when the same model runs on data from a different user, with slightly "
        "different preprocessing, or months later - how does it behave? Who decides whether to retrain? "
        "That is the question this thesis addresses.")


def slide_03_domain(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Application Domain: Why Repetitive Wrist Behaviors?",
                  "Anxiety-relevant repetitive behaviors can be studied as wrist-IMU activity patterns.")
    L, T, W, H = content_area()
    txb(slide,
        "Repetitive hand- and wrist-centered behaviors:",
        L, T, W, Inches(0.45),
        font_size=18, bold=True, color=DARK_BLUE)
    txb(slide,
        "hand tapping  -  hand scratching  -  nail biting\nhair pulling  -  skin picking  -  hand rubbing",
        L, T + Inches(0.5), W, Inches(0.7),
        font_size=17, color=DARK_GREY)
    txb(slide,
        "Expressed as short, repeated wrist movements  ->  observable from accelerometer + gyroscope\n"
        "Passive sensing: no clinician present, no recall bias.",
        L, T + Inches(1.35), W, Inches(0.8),
        font_size=14, color=DARK_GREY)
    # anchor box
    add_rect(slide, L, T + Inches(2.35), W, Inches(1.1), DARK_BLUE)
    txb(slide,
        '"This thesis does not diagnose mental health conditions.\n'
        ' It treats these behaviors as observable behavioral proxies."',
        L + Inches(0.25), T + Inches(2.5), W - Inches(0.5), Inches(0.8),
        font_size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txb(slide,
        "Engineering target:  build a reproducible, monitored, offline-first MLOps pipeline\n"
        "around a wrist-IMU HAR classifier - not a clinical diagnostic instrument.",
        L, T + Inches(3.65), W, Inches(0.8),
        font_size=13, color=DARK_GREY)
    set_notes(slide,
        "The application domain is repetitive hand- and wrist-centered behavior relevant to "
        "anxiety or distress contexts. A wrist-worn IMU can observe these movement patterns "
        "passively, without a clinician present, without recall bias. This thesis does not claim "
        "a clinical diagnostic system or a clinical taxonomy. It treats these behaviors as an "
        "engineering target that motivates building a governed pipeline.")


def slide_04_claim(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, DARK_BLUE)
    txb(slide, "The contribution is not a new classifier.",
        Inches(1.0), Inches(1.0), Inches(11.3), Inches(0.7),
        font_size=28, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txb(slide,
        "It is a reproducible, monitored, and governed\noffline-first MLOps lifecycle for wearable HAR",
        Inches(1.0), Inches(2.0), Inches(11.3), Inches(1.0),
        font_size=26, bold=False, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    add_rect(slide, Inches(1.5), Inches(3.3), Inches(10.3), Inches(2.1), MID_BLUE)
    txb(slide,
        "7-stage operational assessment path\n(observe, infer, evaluate, monitor, govern)\n\n"
        "3-stage gated mutation path\n(retrain, register, promote - explicit flag only)",
        Inches(1.8), Inches(3.45), Inches(9.7), Inches(1.8),
        font_size=16, color=WHITE)
    txb(slide,
        "MLOps Level 1 - by design, not by limitation",
        Inches(1.0), Inches(5.65), Inches(11.3), Inches(0.4),
        font_size=14, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    set_notes(slide,
        "Here is the claim. Not: I built the most accurate HAR model. Not: I built a clinical system. "
        "The claim is: the lifecycle can be designed so that preprocessing decisions are traceable, "
        "monitoring signals are multi-dimensional, and retraining is a deliberate act - not an automatic reflex.")


def slide_05_architecture(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Architecture: Two Explicit Paths",
                  "Stage 1-7 observes and governs. Stage 8-10 mutates. Explicitly separated.")
    L, T, W, H = content_area()
    # labels left
    txb(slide,
        "Stage 1-7\nOperational\nassessment path\n(observe, infer,\nevaluate, monitor,\ngovern)",
        L, T + Inches(0.1), Inches(2.1), Inches(3.0),
        font_size=13, bold=False, color=DARK_BLUE)
    txb(slide,
        "Stage 8-10\nGoverned\nmutation path\n(retrain, register,\npromote baseline)\n- explicit flag only -",
        L, T + Inches(3.2), Inches(2.1), Inches(2.0),
        font_size=13, bold=False, color=MID_BLUE)
    # figure
    add_figure(slide, "pipeline", L + Inches(2.2), T, Inches(10.1), H)
    set_notes(slide,
        "The architecture has two linked but distinct flows. The blue band - Stages 1 to 7 - runs every session. "
        "It ingests data, validates the preprocessing contract, runs inference, evaluates, monitors, and makes a "
        "governance decision. The orange band - Stages 8 to 10 - only runs when explicitly activated. "
        "Retraining changes operational state, so it must be gated. That separation is not cosmetic. "
        "It is the core governance design.")


def slide_06_scalable(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, 'What "Scalable" Actually Means',
                  "Modular, reproducible, configurable, artifact-tracked, extensible - not cloud-scale.")
    L, T, W, H = content_area()
    # left - NOT this
    add_rect(slide, L, T, Inches(5.6), H, WHITE, RED_ACC)
    txb(slide, "NOT this:", L + Inches(0.2), T + Inches(0.15), Inches(5.2), Inches(0.4),
        font_size=15, bold=True, color=RED_ACC)
    txb(slide,
        "x  Cloud-scale deployment\nx  Multi-tenant streaming\nx  Automated continuous retraining\nx  Production-grade clinical system",
        L + Inches(0.2), T + Inches(0.65), Inches(5.2), Inches(2.5),
        font_size=15, color=DARK_GREY)
    # right - THIS
    RX = L + Inches(6.1)
    add_rect(slide, RX, T, Inches(6.2), H, DARK_BLUE)
    txb(slide, "THIS:", RX + Inches(0.2), T + Inches(0.15), Inches(5.8), Inches(0.4),
        font_size=15, bold=True, color=LIGHT_BLUE)
    txb(slide,
        "OK  Each stage is independently replaceable\n"
        "OK  YAML config layer - no code edits for thresholds\n"
        "OK  All artifacts run-scoped and versioned\n"
        "OK  Mutation stages activated by flag, not default\n"
        "OK  Stage 8-10 extensible without redesigning 1-7",
        RX + Inches(0.2), T + Inches(0.65), Inches(5.8), Inches(4.6),
        font_size=14, color=WHITE)
    set_notes(slide,
        "The word 'scalable' in the thesis title does not mean cloud infrastructure. It means the pipeline "
        "can absorb a new model checkpoint, a changed dataset, or an updated threshold without dismantling "
        "and rebuilding. Each stage has one responsibility, one component file. The configuration layer "
        "controls behavior without touching code. That is what scalable means here.")


def slide_07_contract(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Data and Model A Contract",
                  "Model A is the defended proof-of-concept runtime candidate. Its contract is fully persisted and verified.")
    L, T, W, H = content_area()
    rows = [
        ("Training data",
         "Garmin Venu 3  -  all_users training split  -  11 classes (ADAMSense taxonomy)\nUser 7 excluded from training, scaler fit, and model selection; external evaluation only"),
        ("Model A",
         "87,083 params  -  1D-CNN + BiLSTM  -  Row-wise time-major  -  (batch, 200, 6)\n"
         "Garmin train-only StandardScaler (persisted JSON + joblib, 0.0 parity verified)\n"
         "SHA-256 label order fingerprint persisted and checked"),
        ("Preprocessing contract",
         "unit conversion (milliG -> m/s^2 when needed)  ->  scaler  ->  windowing  ->  Model A"),
        ("Status",
         "Proof-of-concept runtime candidate\n"
         "NOT: production-grade  -  NOT: clinical device  -  NOT: population-level proof"),
    ]
    row_h = Inches(1.2)
    for i, (label, val) in enumerate(rows):
        y = T + i * row_h
        bg = DARK_BLUE if i % 2 == 0 else MID_BLUE
        add_rect(slide, L, y, Inches(2.6), row_h, bg)
        txb(slide, label, L + Inches(0.1), y + Inches(0.35), Inches(2.4), Inches(0.5),
            font_size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_rect(slide, L + Inches(2.65), y, Inches(9.88), row_h, WHITE, MID_BLUE)
        txb(slide, val, L + Inches(2.8), y + Inches(0.15), Inches(9.5), row_h - Inches(0.3),
            font_size=12, color=DARK_GREY)
    set_notes(slide,
        "Model A is the defended runtime candidate. 87,000 parameters. The scaler is fitted only on "
        "Garmin training data - not on the external evaluation set. That scaler is persisted in two "
        "redundant forms and verified to agree to 0.0 absolute difference at evaluation time. "
        "The label order of 11 classes has a persisted SHA-256 fingerprint. Every parameter that matters "
        "is frozen and checked. That is what a runtime contract means.")


def slide_08_abc(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "ABC Comparison: Three Models, One Lesson",
                  "Same tensor shape. Different contracts. Wildly different behavior.")
    L, T, W, H = content_area()
    # bullet summary left
    lines = [
        ("Model A", "reproducible contract - modest but honest - all 11 classes", GREEN_ACC),
        ("Model B", "non-persisted full-evaluation scaler -> not a fixed runtime contract", MID_BLUE),
        ("Model C", "same checkpoint as B, wrong contract -> 7.6% accuracy, 4/11 classes", RED_ACC),
    ]
    for i, (model, desc, color) in enumerate(lines):
        y = T + i * Inches(0.75)
        txb(slide, model, L, y, Inches(1.5), Inches(0.6),
            font_size=15, bold=True, color=color)
        txb(slide, desc, L + Inches(1.6), y, Inches(4.8), Inches(0.6),
            font_size=13, color=DARK_GREY)
    add_rect(slide, L, T + Inches(2.4), Inches(6.4), Inches(0.75), DARK_BLUE)
    txb(slide,
        "Same tensor shape (batch, 200, 6) is necessary but NOT sufficient.\nContract = shape + scaler + layout + label order.",
        L + Inches(0.15), T + Inches(2.5), Inches(6.1), Inches(0.65),
        font_size=12, bold=True, color=WHITE)
    # figure right
    add_figure(slide, "abc", L + Inches(6.6), T, Inches(5.93), H)
    set_notes(slide,
        "Three models, all with the same nominal input shape. Completely different behavior. "
        "Model A is the honest candidate: modest external accuracy, reproducible, all 11 classes. "
        "Model B uses a non-persisted scaler recomputed from the full evaluation dataframe - "
        "its native diagnostic result is not a fixed reproducible runtime contract. That is why "
        "the 47-point internal-to-external gap exists. Model C is the contract-mismatch lesson: "
        "the same checkpoint as B, run without its scaler, collapses to 7.6 percent and uses "
        "only 4 of 11 classes. Same shape is not enough. The contract matters.")


def slide_09_monitoring(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Monitoring: Three Signals, One Governance Decision",
                  "No single signal decides. CRITICAL = severity.  REVIEW = governance action.  Different fields.")
    L, T, W, H = content_area()
    add_figure(slide, "monitoring", L, T, W, H)
    set_notes(slide,
        "Stage 6 computes three independent monitoring assessments: one on confidence and uncertainty, "
        "one on prediction stability over time, one on distribution drift. Each gets its own rating. "
        "Stage 7 combines them with a two-of-three voting rule, a collapse guard, and a cooldown gate. "
        "CRITICAL is a severity rating. REVIEW is the action. They are two separate fields. "
        "On both defended evidence runs, CRITICAL signals fired on confidence/uncertainty, "
        "drift and temporal remained HEALTHY, and the action was REVIEW - not RETRAIN.")


def slide_10_trigger(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Trigger Policy: Why Two-of-Three Voting?",
                  "Single-signal: 13.9% false alarm rate.  Two-of-three: 0.7% FAR, full episode recall.")
    L, T, W, H = content_area()
    # table left
    header = ["Policy", "Precision", "FAR", "Episode recall"]
    rows_data = [
        ("single_signal",  "0.8406", "13.9 %", "100 %"),
        ("two_of_three OK", "0.9878", " 0.7 %", "100 %"),
        ("+cooldown 24 h",  "1.0000", " 0.0 %", " 87.5 %"),
    ]
    col_w = [Inches(2.8), Inches(1.5), Inches(1.4), Inches(1.8)]
    col_x = [L]
    for cw in col_w[:-1]:
        col_x.append(col_x[-1] + cw)
    row_h = Inches(0.55)
    # header row
    for ci, (hdr, cx, cw) in enumerate(zip(header, col_x, col_w)):
        add_rect(slide, cx, T, cw, row_h, DARK_BLUE)
        txb(slide, hdr, cx + Inches(0.05), T + Inches(0.1), cw - Inches(0.1), row_h,
            font_size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    row_colors = [WHITE, LIGHT_BLUE, WHITE]
    for ri, (rdata, rcol) in enumerate(zip(rows_data, row_colors)):
        y = T + (ri + 1) * row_h
        is_defended = ri == 1
        for ci, (cell, cx, cw) in enumerate(zip(rdata, col_x, col_w)):
            bg = MID_BLUE if is_defended else rcol
            add_rect(slide, cx, y, cw, row_h, bg, MID_BLUE)
            fc = WHITE if is_defended else DARK_GREY
            txb(slide, cell, cx + Inches(0.05), y + Inches(0.1), cw - Inches(0.1), row_h,
                font_size=12, bold=is_defended, color=fc, align=PP_ALIGN.CENTER)
    txb(slide,
        "-> Two-of-three: full recall, 20x fewer false alarms than single-signal.\n"
        "-> 24h cooldown: zero false alarms but misses 2 of 16 episodes.\n"
        "-> Governance trade-off is explicit and documented.",
        L, T + Inches(2.3), Inches(7.4), Inches(1.4),
        font_size=13, color=DARK_BLUE)
    # figure right
    add_figure(slide, "trigger", L + Inches(7.6), T, Inches(4.93), H)
    set_notes(slide,
        "The trigger policy comparison replays 16 monitored episodes. Single-signal triggering fires "
        "too easily - 1 in 7 alerts is spurious. The two-of-three policy requires two of the three "
        "signal groups to be in a concerning state before firing. That gives precision 0.99 and a "
        "false alarm rate under 1 percent while still catching every genuine episode. "
        "The 24-hour cooldown eliminates false alarms entirely but misses 2 episodes. "
        "The trade-off is documented. Two-of-three without cooldown is the defended choice.")


def slide_11_ablation(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Preprocessing Sensitivity: Gravity Removal Made It Worse",
                  "Intuitively reasonable signal cleaning worsened collapse. Train-serve parity is empirically real.")
    L, T, W, H = content_area()
    # summary table left
    cols = ["Config", "Unique classes", "Hand-tapping %"]
    data = [
        ("A  baseline",    "7.08", "78.4 %"),
        ("B  +calibration","7.88", "73.2 %"),
        ("C  +gravity removal", "5.32", "96.7 % high"),
        ("D  +calibration + gravity", "9.72", "50.1 % lower"),
    ]
    row_h = Inches(0.62)
    cw = [Inches(2.3), Inches(1.9), Inches(1.9)]
    cx = [L, L + cw[0], L + cw[0] + cw[1]]
    for ci, (hdr, x, w) in enumerate(zip(cols, cx, cw)):
        add_rect(slide, x, T, w, row_h, DARK_BLUE)
        txb(slide, hdr, x + Inches(0.05), T + Inches(0.1), w, row_h,
            font_size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    highlight_colors = [WHITE, WHITE, RGBColor(0xFF, 0xDD, 0xDD), RGBColor(0xDD, 0xFF, 0xDD)]
    for ri, (row, hl) in enumerate(zip(data, highlight_colors)):
        y = T + (ri + 1) * row_h
        for ci, (cell, x, w) in enumerate(zip(row, cx, cw)):
            add_rect(slide, x, y, w, row_h, hl, MID_BLUE)
            txb(slide, cell, x + Inches(0.05), y + Inches(0.1), w, row_h,
                font_size=12, color=DARK_GREY, align=PP_ALIGN.CENTER)
    txb(slide,
        "-> Gravity removal alone (C) worsened collapse dramatically.\n"
        "-> Preprocessing is part of the model contract.\n"
        "-> \"Intuitively reasonable\" != \"operationally safe.\"",
        L, T + Inches(3.2), Inches(6.2), Inches(1.2),
        font_size=13, color=DARK_BLUE)
    # figure right
    add_figure(slide, "ablation", L + Inches(6.4), T, Inches(6.13), H)
    set_notes(slide,
        "We ran 25 session pairs under four preprocessing configurations, holding the model constant. "
        "Gravity removal alone - configuration C - made class collapse dramatically worse: only 5 classes "
        "predicted on average, and 97 percent of predictions concentrated on hand-tapping. Adding "
        "calibration on top recovered diversity. The lesson: preprocessing is not neutral preamble - "
        "it is part of the operational contract. Changing it at inference time without retraining "
        "is the exact train-serve mismatch the thesis is built around.")


def slide_12_collapse(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Model Choice Drives Collapse: Same Input, Different Behavior",
                  "Old model collapse was reproduced on a controlled rerun - it is a model property, not an input property.")
    L, T, W, H = content_area()
    add_figure(slide, "old_vs_new", L, T, Inches(8.5), H)
    # summary box right
    RX = L + Inches(8.7)
    add_rect(slide, RX, T, Inches(3.83), H, DARK_BLUE)
    txb(slide,
        "Same raw session\nall three runs\n\n"
        "Old model:\n85.6% top-class\n9/11 classes\n\n"
        "New model:\n29.0% top-class\n11/11 classes\n\n"
        "Old model (rerun):\n85.6% top-class\n9/11 classes\n<- reproduced\n\n"
        "-> Collapse is a\nmodel property,\nnot an input property.",
        RX + Inches(0.15), T + Inches(0.15), Inches(3.5), H - Inches(0.3),
        font_size=12, color=WHITE)
    set_notes(slide,
        "We ran the same raw sensor file through the old model, the new retrained model, and the old model "
        "a second time as a control. The old model reproduced the same collapse pattern exactly - 85 percent "
        "hand-tapping, 9 classes, both times. The new model used all 11 classes with 29 percent dominance. "
        "The input was identical. The collapse was model-specific. That is why Stage 7 includes a collapse guard.")


def slide_13_negative(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Negative Result: Routing Change != Quality Improvement",
                  "Mean confidence unchanged at 0.8578 before and after a plausible intervention bundle.")
    L, T, W, H = content_area()
    # 26-session before/after table
    header = ["Metric", "Before", "After", ""]
    col_w = [Inches(4.0), Inches(2.2), Inches(2.2), Inches(4.0)]
    col_x = [L]
    for cw in col_w[:-1]:
        col_x.append(col_x[-1] + cw)
    row_h = Inches(0.62)
    for ci, (hdr, cx, cw) in enumerate(zip(header[:3], col_x[:3], col_w[:3])):
        add_rect(slide, cx, T, cw, row_h, DARK_BLUE)
        txb(slide, hdr, cx + Inches(0.05), T + Inches(0.1), cw - Inches(0.1), row_h,
            font_size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    rows_data = [
        ("Mean confidence", "0.8578", "0.8578", WHITE, "<- unchanged"),
        ("Mean dominant-class share", "81.2 %", "67.3 %", RGBColor(0xFF, 0xEE, 0xCC), "<- appears better"),
        ("Mean REVIEW-routed share", " 0.0 %", "66.1 %", RGBColor(0xFF, 0xDD, 0xDD), "<- explains the drop"),
    ]
    for ri, (label, before, after, bg, note) in enumerate(rows_data):
        y = T + (ri + 1) * row_h
        for ci, (cell, cx, cw) in enumerate(zip([label, before, after], col_x[:3], col_w[:3])):
            add_rect(slide, cx, y, cw, row_h, bg, MID_BLUE)
            fc = DARK_GREY
            txb(slide, cell, cx + Inches(0.05), y + Inches(0.12), cw - Inches(0.1), row_h,
                font_size=12, color=fc, align=PP_ALIGN.CENTER if ci > 0 else PP_ALIGN.LEFT)
        txb(slide, note, col_x[2] + col_w[2] + Inches(0.1), y + Inches(0.12),
            Inches(3.7), row_h, font_size=12, color=MID_BLUE)
    add_rect(slide, L, T + Inches(2.4), W, Inches(1.4), DARK_BLUE)
    txb(slide,
        "-> Lower dominance = windows routed to REVIEW, not better classification.\n"
        "-> The quality signal (mean confidence) did not move.\n"
        "-> This is a deliberate negative result - governance must track quality, not routing.",
        L + Inches(0.2), T + Inches(2.5), W - Inches(0.4), Inches(1.2),
        font_size=13, bold=False, color=WHITE)
    set_notes(slide,
        "One of the most academically important results in this thesis is a negative one. We applied a "
        "plausible bundle of interventions to 26 sessions. Dominant-class share dropped from 81 to 67 percent, "
        "which looks like an improvement. But mean confidence was unchanged at 0.8578 before and after. "
        "The apparent improvement was entirely explained by routing windows into REVIEW. "
        "The underlying quality signal did not move. This is the empirical argument for why governance "
        "must track quality signals, not routing distributions.")


def slide_14_evidence(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Defended Evidence Runs: The Honest External Ceiling",
                  "37.6% external accuracy + REVIEW routing + auto_retrain=false is correct governed behavior.")
    L, T, W, H = content_area()
    # two evidence boxes
    box_w = Inches(5.9)
    for bi, (title, lines, bg) in enumerate([
        ("Garmin unlabeled run", [
            "1,304 windows  -  50 Hz  -  no labels",
            "Mean confidence:  0.393",
            "Drift status:     HEALTHY",
            "Monitoring:       CRITICAL (low confidence)",
            "Temporal status:  HEALTHY",
            "Trigger action:   REVIEW",
            "auto_retrain:     false",
        ], DARK_BLUE),
        ("User 7 external labeled run", [
            "989 windows  -  50 Hz  -  labeled",
            "Accuracy:         37.6%   Macro F1: 34.1%",
            "Mean confidence:  0.359",
            "Classes used:     11 / 11",
            "Monitoring:       CRITICAL (low confidence)",
            "Drift/temporal:   HEALTHY",
            "Trigger action:   REVIEW   auto_retrain: false",
        ], MID_BLUE),
    ]):
        bx = L + bi * (box_w + Inches(0.5))
        add_rect(slide, bx, T, box_w, H, bg)
        txb(slide, title, bx + Inches(0.15), T + Inches(0.1), box_w - Inches(0.3), Inches(0.45),
            font_size=14, bold=True, color=WHITE)
        for li, ln in enumerate(lines):
            txb(slide, ln, bx + Inches(0.2), T + Inches(0.6) + li * Inches(0.6),
                box_w - Inches(0.4), Inches(0.55),
                font_size=12, color=WHITE)
    # bottom label
    txb(slide,
        "-> Both runs: Stage 1-7 all SUCCESS  -  Risk flagged  -  Routed to human review  -  No model mutation",
        L, T + H - Inches(0.1), W, Inches(0.4),
        font_size=13, bold=True, color=DARK_BLUE)
    set_notes(slide,
        "The two defended evidence runs. User 7: an external participant not in the training set. "
        "37 percent accuracy - low, honest, expected for cross-user transfer. "
        "The monitoring layer correctly identified low confidence and high uncertainty, "
        "while drift and temporal status remained healthy. Stage 7 routed the run to REVIEW. "
        "The Garmin unlabeled run: 1,304 windows of real wrist sensor data, no labels. "
        "Drift status HEALTHY, but confidence low enough to trigger REVIEW. "
        "Both runs: auto_retrain=false. That is not a missing feature. That is the governance policy working.")


def slide_15_nonclaims(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "What the Pipeline Does NOT Claim",
                  "Scope limits are explicit non-claims - documented, not hidden.")
    L, T, W, H = content_area()
    nots = [
        "Clinical diagnosis or population-level generalisation",
        "Model A is production-grade or deployable at scale",
        "Subject-independent generalisation beyond User 7",
        "Confidence calibration solved  (mean conf 0.359 on User 7)",
        "Auto-retraining as a live feature  (auto_retrain=false by design)",
        "CRITICAL monitoring severity means automatic retraining",
        "Stages 8-10/11 are live automatic runtime features",
    ]
    dos = [
        "Reproducible offline-first lifecycle",
        "Honest external accuracy ceiling reported",
        "Risk detectable without ground-truth labels",
        "Retraining gated by auditable policy",
    ]
    add_rect(slide, L, T, Inches(6.1), H, WHITE, RED_ACC)
    txb(slide, "x  Not claimed:", L + Inches(0.15), T + Inches(0.1), Inches(5.8), Inches(0.4),
        font_size=14, bold=True, color=RED_ACC)
    for i, item in enumerate(nots):
        txb(slide, "-  " + item,
            L + Inches(0.2), T + Inches(0.6) + i * Inches(0.66), Inches(5.7), Inches(0.6),
            font_size=12, color=DARK_GREY)
    RX = L + Inches(6.4)
    add_rect(slide, RX, T, Inches(6.13), H, DARK_BLUE)
    txb(slide, "OK  What IS contributed:", RX + Inches(0.15), T + Inches(0.1), Inches(5.8), Inches(0.4),
        font_size=14, bold=True, color=LIGHT_BLUE)
    for i, item in enumerate(dos):
        txb(slide, "-  " + item,
            RX + Inches(0.2), T + Inches(0.6) + i * Inches(0.9), Inches(5.7), Inches(0.8),
            font_size=13, color=WHITE)
    set_notes(slide,
        "These are the explicit non-claims. They are not weaknesses the examiner found. "
        "They are scope boundaries the thesis documents. A system that reports its limitations "
        "clearly is a stronger contribution than one that overstates.")


def slide_16_rq(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, LIGHT_GREY)
    add_title_bar(slide, "Research Questions: Bounded Answers",
                  "All four RQs answered - each with explicit evidence and explicit bounds.")
    L, T, W, H = content_area()
    rqs = [
        ("RQ1", "Can the pipeline detect risk without labels?",
         "Yes, partially. Monitoring signals respond directionally.\n(Not: recover label-level accuracy)"),
        ("RQ2", "How strongly do preprocessing decisions affect behavior?",
         "Strongly and non-monotonically.\n(Gravity removal alone worsened collapse - Config C)"),
        ("RQ3", "Can governed trigger policy improve safety?",
         "Yes. Two-of-three: precision 0.9878, FAR 0.7%, full episode recall.\n(Bounded to one replay set)"),
        ("RQ4", "How much collapse is from model choice vs input?",
         "Materially from model choice.\n(Controlled rerun reproduced old-model collapse pattern exactly)"),
    ]
    rq_h = Inches(1.25)
    for i, (rq, question, answer) in enumerate(rqs):
        y = T + i * rq_h
        add_rect(slide, L, y, Inches(0.9), rq_h, DARK_BLUE)
        txb(slide, rq, L + Inches(0.05), y + Inches(0.4), Inches(0.8), Inches(0.5),
            font_size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_rect(slide, L + Inches(0.95), y, Inches(5.3), rq_h, WHITE, MID_BLUE)
        txb(slide, question, L + Inches(1.05), y + Inches(0.1), Inches(5.1), Inches(0.5),
            font_size=12, bold=True, color=DARK_BLUE)
        add_rect(slide, L + Inches(6.3), y, Inches(6.23), rq_h, MID_BLUE)
        txb(slide, answer, L + Inches(6.45), y + Inches(0.1), Inches(5.9), rq_h - Inches(0.2),
            font_size=12, color=WHITE)
    set_notes(slide,
        "Four bounded answers. Partial on RQ1 - the signals move in the right direction but they are proxies, "
        "not ground truth. Strong on RQ2 - preprocessing matters more than expected, and in a non-obvious direction. "
        "Strong on RQ3 - the voting policy is a clear improvement over single-signal. "
        "Clear on RQ4 - the controlled rerun shows the collapse is model-specific. "
        "Each answer is tied to archived run artifacts. None of them is a claim beyond the available evidence.")


def slide_17_contribution(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, DARK_BLUE)
    txb(slide, "Contribution",
        Inches(1.0), Inches(0.4), Inches(11.3), Inches(0.6),
        font_size=18, bold=False, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    txb(slide,
        "A reproducible, auditable, and governance-aware\noffline-first MLOps lifecycle for wearable HAR",
        Inches(0.8), Inches(1.1), Inches(11.7), Inches(1.1),
        font_size=26, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_rect(slide, Inches(1.0), Inches(2.4), Inches(11.3), Inches(2.8), MID_BLUE)
    txb(slide,
        "Model A  -  frozen proof-of-concept runtime candidate  (87,083 params)\n\n"
        "Model B  -  diagnostic reference only  (non-persisted scaler, not a fixed runtime contract)\n\n"
        "Model C  -  checkpoint-contract mismatch evidence  (7.6% on User 7)\n\n"
        "Review-first trigger policy  -  CRITICAL severity routes to human review, not automatic retraining",
        Inches(1.25), Inches(2.55), Inches(10.8), Inches(2.55),
        font_size=15, color=WHITE)
    txb(slide,
        "The pipeline is not broken. It executes end-to-end, detects uncertainty, and routes risk to REVIEW.\n"
        "The remaining limitation is model confidence, calibration, and external generalisation.\n"
        "Those limitations are documented - not hidden.",
        Inches(0.8), Inches(5.4), Inches(11.7), Inches(0.9),
        font_size=14, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    set_notes(slide,
        "That is the contribution. Not a new architecture. Not a clinical tool. A lifecycle in which the "
        "distinctions that matter - between observation and mutation, between monitoring severity and governance "
        "action, between internal accuracy and deployment transferability - are all observable from archived artifacts.")


def slide_18_close(prs):
    slide = prs.slides.add_slide(blank_layout(prs))
    add_bg(slide, DARK_BLUE)
    add_figure(slide, "scope_map",
               Inches(0), Inches(0), SLIDE_W, SLIDE_H)
    # dim overlay
    add_rect(slide, Inches(0), Inches(0), SLIDE_W, SLIDE_H,
             RGBColor(0x0A, 0x1E, 0x3A))
    # send overlay to back so text renders on top
    overlay = slide.shapes[-1]
    sp_tree = slide.shapes._spTree
    sp = overlay._element
    sp_tree.remove(sp)
    sp_tree.insert(2, sp)
    txb(slide, "Thank you.",
        Inches(1.0), Inches(1.5), Inches(11.3), Inches(0.9),
        font_size=40, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    txb(slide, "Offline-first  -  Reproducible  -  Governed",
        Inches(1.0), Inches(2.6), Inches(11.3), Inches(0.5),
        font_size=20, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    txb(slide, "MLOps Level 1 - by design, not by limitation",
        Inches(1.0), Inches(3.2), Inches(11.3), Inches(0.5),
        font_size=18, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)
    txb(slide, "Questions?",
        Inches(1.0), Inches(4.5), Inches(11.3), Inches(0.7),
        font_size=32, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    set_notes(slide,
        "Thank you. The system is not Level 2 MLOps because Level 2 is not safe here - "
        "unlabeled data, label-scarce monitoring, health-adjacent context. "
        "Level 1 with explicit governance is the correct target. "
        "I am happy to go into any of the model decision, monitoring signals, "
        "trigger policy, or preprocessing ablation in more detail.")


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    prs = new_prs()
    slide_01_title(prs)
    slide_02_gap(prs)
    slide_03_domain(prs)
    slide_04_claim(prs)
    slide_05_architecture(prs)
    slide_06_scalable(prs)
    slide_07_contract(prs)
    slide_08_abc(prs)
    slide_09_monitoring(prs)
    slide_10_trigger(prs)
    slide_11_ablation(prs)
    slide_12_collapse(prs)
    slide_13_negative(prs)
    slide_14_evidence(prs)
    slide_15_nonclaims(prs)
    slide_16_rq(prs)
    slide_17_contribution(prs)
    slide_18_close(prs)

    out = r"d:\study apply\ML Ops\MasterArbeit_MLops\internal\writing\defense_slides.pptx"
    prs.save(out)
    print(f"Saved: {out}")
    print(f"Slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()
