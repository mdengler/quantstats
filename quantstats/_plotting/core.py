# Quantreturns: Portfolio analytics for quants
# https://github.com/ranaroussi/quantreturns
#
# Copyright 2019-2024 Ran Aroussi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# try:
# _plt.rcParams["font.family"] = "Arial"
# except Exception:
#    pass
import matplotlib.dates as _mdates
import matplotlib.pyplot as _plt
import numpy as _np
import pandas as _pd
import plotly.graph_objects as go
import seaborn as _sns
from matplotlib.ticker import (
    FormatStrFormatter as _FormatStrFormatter,
)
from matplotlib.ticker import (
    FuncFormatter as _FuncFormatter,
)

from .. import (
    stats as _stats,
)
from ..data import build_data

_sns.set_theme(
    font_scale=1.1,
    rc={
        "figure.figsize": (10, 6),
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "grid.color": "#dddddd",
        "grid.linewidth": 0.5,
        "lines.linewidth": 1.5,
        "text.color": "#333333",
        "xtick.color": "#666666",
        "ytick.color": "#666666",
    },
)

_FLATUI_COLORS = [
    "#FEDD78",
    "#348DC1",
    "#BA516B",
    "#4FA487",
    "#9B59B6",
    "#613F66",
    "#84B082",
    "#DC136C",
    "#559CAD",
    "#4A5899",
]

_default_fontname = "sans-serif"


def _get_colors():
    colors = _FLATUI_COLORS
    ls = "-"
    alpha = 0.8
    return colors, ls, alpha


def plot_returns_bars(
    returns,
    benchmark=None,
    returns_label="Strategy",
    hline=None,
    hlw=None,
    hlcolor="red",
    hllabel="",
    resample="YE",
    title="Returns",
    match_volatility=False,
    log_scale=False,
    figsize=(10, 6),
    fontname=_default_fontname,
    ylabel=True,
    subtitle=True,
    savefig=None,
    show=True,
):
    d = build_data(returns=returns, benchmark=benchmark)

    if match_volatility and benchmark is None:
        raise ValueError("match_volatility requires passing of benchmark.")
    if match_volatility and benchmark is not None:
        bmark_vol = d.benchmark.std()
        returns = (d.returns / d.returns.std()) * bmark_vol

    # ---------------
    colors, _, _ = _get_colors()
    df = d.all()

    df = df.dropna()
    if resample is not None:
        df = df.resample(resample).apply(_stats.comp).resample(resample).last()
    # ---------------

    fig, ax = _plt.subplots(figsize=figsize)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # use a more precise date string for the x axis locations in the toolbar
    fig.suptitle(title, y=0.94, fontweight="bold", fontname=fontname, fontsize=14, color="black")

    if subtitle:
        ax.set_title(
            "%s - %s           \n"
            % (
                df.index.date[:1][0].strftime("%Y"),
                df.index.date[-1:][0].strftime("%Y"),
            ),
            fontsize=12,
            color="gray",
        )

    if benchmark is None:
        colors = colors[1:]
    df.plot(kind="bar", ax=ax, color=colors)

    fig.set_facecolor("white")
    ax.set_facecolor("white")

    try:
        ax.set_xticklabels(df.index.year)
        years = sorted(list(set(df.index.year)))
    except AttributeError:
        ax.set_xticklabels(df.index)
        years = sorted(list(set(df.index)))

    # ax.fmt_xdata = _mdates.DateFormatter('%Y-%m-%d')
    # years = sorted(list(set(df.index.year)))
    if len(years) > 10:
        mod = int(len(years) / 10)
        _plt.xticks(
            _np.arange(len(years)),
            [str(year) if not i % mod else "" for i, year in enumerate(years)],
        )

    # rotate and align the tick labels so they look better
    fig.autofmt_xdate()

    if hline is not None:
        if not isinstance(hline, _pd.Series):
            ax.axhline(hline, ls="--", lw=hlw, color=hlcolor, label=hllabel, zorder=2)

    ax.axhline(0, ls="--", lw=1, color="#000000", zorder=2)

    # if isinstance(benchmark, _pd.Series) or hline:
    ax.legend(fontsize=11)

    _plt.yscale("symlog" if log_scale else "linear")

    ax.set_xlabel("")
    if ylabel:
        ax.set_ylabel("Returns", fontname=fontname, fontweight="bold", fontsize=12, color="black")
        ax.yaxis.set_label_coords(-0.1, 0.5)

    ax.yaxis.set_major_formatter(_FuncFormatter(format_pct_axis))

    if benchmark is None and len(_pd.DataFrame(returns).columns) == 1:
        ax.get_legend().remove()

    _plt.subplots_adjust(hspace=0, bottom=0, top=1)
    fig.tight_layout()

    return save(fig, savefig=savefig, show=show)


