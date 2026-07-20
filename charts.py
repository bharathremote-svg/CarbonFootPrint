"""
charts.py
=========
Matplotlib figure builders. Kept separate from app.py so they can be
reused/tested without spinning up Streamlit.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

CATEGORY_COLORS = {
    "Home Energy": "#2f4a3d",
    "Transport": "#c9a24b",
    "Diet": "#c17a5e",
    "Lifestyle": "#6f95a8",
}


def _style_fig(fig, dark_mode: bool):
    bg = "#22251f" if dark_mode else "#ffffff"
    fig.patch.set_facecolor(bg)
    return fig


def eco_score_donut(score: int, dark_mode: bool = False):
    text_color = "#f0efe9" if dark_mode else "#1f241f"
    muted = "#a2a49b" if dark_mode else "#6b7280"
    track_color = "#33362e" if dark_mode else "#e9e7df"
    fill_color = "#c17a5e" if score < 60 else "#2f4a3d"

    fig, ax = plt.subplots(figsize=(3.2, 3.2), subplot_kw={"aspect": "equal"})
    _style_fig(fig, dark_mode)
    ax.set_facecolor(fig.get_facecolor())

    wedge_bg = mpatches.Wedge((0, 0), 1, 0, 360, width=0.22, facecolor=track_color)
    ax.add_patch(wedge_bg)

    angle = 360 * (score / 100)
    # start at top (90 deg) and go clockwise
    wedge_fg = mpatches.Wedge((0, 0), 1, 90 - angle, 90, width=0.22, facecolor=fill_color)
    ax.add_patch(wedge_fg)

    ax.text(0, 0.08, str(score), ha="center", va="center",
            fontsize=30, fontweight="bold", color=text_color, family="serif")
    ax.text(0, -0.18, "/ 100", ha="center", va="center", fontsize=10, color=muted)

    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.axis("off")
    fig.tight_layout()
    return fig


def emissions_breakdown_donut(breakdown: dict, dark_mode: bool = False):
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    colors = [CATEGORY_COLORS.get(k, "#999999") for k in labels]

    fig, ax = plt.subplots(figsize=(3.4, 3.4), subplot_kw={"aspect": "equal"})
    _style_fig(fig, dark_mode)
    ax.set_facecolor(fig.get_facecolor())

    wedges, _ = ax.pie(
        values, colors=colors, startangle=90,
        wedgeprops=dict(width=0.38, edgecolor=fig.get_facecolor(), linewidth=2),
    )
    ax.axis("equal")
    fig.tight_layout()
    return fig


def comparison_bar_chart(data: list, dark_mode: bool = False):
    """data: list of (label, tonnes) tuples, 'You' first."""
    text_color = "#f0efe9" if dark_mode else "#1f241f"
    grid_color = "#33362e" if dark_mode else "#eceae2"

    labels = [d[0] for d in data][::-1]
    values = [d[1] for d in data][::-1]
    colors = ["#2f4a3d" if lbl == "You" else "#8a9a8c" for lbl in labels]

    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    _style_fig(fig, dark_mode)
    ax.set_facecolor(fig.get_facecolor())

    bars = ax.barh(labels, values, color=colors, height=0.55)
    for bar, v in zip(bars, values):
        ax.text(v + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}t", va="center", fontsize=9, color=text_color)

    ax.set_xlim(0, max(values) * 1.2)
    ax.tick_params(colors=text_color, labelsize=10)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(grid_color)
    ax.grid(axis="x", color=grid_color, linewidth=0.7)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig
