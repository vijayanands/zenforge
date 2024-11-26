import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from matplotlib import pyplot as plt


def create_styled_metric(label, value, icon):
    styled_metric_css = """
    <style>
    .metric-card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 20px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .metric-card h3 {
        font-size: 16px;
        margin-bottom: 10px;
        color: #555;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .icon {
        font-size: 24px;
        margin-bottom: 10px;
    }
    </style>
    """

    metric_html = f"""
    <div class="metric-card">
        <div class="icon">{icon}</div>
        <h3>{label}</h3>
        <div class="metric-value">{value}</div>
    </div>
    """

    # Combine the CSS and the metric HTML
    full_html = styled_metric_css + metric_html

    # Render the metric using st.markdown
    st.markdown(full_html, unsafe_allow_html=True)


def create_styled_bullet_list(items, title=None):
    styled_list_css = """
    <style>
    .styled-list-container {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 20px;
    }
    .styled-list-title {
        font-size: 18px;
        font-weight: bold;
        color: #495057;
        margin-bottom: 10px;
    }
    .styled-list {
        list-style-type: none;
        padding-left: 0;
        margin-bottom: 0;
    }
    .styled-list li {
        position: relative;
        padding-left: 25px;
        margin-bottom: 8px;
        line-height: 1.5;
        color: #495057;
    }
    .styled-list li:before {
        content: '•';
        position: absolute;
        left: 10px;
        color: #495057;
        font-size: 18px;
        line-height: 1.2;
    }
    .styled-list li:last-child {
        margin-bottom: 0;
    }
    </style>
    """

    list_items = "".join([f"<li>{item}</li>" for item in items])
    title_html = f"<div class='styled-list-title'>{title}</div>" if title else ""
    list_html = f"""
    <div class="styled-list-container">
        {title_html}
        <ul class="styled-list">
            {list_items}
        </ul>
    </div>
    """

    # Combine the CSS and the list HTML
    full_html = styled_list_css + list_html

    # Render the styled list using st.markdown
    st.markdown(full_html, unsafe_allow_html=True)