def plot_timeseries(
    returns,
    benchmark=None,
    title="Returns",
    compound=False,
    cumulative=True,
    hline=None,
    hlw=1,
    hlcolor="red",
    hllabel="",
    percent=True,
    match_volatility=False,
    log_scale=False,
    lw=1.5,
    ylabel="",
    fontname=_default_fontname,
    subtitle=True,
    savefig=None,
    show=True,
):
    colors, ls, alpha = _get_colors()
    d = build_data(returns, benchmark=benchmark)

    d.returns.fillna(0, inplace=True)
    if isinstance(d.benchmark, _pd.Series):
        d.benchmark.fillna(0, inplace=True)

    if match_volatility and d.benchmark is None:
        raise ValueError("match_volatility requires a benchmark.")

    if match_volatility and d.benchmark is not None:
        bmark_vol = d.benchmark.std()
        d.returns = (d.returns / d.returns.std()) * bmark_vol

    # Handle compounding
    if compound:
        if cumulative:
            returns = _stats.compsum(d.returns)
            if isinstance(d.benchmark, _pd.Series):
                benchmark = _stats.compsum(d.benchmark)
        else:
            returns = d.returns.cumsum()
            if isinstance(d.benchmark, _pd.Series):
                benchmark = d.benchmark.cumsum()
    else:
        returns = d.returns

    # Combine returns and benchmark into one DataFrame
    x = returns.to_frame() if isinstance(returns, _pd.Series) else returns.copy()
    if benchmark is not None:
        if isinstance(benchmark, _pd.Series):
            x["Benchmark"] = benchmark

    fig = go.Figure()

    # Plot each series
    for i, col in enumerate(x.columns):
        fig.add_trace(
            go.Scatter(
                x=x.index,
                y=x[col],
                mode="lines",
                name=col,
                line=dict(color=colors[i + 1], width=lw),
                opacity=alpha,
                hovertemplate=f"<b>{col}</b><br>%{{y:.2%}}<extra></extra>"
                if percent
                else f"<b>{col}</b><br>%{{y:.2f}}<extra></extra>",
            )
        )

    # Add horizontal lines
    if hline is not None:
        if isinstance(hline, _pd.Series):
            fig.add_trace(
                go.Scatter(
                    x=hline.index,
                    y=hline.values,
                    mode="lines",
                    name=hllabel,
                    line=dict(color=hlcolor, width=hlw, dash="dash"),
                )
            )
        else:
            fig.add_hline(
                y=hline,
                line_dash="dash",
                line_color=hlcolor,
                line_width=hlw,
                annotation_text=hllabel,
                annotation_position="top left",
                annotation_font_size=12,
            )

    # Always add 0-line
    fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1)

    # Layout polish
    date_range = f"{d.index.min():%d %b '%y} - {d.index.max():%d %b '%y}"

    fig.update_layout(
        title={
            "text": f"<b>{title}</b><br><sub>{date_range}</sub>" if subtitle else f"<b>{title}</b>",
            "y": 0.93,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        font=dict(family=fontname, size=14),
        yaxis_title=ylabel if ylabel else None,
        yaxis_tickformat=".0%" if percent else None,
        yaxis_type="log" if log_scale else "linear",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=12)),
        hovermode="x unified",
        margin=dict(l=30, r=30, t=60, b=30),
    )

    # Softer gridlines
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor="lightgray", zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor="lightgray", zeroline=False)

    # Save if needed
    if savefig:
        if savefig.endswith(".html"):
            fig.write_html(savefig)
        elif savefig.endswith(".png"):
            fig.write_image(savefig)
        else:
            raise ValueError("savefig must end with '.html' or '.png'")

    if show:
        fig.show()

    return fig


