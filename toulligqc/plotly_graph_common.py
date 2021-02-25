# -*- coding: utf-8 -*-

#                  ToulligQC development code
#
# This code may be freely distributed and modified under the
# terms of the GNU General Public License version 3 or later
# and CeCILL. This should be distributed with the code. If you
# do not have a copy, see:
#
#      http://www.gnu.org/licenses/gpl-3.0-standalone.html
#      http://www.cecill.info/licences/Licence_CeCILL_V2-en.html
#
# Copyright for this code is held jointly by the Genomic platform
# of the Institut de Biologie de l'École Normale Supérieure and
# the individual authors.
#
# First author: Lionel Ferrato-Berberian, Karine Dias, Laurent Jourdren
# Maintainer: Karine Dias
# Since version 2.0

# This module contains common methods for plotly modules.

import numpy as np
import pandas as pd
import plotly.offline as py
from scipy.interpolate import interp1d
from scipy.ndimage.filters import gaussian_filter1d
from sklearn.utils import resample
import plotly.graph_objs as go
from scipy.stats import norm
from collections import defaultdict

figure_image_width = 1000
figure_image_height = 562
percent_format_str = '{:.2f}%'
line_width = 2
interpolation_threshold = 10000

toulligqc_colors = {'all': '#fca311',  # Yellow
                    'all_1d2': '#fca311',  # Yellow
                    'pass': '#51a96d',  # Green
                    'fail': '#d90429',  # Red
                    'barcode_pass': '#51a96d',  # Green
                    'barcode_fail': '#d90429',  # Red
                    'sequence_length_over_time': '#205b47',
                    'phred_score_over_time': '#7aaceb',
                    'speed_over_time': '#AE3F7B',
                    'nseq_over_time': '#edb773',
                    'pie_chart_palette': ["#f3a683", "#f7d794", "#778beb", "#e77f67", "#cf6a87", "#786fa6", "#f8a5c2",
                                          "#63cdda", "#ea8685", "#596275"],
                    'green_zone_color': 'rgba(0,100,0,.1)'
                    }

plotly_background_color = '#e5ecf6'
legend_font_size = 16
axis_title_font_size = 14
axis_font_size = 12
on_chart_font_size = 15
title_size = 24
graph_font = 'Helvetica, Arial, sans-serif'
image_dpi = 100
default_graph_layout = dict(
    font=dict(family=graph_font),
    height=figure_image_height,
    width=figure_image_width
)

def _format_int(i):
    return '{:,d}'.format(i)

def _format_float(f):

    s = str(f)
    i = int(s.split('.')[0])
    f = float('0.' + s.split('.')[1])

    return '{:,d}'.format(i) + '{:.2f}'.format(f)[1:]

def _format_percent(f):
    return percent_format_str.format(f)


def _title(title):
    return dict(title=dict(
        text="<b>" + title + "</b>",
        y=0.95,
        x=0,
        xanchor='left',
        yanchor='top',
        font=dict(
        size=title_size,
        color="black")))


def _legend(legend_title='Legend'):
    return dict(legend=dict(
        x=1.02,
        #y=.5,
        y=.95,
        title_text="<b>" + legend_title + "</b>",
        title=dict(font=dict(size=legend_font_size)),
        bgcolor='white',
        bordercolor='white',
        font=dict(size=legend_font_size)))


def _xaxis(title, args=None):

    axis_dict = dict(
        title='<b>' + title + '</b>',
        titlefont_size=axis_title_font_size,
        tickfont_size=axis_font_size)

    if args is not None:
        axis_dict.update(dict(**args))

    return dict(xaxis=axis_dict)


def _yaxis(title, args=None):

    axis_dict = dict(
        title='<b>' + title + '</b>',
        titlefont_size=axis_title_font_size,
        tickfont_size=axis_font_size,
        fixedrange=True)

    if args is not None:
        axis_dict.update(dict(**args))

    return dict(yaxis=axis_dict)


def _make_describe_dataframe(value):
    """
    Creation of a statistics table printed with the graph in report.html
    :param value: information measured (series)
    """

    desc = value.describe()
    desc.loc['count'] = desc.loc['count'].astype(int).apply(lambda x: _format_int(x))
    desc.iloc[1:] = desc.iloc[1:].applymap(lambda x: _format_float(x))
    desc.rename({'50%': 'median'}, axis='index', inplace=True)

    return desc