def create_styled_radio_buttons(label, options, key):
    st.markdown(
        f"""
    <style>
    div.row-widget.stRadio > div {{
        flex-direction: row;
        align-items: center;
    }}
    div.row-widget.stRadio > div[role="radiogroup"] {{
        background-color: #f0f2f6;
        border-radius: 25px;
        padding: 5px;
        display: inline-flex;
    }}
    div.row-widget.stRadio > div[role="radiogroup"] > label {{
        padding: 10px 20px;
        margin: 0;
        border-radius: 20px;
        transition: all 0.3s ease;
        color: #31333F;
    }}
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover {{
        background-color: rgba(51, 102, 204, 0.1);
    }}
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {{
        display: none;
    }}
    div.row-widget.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {{
        background-color: #3366cc;
        color: white;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(51, 102, 204, 0.3);
    }}
    .custom-radio-label {{
        font-size: 18px;
        font-weight: bold;
        color: #31333F;
        margin-bottom: 10px;
        text-align: left;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(f'<p class="custom-radio-label">{label}</p>', unsafe_allow_html=True)
    return st.radio("", options, key=key, label_visibility="collapsed")


def create_pie_chart(
    data,
    names,
    values,
    title=None,
    color_sequence=px.colors.qualitative.Pastel,
    hole=0.4,
    height=400,
    width=400,
    show_legend=False,
    text_info="percent+label",
    hover_info="label+percent+value",
    text_position="inside",
    pull=None,
    sort_values=False,
    color=None,
):
    # Convert to DataFrame if it's a dict
    if isinstance(data, dict):
        data = pd.DataFrame(data)

    # Sort values if requested
    if sort_values:
        data = data.sort_values(by=values, ascending=False)

    fig = px.pie(
        data,
        names=names,
        values=values,
        title=title,
        color_discrete_sequence=color_sequence,
        hole=hole,
        height=height,
        width=width,
        color=color,
    )

    fig.update_traces(
        textposition=text_position,
        textinfo=text_info,
        hoverinfo=hover_info,
        pull=pull,
        marker=dict(line=dict(color="white", width=2)),
    )

    fig.update_layout(
        showlegend=show_legend,
        margin=dict(l=20, r=20, t=30, b=20),
        height=height,
        width=width,
    )

    return fig


def display_pie_chart(fig, use_container_width=True):
    return st.plotly_chart(
        fig, use_container_width=use_container_width, config={"displayModeBar": False}
    )


def create_styled_tabs(tab_labels):
    # CSS for custom tab styling
    st.markdown(
        """
    <style>
        .stTabs {
            background-color: #f1f3f6;
            padding: 10px 20px 0 20px;
            border-radius: 10px 10px 0 0;
            margin-bottom: 20px;  /* Add margin to the bottom of tabs */
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            border-bottom: 1px solid #d1d5db;
        }
        .stTabs [data-baseweb="tab"] {
            height: 60px;
            white-space: pre-wrap;
            background-color: #f1f3f6;
            border-radius: 10px 10px 0 0;
            gap: 10px;
            padding: 10px 20px;
            font-weight: 400;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff;
            border: 1px solid #d1d5db;
            border-bottom: none;
            font-weight: 600;
        }
        .stTabs [data-baseweb="tab-border"] {
            display: none;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #ffffff;
            border-radius: 10px 10px 0 0;
        }
        .stTabs [data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {
            font-size: 16px;
            color: #1f2937;
        }
        .stTabs [aria-selected="true"] [data-testid="stMarkdownContainer"] p {
            color: #111827;
        }
        /* Add spacing between tab content and bottom of page */
        .stTabs [role="tabpanel"] {
            padding-bottom: 20px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Create tabs
    return st.tabs(tab_labels)


def create_progress_bar(name, progress, status):
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.write(f"**{name}**")
        st.progress(progress)
    with col2:
        st.write(f"{progress}%")
    with col3:
        if status == "Completed":
            st.success("Completed")
        elif status == "In Progress":
            st.info("In Progress")
        else:
            st.warning("Not Started")


def style_line_chart(fig, ax):
    # Set color scheme
    line_color = "#3366cc"
    fill_color = "#e6f0ff"

    # Style the line
    for line in ax.lines:
        line.set_color(line_color)
        line.set_linewidth(2)
        line.set_alpha(0.8)

    # Add fill below the line
    ax.fill_between(
        range(len(ax.lines[0].get_ydata())),
        ax.lines[0].get_ydata(),
        color=fill_color,
        alpha=0.3,
    )

    # Style the grid
    ax.grid(True, linestyle="--", alpha=0.3, color="#cccccc")
    ax.set_axisbelow(True)

    # Style the spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")

    # Style the ticks
    ax.tick_params(axis="both", colors="#888888", labelsize=8)

    # Add subtle markers to data points
    ax.plot(
        range(len(ax.lines[0].get_ydata())),
        ax.lines[0].get_ydata(),
        "o",
        color=line_color,
        markersize=4,
        alpha=0.6,
    )

    # Adjust layout
    fig.tight_layout(pad=2)  # Increased padding
    plt.subplots_adjust(bottom=0.2)  # Add more space at the bottom


def create_styled_line_chart(data, x_label, y_label):
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot(range(len(data)), data)
    ax.set_xlabel(x_label, fontsize=9)
    ax.set_ylabel(y_label, fontsize=9)
    style_line_chart(fig, ax)
    return st.pyplot(fig)


def create_styled_bar_chart(x, y, x_label, y_label):
    fig, ax = plt.subplots(figsize=(4, 3))
    colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(x)))  # Use a blue color palette
    bars = ax.bar(x, y, color=colors, alpha=0.8)
    ax.set_xlabel(x_label, fontsize=9)
    ax.set_ylabel(y_label, fontsize=9)

    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.0f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Styling similar to line chart
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#888888")
    ax.spines["bottom"].set_color("#888888")
    ax.tick_params(axis="both", colors="#888888", labelsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.3, color="#cccccc")
    ax.set_axisbelow(True)

    fig.tight_layout(pad=1)
    return st.pyplot(fig)


def apply_styled_dropdown_css():
    st.markdown(
        """
    <style>
    /* Common styles for both select box and date input */
    .stSelectbox [data-baseweb="select"], .stDateInput > div > div {
        background-color: #f0f2f6;
        color: #31333F;
        border: 1px solid #d1d5db;
        border-radius: 4px;
        padding: 0.5rem;
    }
    .stSelectbox [data-baseweb="select"]:hover, .stDateInput > div > div:hover {
        border-color: #3366cc;
    }
    /* Ensure the date input text is visible */
    .stDateInput > div > div > input {
        color: #31333F;
        background-color: transparent;
        border: none;
    }
    /* Style for labels */
    .stSelectbox label, .stDateInput label {
        color: #31333F;
        font-weight: bold;
    }
    /* Style for the Apply Filters button */
    .stButton > button {
        background-color: #3366cc;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #254e9c;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def create_multi_bar_chart(
    data, x, y, labels, title=None, color_sequence=px.colors.qualitative.Pastel
):
    fig = go.Figure()

    for i, column in enumerate(y):
        fig.add_trace(
            go.Bar(
                x=data[x],
                y=data[column],
                name=labels[column],
                marker_color=color_sequence[i % len(color_sequence)],
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title="Amount",
        barmode="group",
        legend_title="Category",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y:,.0f}",
        marker=dict(line=dict(width=1, color="white")),
    )

    return fig