def plot_histogram(
    returns,
    benchmark,
    resample="ME",
    bins=20,
    fontname=_default_fontname,
    title="Returns",
    kde=True,
    figsize=(10, 6),
    subtitle=True,
    compounded=True,
    savefig=None,
    show=True,
):
    colors, _, _ = _get_colors()

    apply_fnc = _stats.comp if compounded else _np.sum
    if benchmark is not None:
        benchmark = benchmark.fillna(0).resample(resample).apply(apply_fnc).resample(resample).last()

    returns = returns.fillna(0).resample(resample).apply(apply_fnc).resample(resample).last()

    figsize = (0.995 * figsize[0], figsize[1])
    fig, ax = _plt.subplots(figsize=figsize)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    fig.suptitle(title, y=0.94, fontweight="bold", fontname=fontname, fontsize=14, color="black")

    if subtitle:
        ax.set_title(
            "%s - %s           \n"
            % (
                returns.index.date[:1][0].strftime("%Y"),
                returns.index.date[-1:][0].strftime("%Y"),
            ),
            fontsize=12,
            color="gray",
        )

    fig.set_facecolor("white")
    ax.set_facecolor("white")

    if isinstance(returns, _pd.DataFrame) and len(returns.columns) == 1:
        returns = returns[returns.columns[0]]

    pallete = colors[1:2] if benchmark is None else colors[:2]
    alpha = 0.7
    if isinstance(returns, _pd.DataFrame):
        pallete = colors[1 : len(returns.columns) + 1] if benchmark is None else colors[: len(returns.columns) + 1]
        if len(returns.columns) > 1:
            alpha = 0.5

    if benchmark is not None:
        if isinstance(returns, _pd.Series):
            combined_returns = (
                benchmark.to_frame()
                .join(returns.to_frame())
                .stack()
                .reset_index()
                .rename(columns={"level_1": "", 0: "Returns"})
            )
        elif isinstance(returns, _pd.DataFrame):
            combined_returns = (
                benchmark.to_frame().join(returns).stack().reset_index().rename(columns={"level_1": "", 0: "Returns"})
            )
        _sns.histplot(
            data=combined_returns,
            x="Returns",
            bins=bins,
            alpha=alpha,
            kde=kde,
            stat="density",
            hue="",
            palette=pallete,
            ax=ax,
        )

    else:
        if isinstance(returns, _pd.Series):
            combined_returns = returns.copy()
            if kde:
                _sns.kdeplot(data=combined_returns, color="black", ax=ax)
            _sns.histplot(
                data=combined_returns,
                bins=bins,
                alpha=alpha,
                kde=False,
                stat="density",
                color=colors[1],
                ax=ax,
            )

        elif isinstance(returns, _pd.DataFrame):
            combined_returns = returns.stack().reset_index().rename(columns={"level_1": "", 0: "Returns"})
            _sns.histplot(
                data=combined_returns,
                x="Returns",
                bins=bins,
                alpha=alpha,
                kde=kde,
                stat="density",
                hue="",
                palette=pallete,
                ax=ax,
            )

    # Why do we need average?
    if isinstance(combined_returns, _pd.Series) or len(combined_returns.columns) == 1:
        ax.axvline(
            combined_returns.mean(),
            ls="--",
            lw=1.5,
            zorder=2,
            label="Average",
            color="red",
        )

    # _plt.setp(x.get_legend().get_texts(), fontsize=11)
    ax.xaxis.set_major_formatter(_plt.FuncFormatter(lambda x, loc: f"{int(x * 100):,}%"))

    # Removed static lines for clarity
    # ax.axhline(0.01, lw=1, color="#000000", zorder=2)
    # ax.axvline(0, lw=1, color="#000000", zorder=2)

    ax.set_xlabel("")
    ax.set_ylabel("Occurrences", fontname=fontname, fontweight="bold", fontsize=12, color="black")
    ax.yaxis.set_label_coords(-0.1, 0.5)

    # fig.autofmt_xdate()

    _plt.subplots_adjust(hspace=0, bottom=0, top=1)
    fig.tight_layout()

    return save(fig, savefig=savefig, show=show)