def _interpolate(x, npoints: int, y=None, interp_type=None, axis=-1):
    """
    Function returning an interpolated version of data passed as input
    :param x: array of data
    :param npoints: number of desired points after interpolation (int)
    :param y: second array in case of 2D data
    :param interp_type: string specifying the type of interpolation (i.e. linear, nearest, cubic, quadratic etc.)
    :param axis: number specifying the axis of y along which to interpolate. Default = -1
    """
    # In case of single array of data, use
    if y is None:
        return np.sort(resample(x, n_samples=npoints, random_state=1))

    else:
        f = interp1d(x, y, kind=interp_type, axis=axis)
        x_int = np.linspace(min(x), max(x), npoints)
        y_int = f(x_int)
        return pd.Series(x_int), pd.Series(y_int)


def _smooth_data(npoints: int, sigma: int, data, min_arg=None, max_arg=None):
    """
    Function for smmothing data with numpy histogram function
    Returns a tuple of smooth data (ndarray)
    :param data: must be array-like data
    :param npoints: number of desired points for smoothing
    :param sigma: sigma value of the gaussian filter
    """

    if min_arg is None:
        min_arg = np.nanmin(data)

    if max_arg is None:
        max_arg = np.nanmax(data)

    bins = np.linspace(min_arg, max_arg, num=npoints)
    count_y, count_x = np.histogram(a=data, bins=bins, density=True)
    # Removes the first value of count_x1
    count_x = count_x[1:]
    count_y = gaussian_filter1d(count_y * len(data), sigma=sigma)
    return count_x, count_y


def _precompute_boxplot_values(y):
    """
    Precompute values for boxplot to avoid data storage in boxplot.
    https://github.com/plotly/plotly.js/blob/master/src/traces/box/calc.js
    """

    y = y.dropna()

    if len(y) == 0:
        return dict(min=0,
                    lowerfence=0,
                    q1=0,
                    median=0,
                    q3=0,
                    upperfence=0,
                    max=0,
                    notchspan=0)

    q1 = y.quantile(.25)
    q3 = y.quantile(.75)
    iqr = q3 - q1
    upper_fence = q3 + (1.5 * iqr)
    lower_fence = q1 - (1.5 * iqr)
    import math
    notchspan = 1.57 * iqr / math.sqrt(len(y))

    return dict(min=min(y),
                lowerfence=max(lower_fence, float(min(y))),
                q1=q1,
                median=y.quantile(.5),
                q3=q3,
                upperfence=min(upper_fence, float(max(y))),
                max=max(y),
                notchspan=notchspan)


def _dataFrame_to_html(df):
    return pd.DataFrame.to_html(df, border="")


def _transparent_colors(colors, background_color, a):
    result = []

    br = int(background_color[1:3], 16)
    bg = int(background_color[3:5], 16)
    bb = int(background_color[5:7], 16)

    for c in colors:
        r = int(c[1:3], 16)
        g = int(c[3:5], 16)
        b = int(c[5:7], 16)
        new_c = '#' + \
                _transparent_component(r, br, a) + \
                _transparent_component(g, bg, a) + \
                _transparent_component(b, bb, a)
        result.append(new_c)

    return result


def _transparent_component(c, b, a):
    v = (1 - a) * c + a * b
    r = hex(int(v))[2:]

    if len(r) == 1:
        return '0' + r
    return r


def _create_and_save_div(fig, result_directory, main):
    output_file = result_directory + '/' + '_'.join(main.split())

    div = py.plot(fig,
                  include_plotlyjs=False,
                  output_type='div',
                  auto_open=False,
                  show_link=False)
    py.plot(fig,
            filename=output_file,
            output_type="file",
            include_plotlyjs="directory",
            auto_open=False)

    return div, output_file


