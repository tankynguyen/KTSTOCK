"""
KTSTOCK - Chart Engine (Plotly)
Tạo biểu đồ chuyên nghiệp cho cổ phiếu và crypto.
"""
from typing import Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from loguru import logger


# ============================================================
# Color Palette
# ============================================================
COLORS = {
    "bg": "#0E1117",
    "card_bg": "#1A1D23",
    "text": "#E0E0E0",
    "muted": "#888",
    "accent": "#FF6B35",
    "accent2": "#F7C948",
    "green": "#00C853",
    "red": "#FF1744",
    "blue": "#2196F3",
    "purple": "#9C27B0",
    "cyan": "#00BCD4",
    "grid": "rgba(255,255,255,0.05)",
}


def _apply_layout(fig: go.Figure, title: str = "", height: int = 500) -> go.Figure:
    """Apply dark theme layout cho mọi chart."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=COLORS["accent"])),
        template="plotly_dark",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        height=height,
        margin=dict(l=50, r=30, t=50, b=40),
        font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
        legend=dict(
            bgcolor="rgba(0,0,0,0.3)", bordercolor=COLORS["grid"],
            font=dict(size=11), orientation="h", yanchor="bottom", y=1.02,
        ),
        xaxis=dict(gridcolor=COLORS["grid"], showgrid=True),
        yaxis=dict(gridcolor=COLORS["grid"], showgrid=True),
        hovermode="x unified",
    )
    return fig


# ============================================================
# CANDLESTICK CHART
# ============================================================
def candlestick_chart(
    df: pd.DataFrame,
    title: str = "",
    show_volume: bool = True,
    show_ma: bool = True,
    ma_periods: list[int] = None,
    height: int = 600,
) -> go.Figure:
    """
    Biểu đồ nến (Candlestick) chuyên nghiệp.

    Args:
        df: DataFrame với columns: date, open, high, low, close, volume
        show_volume: Hiển thị volume subplot
        show_ma: Hiển thị đường MA
        ma_periods: Chu kỳ MA (default: [20, 50])
    """
    ma_periods = ma_periods or [20, 50]
    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=row_heights,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="OHLC",
        increasing_line_color=COLORS["green"],
        decreasing_line_color=COLORS["red"],
    ), row=1, col=1)

    # Moving Averages
    if show_ma:
        ma_colors = [COLORS["accent"], COLORS["cyan"], COLORS["purple"]]
        for i, period in enumerate(ma_periods):
            if len(df) >= period:
                ma = df["close"].rolling(period).mean()
                fig.add_trace(go.Scatter(
                    x=df["date"], y=ma, name=f"SMA {period}",
                    line=dict(width=1.5, color=ma_colors[i % len(ma_colors)]),
                ), row=1, col=1)

    # Volume
    if show_volume and "volume" in df.columns:
        colors = [
            COLORS["green"] if c >= o else COLORS["red"]
            for c, o in zip(df["close"], df["open"])
        ]
        fig.add_trace(go.Bar(
            x=df["date"], y=df["volume"], name="Volume",
            marker_color=colors, opacity=0.6,
        ), row=2, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_xaxes(rangeslider_visible=False)

    return _apply_layout(fig, title, height)


# ============================================================
# TECHNICAL INDICATORS CHART
# ============================================================
def technical_chart(
    df: pd.DataFrame,
    indicators: list[str] = None,
    title: str = "",
    height: int = 700,
) -> go.Figure:
    """
    Biểu đồ chỉ báo kỹ thuật (RSI, MACD, Bollinger, Stochastic).

    Args:
        df: DataFrame đã tính indicators (output từ TechnicalAnalysis.calculate_all())
        indicators: Chỉ báo cần hiển thị ["rsi", "macd", "bollinger", "stochastic"]
    """
    indicators = indicators or ["rsi", "macd"]

    num_panels = 1 + len(indicators)
    row_heights = [0.4] + [0.3 / max(len(indicators), 1)] * len(indicators)

    fig = make_subplots(
        rows=num_panels, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=row_heights,
    )

    # Price
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["close"], name="Close",
        line=dict(color=COLORS["accent"], width=2),
    ), row=1, col=1)

    # Bollinger on price
    if "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df["date"], y=df["bb_upper"], name="BB Upper",
                                 line=dict(color=COLORS["blue"], width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["date"], y=df["bb_lower"], name="BB Lower",
                                 line=dict(color=COLORS["blue"], width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(33,150,243,0.05)"), row=1, col=1)

    for idx, ind in enumerate(indicators, start=2):
        if ind == "rsi" and "rsi" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["rsi"], name="RSI",
                line=dict(color=COLORS["cyan"], width=1.5),
            ), row=idx, col=1)
            fig.add_hline(y=70, line=dict(color=COLORS["red"], dash="dash", width=0.8), row=idx, col=1)
            fig.add_hline(y=30, line=dict(color=COLORS["green"], dash="dash", width=0.8), row=idx, col=1)
            fig.update_yaxes(title_text="RSI", row=idx, col=1)

        elif ind == "macd" and "macd" in df.columns:
            fig.add_trace(go.Scatter(x=df["date"], y=df["macd"], name="MACD",
                                     line=dict(color=COLORS["blue"], width=1.5)), row=idx, col=1)
            fig.add_trace(go.Scatter(x=df["date"], y=df["macd_signal"], name="Signal",
                                     line=dict(color=COLORS["accent"], width=1)), row=idx, col=1)
            hist_colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in df["macd_hist"]]
            fig.add_trace(go.Bar(x=df["date"], y=df["macd_hist"], name="Histogram",
                                 marker_color=hist_colors, opacity=0.6), row=idx, col=1)
            fig.update_yaxes(title_text="MACD", row=idx, col=1)

        elif ind == "stochastic" and "stoch_k" in df.columns:
            fig.add_trace(go.Scatter(x=df["date"], y=df["stoch_k"], name="%K",
                                     line=dict(color=COLORS["cyan"], width=1.5)), row=idx, col=1)
            fig.add_trace(go.Scatter(x=df["date"], y=df["stoch_d"], name="%D",
                                     line=dict(color=COLORS["accent"], width=1)), row=idx, col=1)
            fig.add_hline(y=80, line=dict(color=COLORS["red"], dash="dash", width=0.8), row=idx, col=1)
            fig.add_hline(y=20, line=dict(color=COLORS["green"], dash="dash", width=0.8), row=idx, col=1)
            fig.update_yaxes(title_text="Stochastic", row=idx, col=1)

    fig.update_xaxes(rangeslider_visible=False)
    return _apply_layout(fig, title, height)


# ============================================================
# PORTFOLIO PIE CHART
# ============================================================
def portfolio_pie_chart(positions: list[dict], title: str = "Phân bổ danh mục") -> go.Figure:
    """Biểu đồ tròn phân bổ danh mục."""
    labels = [p["symbol"] for p in positions]
    values = [p.get("market_value", 0) for p in positions]
    colors_palette = [COLORS["accent"], COLORS["green"], COLORS["blue"],
                      COLORS["purple"], COLORS["cyan"], COLORS["accent2"]]

    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values,
        hole=0.45,
        marker=dict(colors=colors_palette[:len(labels)],
                    line=dict(color=COLORS["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=12),
    )])

    return _apply_layout(fig, title, 400)


# ============================================================
# EFFICIENT FRONTIER (Markowitz)
# ============================================================
def efficient_frontier_chart(data: dict, title: str = "Efficient Frontier") -> go.Figure:
    """Biểu đồ đường biên hiệu quả."""
    fig = go.Figure()

    # All simulations
    fig.add_trace(go.Scatter(
        x=data["efficient_frontier"]["risks"],
        y=data["efficient_frontier"]["returns"],
        mode="markers",
        marker=dict(
            size=3, color=data["efficient_frontier"]["sharpes"],
            colorscale="Viridis", showscale=True,
            colorbar=dict(title="Sharpe"),
        ),
        name="Simulations", hoverinfo="skip",
    ))

    # Max Sharpe point
    fig.add_trace(go.Scatter(
        x=[data["max_sharpe"]["risk"]],
        y=[data["max_sharpe"]["return"]],
        mode="markers+text",
        marker=dict(size=15, color=COLORS["accent"], symbol="star"),
        text=["Max Sharpe"], textposition="top center",
        name=f"Max Sharpe ({data['max_sharpe']['sharpe']:.3f})",
    ))

    # Min Vol point
    fig.add_trace(go.Scatter(
        x=[data["min_volatility"]["risk"]],
        y=[data["min_volatility"]["return"]],
        mode="markers+text",
        marker=dict(size=15, color=COLORS["green"], symbol="diamond"),
        text=["Min Vol"], textposition="top center",
        name=f"Min Volatility",
    ))

    fig.update_xaxes(title_text="Risk (Volatility %)")
    fig.update_yaxes(title_text="Expected Return (%)")

    return _apply_layout(fig, title, 500)


# ============================================================
# HEATMAP
# ============================================================
def correlation_heatmap(df: pd.DataFrame, title: str = "Ma trận tương quan") -> go.Figure:
    """Heatmap tương quan giữa các cổ phiếu."""
    corr = df.corr()
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.index,
        colorscale="RdBu_r",
        zmid=0,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=10),
    ))
    return _apply_layout(fig, title, 500)


# ============================================================
# GAUGE (Speedometer)
# ============================================================
def signal_gauge(value: float, label: str = "Signal", title: str = "") -> go.Figure:
    """Đồng hồ đo tín hiệu (VD: RSI, Fear & Greed)."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title=dict(text=label, font=dict(size=14, color=COLORS["text"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=COLORS["muted"]),
            bar=dict(color=COLORS["accent"]),
            bgcolor=COLORS["card_bg"],
            bordercolor=COLORS["grid"],
            steps=[
                dict(range=[0, 30], color="rgba(0,200,83,0.2)"),
                dict(range=[30, 70], color="rgba(255,193,7,0.2)"),
                dict(range=[70, 100], color="rgba(255,23,68,0.2)"),
            ],
            threshold=dict(
                line=dict(color=COLORS["accent2"], width=3),
                thickness=0.8, value=value,
            ),
        ),
    ))
    return _apply_layout(fig, title, 300)