def plot_rolling_stats(
    returns,
    benchmark=None,
    title="",
    returns_label="Strategy",
    hline=None,
    hlw=None,
    hlcolor="red",
    hllabel="",
    lw=1.5,
    figsize=(10, 6),
    ylabel="",
    fontname=_default_fontname,
    subtitle=True,
    savefig=None,
    show=True,
):
    colors, _, _ = _get_colors()

    fig, ax = _plt.subplots(figsize=figsize)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    if isinstance(returns, _pd.DataFrame):
        returns_label = list(returns.columns)

    if isinstance(returns, _pd.Series):
        df = _pd.DataFrame(index=returns.index, data={returns_label: returns})
    elif isinstance(returns, _pd.DataFrame):
        df = _pd.DataFrame(index=returns.index, data={col: returns[col] for col in returns.columns})
    if isinstance(benchmark, _pd.Series):
        df["Benchmark"] = benchmark[benchmark.index.isin(returns.index)]
        if isinstance(returns, _pd.Series):
            df = df[["Benchmark", returns_label]].dropna()
            ax.plot(df[returns_label].dropna(), lw=lw, label=returns.name, color=colors[1])
        elif isinstance(returns, _pd.DataFrame):
            col_names = ["Benchmark", returns_label]
            df = df[list(_pd.core.common.flatten(col_names))].dropna()
            for i, col in enumerate(returns_label):
                ax.plot(df[col], lw=lw, label=col, color=colors[i + 1])
        ax.plot(df["Benchmark"], lw=lw, label=benchmark.name, color=colors[0], alpha=0.8)
    else:
        if isinstance(returns, _pd.Series):
            df = df[[returns_label]].dropna()
            ax.plot(df[returns_label].dropna(), lw=lw, label=returns.name, color=colors[1])
        elif isinstance(returns, _pd.DataFrame):
            df = df[returns_label].dropna()
            for i, col in enumerate(returns_label):
                ax.plot(df[col], lw=lw, label=col, color=colors[i + 1])

    # rotate and align the tick labels so they look better
    fig.autofmt_xdate()

    # use a more precise date string for the x axis locations in the toolbar
    # ax.fmt_xdata = _mdates.DateFormatter('%Y-%m-%d')\
    fig.suptitle(title, y=0.94, fontweight="bold", fontname=fontname, fontsize=14, color="black")

    if subtitle:
        ax.set_title(
            "%s - %s           \n"
            % (
                df.index.date[:1][0].strftime("%e %b '%y"),
                df.index.date[-1:][0].strftime("%e %b '%y"),
            ),
            fontsize=12,
            color="gray",
        )

    if hline is not None:
        if not isinstance(hline, _pd.Series):
            ax.axhline(hline, ls="--", lw=hlw, color=hlcolor, label=hllabel, zorder=2)

    ax.axhline(0, ls="--", lw=1, color="#000000", zorder=2)

    if ylabel:
        ax.set_ylabel(ylabel, fontname=fontname, fontweight="bold", fontsize=12, color="black")
        ax.yaxis.set_label_coords(-0.1, 0.5)

    ax.yaxis.set_major_formatter(_FormatStrFormatter("%.2f"))

    ax.legend(fontsize=11)

    if benchmark is None and len(_pd.DataFrame(returns).columns) == 1:
        ax.get_legend().remove()

    _plt.subplots_adjust(hspace=0, bottom=0, top=1)
    fig.tight_layout()

    return save(fig, savefig=savefig, show=show)