def _over_time_graph(data_series,
                     time_series,
                     result_directory,
                     graph_name,
                     color,
                     yaxis_title,
                     log=False,
                     time_bins=1000,
                     sigma=1,
                     quartiles=True,
                     min_max=False,
                     yaxis_starts_zero=False,
                     green_zone_starts_at=None,
                     green_zone_color='rgba(0,100,0,.1)'):

    t = (time_series/3600).values
    x = np.linspace(t.min(), t.max(), num=time_bins)
    t = np.digitize(t, bins=x, right=True)

    bin_dict = defaultdict(list)
    for bin_idx, val in zip(t, data_series):
        b = x[bin_idx]
        bin_dict[b].append(val)

    percentiles = (0, 25, 50, 75, 100)
    y = []
    for i in range(len(percentiles)):
        y.append([])

    for b in x:
        if b in bin_dict:
            for i, v in enumerate(percentiles):
                y[i].append(np.percentile(bin_dict[b], v))
        else:
            for i in range(len(percentiles)):
                y[i].append(np.nan)

    for i, v in enumerate(y):
        y[i] = gaussian_filter1d(v, sigma=sigma)

    fig = go.Figure()

    # define the green zone if required
    if green_zone_starts_at is not None:
        min_x = min(time_series)/3600
        max_x = max(time_series)/3600
        if min_max:
            max_y = max(y[4]) * 1.05
        else:
            max_y = max(y[3]) * 1.05
        fig.add_trace(go.Scatter(
            mode="lines",
            x=[min_x, max_x],
            y=[max_y, max_y],
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            mode="lines",
            name="Median target",
            x=[min_x, max_x],
            y=[green_zone_starts_at, green_zone_starts_at],
            fill='tonexty',
            fillcolor=green_zone_color,
            line=dict(width=0),
            hoverinfo="skip",
        ))

    if quartiles:
        fig.add_trace(go.Scatter(
            x=x,
            y=y[1],
            name="25% quartile",
            mode='lines',
            fill="none",
            line=dict(color=color,
                      width=line_width,
                      shape="spline")))

        fig.add_trace(go.Scatter(
            x=x,
            y=y[3],
            name="75% quartile",
            mode='lines',
            fill="tonexty",
            line=dict(color=color,
                      width=line_width,
                      shape="spline")))

        fig.add_trace(go.Scatter(
            x=x,
            y=y[2],
            name="Median",
            mode='lines',
            line=dict(color="black",
                      width=line_width,
                      shape="spline")))
        if min_max:
            fig.add_trace(go.Scatter(
                x=x,
                y=y[0],
                name="Min",
                mode='lines',
                line=dict(color="black",
                          width=int(line_width/2),
                          shape="spline")))
            fig.add_trace(go.Scatter(
                x=x,
                y=y[4],
                name="Max",
                mode='lines',
                line=dict(color="black",
                          width=int(line_width/2),
                          shape="spline")))

    else:
        # No quartile lines, only median
        fig.add_trace(go.Scatter(
            x=x,
            y=y[2],
            name="Median",
            mode='lines',
            fill='tozeroy',
            line=dict(color=color,
                      width=line_width,
                      shape="spline")))

    # set minimal value of y axis to 0 is required
    if yaxis_starts_zero:
        range_mode = 'tozero'
    else:
        range_mode = 'normal'

    fig.update_layout(
        **_title(graph_name),
        **_legend(),
        **default_graph_layout,
        hovermode='x',
        **_xaxis('Experiment time (hours)'),
        **_yaxis(yaxis_title, dict(rangemode=range_mode)),
    )

    if log:
        fig.update_yaxes(type="log")

    table_html = None
    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def _barcode_boxplot_graph(graph_name, df, qscore, barcode_selection, pass_color, fail_color, yaxis_title, legend_title, result_directory):

    # Sort reads by read type and drop read type column
    pass_df = df.loc[df['passes_filtering'] == bool(True)].drop(columns='passes_filtering')
    fail_df = df.loc[df['passes_filtering'] == bool(False)].drop(columns='passes_filtering')

    fig = go.Figure()

    for read_type in ('Pass', 'Fail'):

        if read_type == 'Pass':
            df = pass_df
            color = pass_color
        else:
            df = fail_df
            color = fail_color

        first = True
        for barcode in sorted(barcode_selection):

            if qscore:
                final_df = df.loc[df['barcodes'] == barcode].dropna()
                d = _precompute_boxplot_values(final_df['qscore'])
            else:
                df[barcode] = df[barcode].loc[df[barcode] > 0]
                d = _precompute_boxplot_values(df[barcode])
            fig.add_trace(go.Box(
                q1=[d['q1']],
                median=[d['median']],
                q3=[d['q3']],
                lowerfence=[d['lowerfence']],
                upperfence=[d['upperfence']],
                name=read_type + " reads",
                x0=barcode,
                marker_color=color,
                offsetgroup=read_type.lower(),
                showlegend=first
            ))
            if first:
                first = False

    fig.update_layout(
        **_title(graph_name),
        **_legend(legend_title),
        **default_graph_layout,
        **_xaxis('Barcodes', dict(fixedrange=True)),
        **_yaxis(yaxis_title, dict(rangemode="tozero")),
        boxmode='group',
        boxgap=0.4,
        boxgroupgap=0,
    )

    # all_read = all_df.describe().T
    # read_pass = pass_df.describe().T
    # read_fail = fail_df.describe().T
    # concat = pd.concat([all_read, read_pass, read_fail],
    #                    keys=['1D', '1D pass', '1D fail'])
    # dataframe = concat.T
    #
    # dataframe.loc['count'] = dataframe.loc['count'].astype(int).apply(lambda x: int_format_str.format(x))
    # dataframe.iloc[1:] = dataframe.iloc[1:].applymap(float_format_str.format)
    # table_html = _dataFrame_to_html(dataframe)

    table_html = None
    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def _pie_chart_graph(graph_name, count_sorted, color_palette, one_d_square, result_directory):
    labels = count_sorted.index.values.tolist()

    fig = go.Figure()

    if len(labels) <= len(color_palette):
        pie_marker = dict(colors=color_palette, line=dict(width=line_width, color='#808080'))
        bar_colors = color_palette
    else:
        pie_marker = dict(line=dict(width=line_width, color='#808080'))
        bar_colors = color_palette[0]

    # Pie chart
    fig.add_trace(go.Pie(labels=labels,
                         values=count_sorted,
                         hoverinfo='label+percent',
                         textinfo='percent',
                         textfont_size=14,
                         marker=pie_marker,
                         textposition='inside',
                         hovertemplate='<b>%{label}</b><br>%{percent:.1%} (%{value:,})<extra></extra>',
                         visible=True
                         ))
    # Histogram
    fig.add_trace(go.Bar(x=labels,
                         y=count_sorted,
                         marker_color=bar_colors,
                         marker_line_color='gray',
                         marker_line_width=line_width,
                         hovertemplate='<b>%{x}</b><br>%{y:,}<extra></extra>',
                         visible=False
                         ))

    # Layout
    fig.update_layout(
        **_title(graph_name),
        **default_graph_layout,
        **_legend('Barcodes'),
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        xaxis={'visible': False},
        yaxis={'visible': False},
        plot_bgcolor='white',
    )

    # Add buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{'visible': [True, False]},
                              {'xaxis': {'visible': False},
                               'yaxis': {'visible': False},
                               'plot_bgcolor': 'white'}],
                        label="Pie chart",
                        method="update"
                    ),
                    dict(
                        args=[{'visible': [False, True]},
                              {**_xaxis('Barcodes', dict(visible=True)),
                               **_yaxis('Read count', dict(visible=True)),
                               'plot_bgcolor': plotly_background_color}],
                        label="Histogram",
                        method="update"
                    )
                ]),
                pad={"r": 20, "t": 20, "l": 20, "b": 20},
                showactive=True,
                x=1.0,
                xanchor="left",
                y=1.25,
                yanchor="top"
            ),
        ]
    )

    if one_d_square:
        count_col_name = '1D² read count'
    else:
        count_col_name = 'Read count'

    barcode_table = pd.DataFrame({"Barcode arrangement (%)": count_sorted / sum(count_sorted) * 100,
                                  count_col_name: count_sorted})
    barcode_table.sort_index(inplace=True)
    pd.options.display.float_format = percent_format_str.format
    barcode_table[count_col_name] = barcode_table[count_col_name].astype(int).apply(lambda x: _format_int(x))
    table_html = _dataFrame_to_html(barcode_table)

    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def _read_length_distribution(graph_name, all_read, read_pass, read_fail, all_color, pass_color, fail_color,
                              xaxis_title, result_directory):

    count_x1, count_y1 = _smooth_data(10000, 5, all_read)
    count_x2, count_y2 = _smooth_data(10000, 5, read_pass)
    count_x3, count_y3 = _smooth_data(10000, 5, read_fail)

    # Find 50 percentile for zoomed range on x axis
    max_x_range = np.percentile(all_read, 99)
    max_y = max(max(count_y1), max(count_y2), max(count_y3))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=count_x1,
                             y=count_y1,
                             name='All reads',
                             fill='tozeroy',
                             marker_color=all_color
                             ))
    fig.add_trace(go.Scatter(x=count_x2,
                             y=count_y2,
                             name='Pass reads',
                             fill='tozeroy',
                             marker_color=pass_color
                             ))
    fig.add_trace(go.Scatter(x=count_x3,
                             y=count_y3,
                             name='Fail reads',
                             fill='tozeroy',
                             marker_color=fail_color
                             ))

    # Threshold
    for p in [25, 50, 75]:
        x0 = np.percentile(all_read, p)
        if p == 50:
            t = 'median<br>all reads'
        else:
            t = str(p) + "%<br>all reads"
        fig.add_trace(go.Scatter(
                      mode="lines+text",
                      name='All reads',
                      x=[x0, x0],
                      y=[0, max_y],
                      line=dict(color="gray", width=1, dash="dot"),
                      text=["", t],
                      textposition="top center",
                      hoverinfo="skip",
                      showlegend=False,
                      visible=True
                     ))

    fig.update_layout(
        **_title(graph_name),
        **default_graph_layout,
        **_legend(),
        hovermode='x',
        **_xaxis(xaxis_title, dict(range=[0, max_x_range])),
        **_yaxis('Density', dict(range=[0, max(count_y1) * 1.10])),
    )

    # Create data for HTML table
    table_df = pd.concat([pd.Series(all_read), read_pass, read_fail], axis=1,
                         keys=['All reads', 'Pass reads', 'Fail reads'])
    table_html = _dataFrame_to_html(_make_describe_dataframe(table_df))

    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def _phred_score_density(graph_name, dataframe, prefix,  all_color, pass_color, fail_color, result_directory):

    all_series = dataframe[prefix].dropna()
    pass_series = dataframe[prefix + " pass"].dropna()
    fail_series = dataframe[prefix + " fail"].dropna()

    count_x2, count_y2 = _smooth_data(10000, 5, pass_series, min_arg=np.nanmin(all_series), max_arg=np.nanmax(all_series))
    count_x3, count_y3 = _smooth_data(10000, 5, fail_series, min_arg=np.nanmin(all_series), max_arg=np.nanmax(all_series))

    count_y2 = count_y2 / len(all_series)
    count_y3 = count_y3 / len(all_series)

    max_y = max(max(count_y2), max(count_y3))

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=count_x2,
                             y=count_y2,
                             name='Pass reads',
                             fill='tozeroy',
                             marker_color=pass_color,
                             visible=True
                             ))
    fig.add_trace(go.Scatter(x=count_x3,
                             y=count_y3,
                             name='Fail reads',
                             fill='tozeroy',
                             marker_color=fail_color,
                             visible=True
                             ))

    # Threshold
    for p in [25, 50, 75]:
        x0 = np.percentile(pass_series, p)
        if p == 50:
            t = 'median'
        else:
            t = str(p) + "%"
        fig.add_trace(go.Scatter(
            mode="lines+text",
            name='Pass read<br>percentiles',
            x=[x0, x0],
            y=[0, max_y],
            line=dict(color="gray", width=1, dash="dot"),
            text=["", t],
            textposition="top center",
            hoverinfo="skip",
            showlegend=(True if p == 50 else False),
            visible=True
        ))

    fig.update_layout(
        **_title(graph_name),
        **_legend(),
        **default_graph_layout,
        hovermode='x',
        **_xaxis('PHRED score', dict(rangemode="tozero")),
        **_yaxis('Density probability', dict(rangemode="tozero")),
    )

    table_html = None
    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div