def plot_rolling_beta(
    returns,
    benchmark,
    window1=126,
    window1_label="",
    window2=None,
    window2_label="",
    title="",
    hlcolor="red",
    figsize=(10, 6),
    fontname=_default_fontname,
    lw=1.5,
    ylabel=True,
    subtitle=True,
    savefig=None,
    show=True,
):
    colors, _, _ = _get_colors()

    fig, ax = _plt.subplots(figsize=figsize)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    fig.suptitle(title, y=0.94, fontweight="bold", fontname=fontname, fontsize=14, color="black")

    if subtitle:
        ax.set_title(
            "%s - %s           \n"
            % (
                returns.index.date[:1][0].strftime("%e %b '%y"),
                returns.index.date[-1:][0].strftime("%e %b '%y"),
            ),
            fontsize=12,
            color="gray",
        )

    i = 1
    if isinstance(returns, _pd.Series):
        beta = _stats.rolling_greeks(returns, benchmark, window1)["beta"].fillna(0)
        ax.plot(beta, lw=lw, label=window1_label, color=colors[1])
    elif isinstance(returns, _pd.DataFrame):
        beta = {
            col: _stats.rolling_greeks(returns[col], benchmark, window1)["beta"].fillna(0) for col in returns.columns
        }
        for name, b in beta.items():
            ax.plot(b, lw=lw, label=name + " " + f"({window1_label})", color=colors[i])
            i += 1

    i = 1
    if window2:
        lw = lw - 0.5
        if isinstance(returns, _pd.Series):
            ax.plot(
                _stats.rolling_greeks(returns, benchmark, window2)["beta"],
                lw=lw,
                label=window2_label,
                color="gray",
                alpha=0.8,
            )
        elif isinstance(returns, _pd.DataFrame):
            betas_w2 = {col: _stats.rolling_greeks(returns[col], benchmark, window2)["beta"] for col in returns.columns}
            for name, beta_w2 in betas_w2.items():
                ax.plot(
                    beta_w2,
                    lw=lw,
                    ls="--",
                    label=name + " " + f"({window2_label})",
                    alpha=0.5,
                    color=colors[i],
                )
                i += 1

    beta_min = beta.min() if isinstance(returns, _pd.Series) else min([b.min() for b in beta.values()])
    beta_max = beta.max() if isinstance(returns, _pd.Series) else max([b.max() for b in beta.values()])
    mmin = min([-100, int(beta_min * 100)])
    mmax = max([100, int(beta_max * 100)])
    step = 50 if (mmax - mmin) >= 200 else 100
    ax.set_yticks([x / 100 for x in list(range(mmin, mmax, step))])

    if isinstance(returns, _pd.Series):
        ax.axhline(beta.mean(), ls="--", lw=1.5, color=hlcolor, zorder=2)

    ax.axhline(0, ls="--", lw=1, color="#000000", zorder=2)

    fig.autofmt_xdate()

    # use a more precise date string for the x axis locations in the toolbar
    ax.fmt_xdata = _mdates.DateFormatter("%Y-%m-%d")

    if ylabel:
        ax.set_ylabel("Beta", fontname=fontname, fontweight="bold", fontsize=12, color="black")
        ax.yaxis.set_label_coords(-0.1, 0.5)

    ax.legend(fontsize=11)
    if benchmark is None and len(_pd.DataFrame(returns).columns) == 1:
        ax.get_legend().remove()

    _plt.subplots_adjust(hspace=0, bottom=0, top=1)
    fig.tight_layout()

    return save(fig, savefig=savefig, show=show)


def plot_longest_drawdowns(
    returns,
    periods=5,
    lw=1.5,
    fontname=_default_fontname,
    title=None,
    log_scale=False,
    figsize=(10, 6),
    ylabel=True,
    subtitle=True,
    compounded=True,
    savefig=None,
    show=True,
):
    colors = ["#348dc1", "#003366", "red"]

    dd = _stats.to_drawdown_series(returns.fillna(0))
    dddf = _stats.drawdown_details(dd)
    longest_dd = dddf.sort_values(by="days", ascending=False, kind="mergesort")[:periods]

    fig, ax = _plt.subplots(figsize=figsize)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    fig.suptitle(
        f"{title} - Worst %.0f Drawdown Periods" % periods,
        y=0.94,
        fontweight="bold",
        fontname=fontname,
        fontsize=14,
        color="black",
    )
    if subtitle:
        ax.set_title(
            "%s - %s           \n"
            % (
                returns.index.date[:1][0].strftime("%e %b '%y"),
                returns.index.date[-1:][0].strftime("%e %b '%y"),
            ),
            fontsize=12,
            color="gray",
        )

    fig.set_facecolor("white")
    ax.set_facecolor("white")
    series = _stats.compsum(returns) if compounded else returns.cumsum()
    ax.plot(series, lw=lw, label="Backtest", color=colors[0])

    highlight = "red"
    for _, row in longest_dd.iterrows():
        ax.axvspan(
            *_mdates.datestr2num([str(row["start"]), str(row["end"])]),
            color=highlight,
            alpha=0.1,
        )

    # rotate and align the tick labels so they look better
    fig.autofmt_xdate()

    # use a more precise date string for the x axis locations in the toolbar
    ax.fmt_xdata = _mdates.DateFormatter("%Y-%m-%d")

    ax.axhline(0, ls="--", lw=1, color="#000000", zorder=2)
    _plt.yscale("symlog" if log_scale else "linear")
    if ylabel:
        ax.set_ylabel(
            "Cumulative Returns",
            fontname=fontname,
            fontweight="bold",
            fontsize=12,
            color="black",
        )
        ax.yaxis.set_label_coords(-0.1, 0.5)

    ax.yaxis.set_major_formatter(_FuncFormatter(format_pct_axis))
    # ax.yaxis.set_major_formatter(_plt.FuncFormatter(
    #     lambda x, loc: "{:,}%".format(int(x*100))))

    fig.autofmt_xdate()

    _plt.subplots_adjust(hspace=0, bottom=0, top=1)
    fig.tight_layout()

    return save(fig, savefig=savefig, show=show)


def plot_distribution(
    returns,
    fontname=_default_fontname,
    compounded=True,
    title=None,
    savefig=None,
    show=True,
):
    colors = _FLATUI_COLORS  # your color palette

    # Ensure DataFrame and fill missing values
    port = _pd.DataFrame(returns.fillna(0))
    port.columns = ["Daily"]

    apply_fnc = _stats.comp if compounded else _np.sum

    # Resample returns
    port["Weekly"] = port["Daily"].resample("W-MON").apply(apply_fnc).ffill()
    port["Monthly"] = port["Daily"].resample("ME").apply(apply_fnc).ffill()
    port["Quarterly"] = port["Daily"].resample("QE").apply(apply_fnc).ffill()
    port["Yearly"] = port["Daily"].resample("YE").apply(apply_fnc).ffill()

    # Create box plots for each frequency
    fig = go.Figure()

    for i, col in enumerate(["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]):
        fig.add_trace(
            go.Box(
                y=port[col],
                name=col,
                marker_color=colors[i],
                boxmean="sd",  # show mean and std
            )
        )

    # Title and layout
    if not title:
        title = "Return Quantiles"
    else:
        title = f"{title} - Return Quantiles"

    date_range = f"{returns.index.min():%d %b '%y} - {returns.index.max():%d %b '%y}"

    fig.update_layout(
        title={
            "text": f"<b>{title}</b><br><sub>{date_range}</sub>",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        font=dict(family=fontname, size=14),
        yaxis_title="Returns (%)",
        yaxis_tickformat=".0%",
        boxmode="group",
        plot_bgcolor="white",
    )

    # Save if path is given
    if savefig:
        if savefig.endswith(".html"):
            fig.write_html(savefig)
        elif savefig.endswith(".png"):
            fig.write_image(savefig)
        else:
            raise ValueError("savefig must end with '.html' or '.png'")

    if show:
        fig.show()

    return fig


# def plot_table(
#     tbl,
#     columns=None,
#     title="",
#     title_loc="left",
#     header=True,
#     colWidths=None,
#     rowLoc="right",
#     colLoc="right",
#     colLabels=None,
#     edges="horizontal",
#     orient="horizontal",
#     figsize=(5.5, 6),
#     savefig=None,
#     show=False,
# ):
#     if columns is not None:
#         try:
#             tbl.columns = columns
#         except Exception:
#             pass
#
#     fig = _plt.figure(figsize=figsize)
#     ax = _plt.subplot(111, frame_on=False)
#
#     if title != "":
#         ax.set_title(title, fontweight="bold", fontsize=14, color="black", loc=title_loc)
#
#     the_table = ax.table(
#         cellText=tbl.values,
#         colWidths=colWidths,
#         rowLoc=rowLoc,
#         colLoc=colLoc,
#         edges=edges,
#         colLabels=(tbl.columns if header else colLabels),
#         loc="center",
#         zorder=2,
#     )
#
#     the_table.auto_set_font_size(False)
#     the_table.set_fontsize(12)
#     the_table.scale(1, 1)
#
#     for (row, col), cell in the_table.get_celld().items():
#         cell.set_height(0.08)
#         cell.set_text_props(color="black")
#         cell.set_edgecolor("#dddddd")
#         if row == 0 and header:
#             cell.set_edgecolor("black")
#             cell.set_facecolor("black")
#             cell.set_linewidth(2)
#             cell.set_text_props(weight="bold", color="black")
#         elif col == 0 and "vertical" in orient:
#             cell.set_edgecolor("#dddddd")
#             cell.set_linewidth(1)
#             cell.set_text_props(weight="bold", color="black")
#         elif row > 1:
#             cell.set_linewidth(1)
#
#     ax.grid(False)
#     ax.set_xticks([])
#     ax.set_yticks([])
#
#     try:
#         _plt.subplots_adjust(hspace=0)
#     except Exception:
#         pass
#     try:
#         fig.tight_layout(w_pad=0, h_pad=0)
#     except Exception:
#         pass
#
#     if savefig:
#         if isinstance(savefig, dict):
#             _plt.savefig(**savefig)
#         else:
#             _plt.savefig(savefig)
#
#     if show:
#         _plt.show(block=False)
#
#     _plt.close()
#
#     if not show:
#         return fig
#
#     return None


def save(fig, savefig, show=True):
    if savefig:
        if isinstance(savefig, dict):
            _plt.savefig(**savefig)
        else:
            _plt.savefig(savefig)

    if show:
        _plt.show(block=False)

    _plt.close()

    if not show:
        return fig

    return None


def format_cur_axis(x, _):
    if x >= 1e12:
        res = "$%1.1fT" % (x * 1e-12)
        return res.replace(".0T", "T")
    if x >= 1e9:
        res = "$%1.1fB" % (x * 1e-9)
        return res.replace(".0B", "B")
    if x >= 1e6:
        res = "$%1.1fM" % (x * 1e-6)
        return res.replace(".0M", "ME")
    if x >= 1e3:
        res = "$%1.0fK" % (x * 1e-3)
        return res.replace(".0K", "K")
    res = "$%1.0f" % x
    return res.replace(".0", "")


def format_pct_axis(x, _):
    x *= 100  # lambda x, loc: "{:,}%".format(int(x * 100))
    if x >= 1e12:
        res = "%1.1fT%%" % (x * 1e-12)
        return res.replace(".0T%", "T%")
    if x >= 1e9:
        res = "%1.1fB%%" % (x * 1e-9)
        return res.replace(".0B%", "B%")
    if x >= 1e6:
        res = "%1.1fM%%" % (x * 1e-6)
        return res.replace(".0M%", "M%")
    if x >= 1e3:
        res = "%1.1fK%%" % (x * 1e-3)
        return res.replace(".0K%", "K%")
    res = "%1.0f%%" % x
    return res.replace(".0%", "%")
