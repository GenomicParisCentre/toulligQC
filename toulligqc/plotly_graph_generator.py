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
# First author: Lionel Ferrato-Berberian
# Maintainer: Karine Dias
# Since version 0.1

# Class for generating Plotly and MPL graphs and statistics tables in HTML format, they use the result_dict or dataframe_dict dictionnaries.

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import seaborn as sns
from scipy.stats import norm

from toulligqc.plotly_graph_common import _create_and_save_div
from toulligqc.plotly_graph_common import _dataFrame_to_html
from toulligqc.plotly_graph_common import _interpolate
from toulligqc.plotly_graph_common import _make_describe_dataframe
from toulligqc.plotly_graph_common import _precompute_boxplot_values
from toulligqc.plotly_graph_common import _smooth_data
from toulligqc.plotly_graph_common import _transparent_colors
from toulligqc.plotly_graph_common import axis_font_size
from toulligqc.plotly_graph_common import figure_image_height
from toulligqc.plotly_graph_common import figure_image_width
from toulligqc.plotly_graph_common import float_format_str
from toulligqc.plotly_graph_common import graph_font
from toulligqc.plotly_graph_common import image_dpi
from toulligqc.plotly_graph_common import int_format_str
from toulligqc.plotly_graph_common import interpolation_threshold
from toulligqc.plotly_graph_common import legend_font_size
from toulligqc.plotly_graph_common import line_width
from toulligqc.plotly_graph_common import on_chart_font_size
from toulligqc.plotly_graph_common import percent_format_str
from toulligqc.plotly_graph_common import plotly_background_color
from toulligqc.plotly_graph_common import title_size
from toulligqc.plotly_graph_common import toulligqc_colors
from toulligqc.plotly_graph_common import _over_time_graph
from toulligqc.plotly_graph_common import _barcode_boxplot_graph
from toulligqc.plotly_graph_common import _pie_chart_graph
from toulligqc.plotly_graph_common import _read_length_distribution
from toulligqc.plotly_graph_common import _phred_score_density

#
#  1D plots
#


def read_count_histogram(result_dict, dataframe_dict, result_directory):
    """
    Plots the histogram of count of the different types of reads:
    1D read return by Guppy
    1D pass read return by Guppy (Qscore >= 7)
    1D fail read return by Guppy (Qscore < 7)
    """

    graph_name = 'Read count histogram'

    # Histogram with barcoded read counts
    if 'read.pass.barcoded.count' in dataframe_dict:

        data = {
            'All reads': result_dict['basecaller.sequencing.summary.1d.extractor.read.count'],
            'Pass reads': result_dict["basecaller.sequencing.summary.1d.extractor.read.pass.count"],
            'Fail reads': result_dict["basecaller.sequencing.summary.1d.extractor.read.fail.count"],
            'Pass barcoded reads': dataframe_dict["read.pass.barcoded.count"],
            'Fail barcoded reads': dataframe_dict["read.fail.barcoded.count"]
        }

        colors = [toulligqc_colors["all"], toulligqc_colors["pass"], toulligqc_colors["fail"],
                  toulligqc_colors["barcode_pass"], toulligqc_colors["barcode_fail"]]

        trace = go.Bar(x=[*data], y=list(data.values()),
                       hovertext=["<b>All reads</b>",
                                  "<b>Pass reads</b>",
                                  "<b>Fail reads</b>",
                                  "<b>Pass barcoded reads</b>",
                                  "<b>Fail barcoded reads</b>"],
                       name="Barcoded graph",
                       marker_color=_transparent_colors(colors, plotly_background_color, .5),
                       marker_line_color=colors,
                       marker_line_width=line_width)

        # Array of data for HTML table with barcode reads
        array = np.array(
            # count
            [[result_dict["basecaller.sequencing.summary.1d.extractor.read.count"],
              result_dict["basecaller.sequencing.summary.1d.extractor.read.pass.count"],
              result_dict["basecaller.sequencing.summary.1d.extractor.read.fail.count"],
              dataframe_dict["read.pass.barcoded.count"],
              dataframe_dict["read.fail.barcoded.count"]],
             # frequencies
             [result_dict["basecaller.sequencing.summary.1d.extractor.read.count.frequency"],
              result_dict["basecaller.sequencing.summary.1d.extractor.read.pass.frequency"],
              result_dict["basecaller.sequencing.summary.1d.extractor.read.fail.frequency"],
              result_dict["basecaller.sequencing.summary.1d.extractor.read.pass.barcoded.frequency"],
              result_dict["basecaller.sequencing.summary.1d.extractor.read.fail.barcoded.frequency"]]])

        dataframe = pd.DataFrame(array, index=['count', 'frequency'],
                                 columns=["All reads", "Pass reads", "Fail reads", "Pass barcoded reads",
                                          "Fail barcoded reads"])

    # Histogram without barcodes
    else:

        data = {
            'All reads': result_dict['basecaller.sequencing.summary.1d.extractor.read.count'],
            'Pass reads': result_dict["basecaller.sequencing.summary.1d.extractor.read.pass.count"],
            'Fail reads': result_dict["basecaller.sequencing.summary.1d.extractor.read.fail.count"]
        }

        colors = [toulligqc_colors['all'], toulligqc_colors['pass'], toulligqc_colors['fail']]

        trace = go.Bar(x=[*data], y=list(data.values()),
                       hovertext=["<b>All reads</b>",
                                  "<b>Pass reads</b>",
                                  "<b>Fail reads</b>"],
                       name="Barcoded graph",
                       marker_color=_transparent_colors(colors, plotly_background_color, .5),
                       marker_line_color=colors,
                       marker_line_width=line_width)

        # Array of data for HTML table without barcode reads
        array = np.array([[result_dict["basecaller.sequencing.summary.1d.extractor.read.count"],
                           result_dict["basecaller.sequencing.summary.1d.extractor.read.pass.count"],
                           result_dict["basecaller.sequencing.summary.1d.extractor.read.fail.count"]],
                          # frequencies
                          [result_dict["basecaller.sequencing.summary.1d.extractor.read.count.frequency"],
                           result_dict["basecaller.sequencing.summary.1d.extractor.read.pass.frequency"],
                           result_dict["basecaller.sequencing.summary.1d.extractor.read.fail.frequency"]]])

        # Create dataframe with array data
        dataframe = pd.DataFrame(array, index=['count', 'frequency'],
                                 columns=["All reads", "Pass reads", "Fail reads"])

    layout = go.Layout(
        hovermode="x",
        title={
            'text': "<b>" + graph_name + "</b>",
            'y': 0.95,
            'x': 0,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': dict(
                size=title_size,
                color="black")
        },
        xaxis=dict(title="<b>Read type</b>",
                   fixedrange=True,
                   titlefont=dict(
                       size=axis_font_size,
                       color="black",
                   ),
                   categoryorder="total descending"
                   ),
        yaxis=dict(title="<b>Counts</b>",
                   fixedrange=True,
                   titlefont=dict(
                       size=axis_font_size,
                       color="black",
                   )),
        font=dict(family=graph_font),
        width=figure_image_width,
        height=figure_image_height)

    fig = go.Figure(data=trace, layout=layout)

    # HTML table
    dataframe.iloc[0] = dataframe.iloc[0].astype(int).apply(lambda x: int_format_str.format(x))
    dataframe.iloc[1:] = dataframe.iloc[1:].applymap(float_format_str.format)
    table_html = _dataFrame_to_html(dataframe)

    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def read_length_scatterplot(dataframe_dict, sequence_length_df, result_directory):
    graph_name = "Distribution of read lengths"

    all_read = sequence_length_df.loc[sequence_length_df >= 10].dropna().values
    read_pass = dataframe_dict['read.pass.length'].loc[dataframe_dict['read.pass.length'] >= 10]
    read_fail = dataframe_dict['read.fail.length'].loc[dataframe_dict['read.fail.length'] >= 10]

    return _read_length_distribution(graph_name=graph_name,
                                     all_read=all_read,
                                     read_pass=read_pass,
                                     read_fail=read_fail,
                                     all_color=toulligqc_colors['all'],
                                     pass_color=toulligqc_colors['pass'],
                                     fail_color=toulligqc_colors['fail'],
                                     xaxis_title='Read length (bp)',
                                     result_directory=result_directory)


def yield_plot(dataframe_dict, result_directory):
    """
    Plots the different reads (1D, 1D pass, 1D fail) produced along the run against the time(in hour)
    """

    graph_name = "Yield plot through time"

    all_read = dataframe_dict['start.time.sorted']
    read_pass = dataframe_dict['read.pass.sorted']
    read_fail = dataframe_dict['read.fail.sorted']

    count_x1, count_y1 = _smooth_data(10000, 5, all_read)
    count_x2, count_y2 = _smooth_data(10000, 5, read_pass)
    count_x3, count_y3 = _smooth_data(10000, 5, read_fail)

    fig = go.Figure()

    # Figures for cumulative yield plot
    fig.add_trace(go.Scatter(x=count_x1,
                             y=np.cumsum(count_y1),
                             name='All reads',
                             fill='tozeroy',
                             marker_color=toulligqc_colors['all'],
                             visible=True
                             ))

    fig.add_trace(go.Scatter(x=count_x2,
                             y=np.cumsum(count_y2),
                             name='Pass reads',
                             fill='tozeroy',
                             marker_color=toulligqc_colors['pass'],
                             visible=True
                             ))

    fig.add_trace(go.Scatter(x=count_x3,
                             y=np.cumsum(count_y3),
                             name='Fail reads',
                             fill='tozeroy',
                             marker_color=toulligqc_colors['fail'],
                             visible=True
                             ))

    # Threshold
    for p in [50, 75, 90, 99]:
        y = np.cumsum(count_y1)
        ymax = max(y)
        index = (np.abs(y-ymax*p/100)).argmin()
        x0 = count_x1[index]
        fig.add_trace(go.Scatter(
                      mode="lines+text",
                      name='All reads',
                      x=[x0, x0],
                      y=[0, ymax],
                      line=dict(color="gray", width=1, dash="dot"),
                      text=["", str(p) + "% all reads"],
                      textposition="top center",
                      hoverinfo="skip",
                      showlegend=False,
                      visible=True
                     ))

    # Yield
    fig.add_trace(go.Scatter(x=count_x1,
                             y=count_y1,
                             name='All reads',
                             marker_color=toulligqc_colors['all'],
                             fill='tozeroy',
                             visible=False
                             ))

    fig.add_trace(go.Scatter(x=count_x2,
                             y=count_y2,
                             name='Pass reads',
                             marker_color=toulligqc_colors['pass'],
                             fill='tozeroy',
                             visible=False
                             ))

    fig.add_trace(go.Scatter(x=count_x3,
                             y=count_y3,
                             name='Fail reads',
                             marker_color=toulligqc_colors['fail'],
                             fill='tozeroy',
                             visible=False
                             ))

    fig.update_layout(
        title={
            'text': "<b>" + graph_name + "</b>",
            'y': 0.95,
            'x': 0,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': dict(
                size=title_size,
                color="black")},
        xaxis=dict(
            title="<b>Time (hours)</b>",
            titlefont_size=axis_font_size,
            rangemode = "tozero"
        ),
        yaxis=dict(
            title='<b>Density</b>',
            titlefont_size=axis_font_size,
            tickfont_size=axis_font_size,
            rangemode="tozero"
        ),
        legend=dict(
            x=1.02,
            y=0.95,
            title_text="<b>Legend</b>",
            title=dict(font=dict(size=legend_font_size)),
            bgcolor='white',
            bordercolor='white',
            font=dict(size=legend_font_size)
        ),
        hovermode='x',
        font=dict(family=graph_font),
        height=figure_image_height,
        width=figure_image_width
    )

    # Add buttons

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{'visible': [True, True, True,
                                           True, True, True, True,
                                           False, False, False]}],
                        label="Cumulative yield plot",
                        method="update"
                    ),
                    dict(
                        args=[{'visible': [False, False, False,
                                           False, False, False, False,
                                           True, True, True]}],
                        label="Yield plot",
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
    table_html = None
    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def read_quality_multiboxplot(dataframe_dict, result_directory):
    """
    Boxplot of PHRED score between read pass and read fail
    Violin plot of PHRED score between read pass and read fail
    """

    graph_name = "PHRED score distribution"

    df = pd.DataFrame(
        {"1D": dataframe_dict['mean.qscore'],
         "1D pass": dataframe_dict['read.pass.qscore'],
         "1D fail": dataframe_dict['read.fail.qscore']
         })

    # If more than 10.000 reads, interpolate data
    if len(df["1D"]) > interpolation_threshold:
        dataframe = pd.DataFrame({
            "1D": _interpolate(df["1D"], 1000),
            "1D pass": _interpolate(df["1D pass"], 1000),
            "1D fail": _interpolate(df["1D fail"], 1000)
        })
    else:
        dataframe = df
    names = {"1D": "All reads",
             "1D pass": "Pass reads",
             "1D fail": "Fail reads"}

    colors = {"1D": toulligqc_colors['all'],
              "1D pass": toulligqc_colors['pass'],
              "1D fail": toulligqc_colors['fail']}

    # Max yaxis value for displaying same scale between plots
    max_yaxis = (dataframe.max(skipna=True, numeric_only=True).values.max() + 2.0)
    min_yaxis = (dataframe.min(skipna=True, numeric_only=True).values.min() - 2.0)

    fig = go.Figure()

    for column in dataframe.columns:
        d = _precompute_boxplot_values(dataframe[column])
        fig.add_trace(go.Box(
            q1=[d['q1']], median=[d['median']], q3=[d['q3']], lowerfence=[d['lowerfence']],
            upperfence=[d['upperfence']],
            name=names[column],
            x0=names[column],
            marker=dict(
                opacity=0.3,
                color=colors[column]

            ),
            boxmean=False,
            showlegend=True
        ))

        fig.add_trace(go.Violin(y=dataframe[column],
                                name=names[column],
                                meanline_visible=True,
                                marker=dict(color=colors[column]),
                                visible=False))

    fig.update_layout(
        title={
            'text': "<b>" + graph_name + "</b>",
            'y': 0.95,
            'x': 0,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': dict(
                size=title_size,
                color="black")},
        xaxis=dict(
            title="<b>Read type</b>",
            titlefont_size=axis_font_size,
            fixedrange=True
        ),
        yaxis=dict(
            title='<b>PHRED score</b>',
            titlefont_size=axis_font_size,
            tickfont_size=axis_font_size,
            range=[min_yaxis, max_yaxis],
            fixedrange=True
        ),
        legend=dict(
            x=1.02,
            y=0.95,
            title_text="<b>Legend</b>",
            title=dict(font=dict(size=legend_font_size)),
            bgcolor='white',
            bordercolor='white',
            font=dict(size=legend_font_size)
        ),
        hovermode='x',
        font=dict(family=graph_font),
        height=figure_image_height,
        width=figure_image_width
    )

    # Add buttons
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{'visible': [True, False]}],
                        label="Boxplot",
                        method="update"
                    ),
                    dict(
                        args=[{'visible': [False, True]}],
                        label="Violin plot",
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

    df = df[["1D", "1D pass", "1D fail"]]
    df.columns=["All reads", "Pass reads", "Fail reads"]
    table_html = _dataFrame_to_html(_make_describe_dataframe(df))

    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def allphred_score_frequency(dataframe_dict, result_directory):
    """
    Plot the distribution of the phred score per read type (1D , 1D pass, 1D fail)
    """

    graph_name = "PHRED score density distribution"

    dataframe = \
        pd.DataFrame({"1D": dataframe_dict['mean.qscore'],
                      "1D pass": dataframe_dict['read.pass.qscore'],
                      "1D fail": dataframe_dict['read.fail.qscore']})

    return _phred_score_density(graph_name=graph_name,
                                dataframe=dataframe,
                                prefix="1D",
                                all_color=toulligqc_colors['all'],
                                pass_color=toulligqc_colors['pass'],
                                fail_color=toulligqc_colors['fail'],
                                result_directory=result_directory)


def all_scatterplot(dataframe_dict, result_directory):
    """
    Plot the scatter plot representing the relation between the phred score and the sequence length in log
    """

    graph_name = "Correlation between read length and PHRED score"

    read_pass_length = dataframe_dict["read.pass.length"]
    read_pass_qscore = dataframe_dict["read.pass.qscore"]
    read_fail_length = dataframe_dict["read.fail.length"]
    read_fail_qscore = dataframe_dict["read.fail.qscore"]

    # If more than 10.000 reads, interpolate data
    if len(read_pass_length) > interpolation_threshold:
        pass_data = _interpolate(read_pass_length, 4000, y=read_pass_qscore, interp_type="nearest")
        fail_data = _interpolate(read_fail_length, 4000, y=read_fail_qscore, interp_type="nearest")
    else:
        pass_data = [read_pass_length, read_pass_qscore]
        fail_data = [read_fail_length, read_fail_qscore]
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=pass_data[0],
                             y=pass_data[1],
                             name="Pass reads",
                             marker_color=toulligqc_colors['pass'],
                             mode="markers"
                             ))

    fig.add_trace(go.Scatter(x=fail_data[0],
                             y=fail_data[1],
                             name="Fail reads",
                             marker_color=toulligqc_colors['fail'],
                             mode="markers"
                             ))

    fig.update_layout(
        title={
            'text': "<b>" + graph_name + "</b>",
            'y': 0.95,
            'x': 0,
            'xanchor': 'left',
            'yanchor': 'top',
            'font': dict(
                size=title_size,
                color="black")},
        xaxis=dict(
            title="<b>Sequence length (bp)</b>",
            titlefont_size=axis_font_size
        ),
        yaxis=dict(
            title='<b>PHRED score</b>',
            titlefont_size=axis_font_size,
            tickfont_size=axis_font_size,
        ),
        legend=dict(
            x=1.02,
            y=.5,
            title_text="<b>Read type</b>",
            title=dict(font=dict(size=legend_font_size)),
            bgcolor='white',
            bordercolor='white',
            font=dict(size=legend_font_size)
        ),
        font=dict(family=graph_font),
        height=figure_image_height,
        width=figure_image_width
    )
    # Trim x axis to avoid negative values
    if max(read_pass_length) >= max(read_fail_length):
        max_val = max(read_pass_length)
    max_val = max(read_fail_length)

    fig.update_xaxes(range=[0, max_val])

    table_html = None
    div, output_file = _create_and_save_div(fig, result_directory, graph_name)
    return graph_name, output_file, table_html, div


def _minion_flowcell_layout():
    """
    Represents the layout of a minion flowcell (not use anymore)
    """
    seeds = [125, 121, 117, 113, 109, 105, 101, 97,
             93, 89, 85, 81, 77, 73, 69, 65,
             61, 57, 53, 49, 45, 41, 37, 33,
             29, 25, 21, 17, 13, 9, 5, 1]

    flowcell_layout = []
    for s in seeds:
        for block in range(4):
            for row in range(4):
                flowcell_layout.append(s + 128 * block + row)
    return flowcell_layout


def plot_performance(pore_measure, result_directory):
    """
    Plots the channels occupancy by the reads
    @:param pore_measure: reads number per pore
    """

    graph_name = "Channel occupancy of the flowcell"

    output_file = result_directory + '/' + '_'.join(graph_name.split()) + '.png'
    flowcell_layout = _minion_flowcell_layout()

    pore_values = []
    for pore in flowcell_layout:
        if pore in pore_measure:
            pore_values.append(pore_measure[pore])
        else:
            pore_values.append(0)

    d = {'Row number': list(range(1, 17)) * 32,
         'Column number': sorted(list(range(1, 33)) * 16),
         'tot_reads': pore_values,
         'labels': flowcell_layout}

    df = pd.DataFrame(d)

    d = df.pivot("Row number", "Column number", "tot_reads")
    df.pivot("Row number", "Column number", "labels")
    plt.figure(figsize=(figure_image_width / image_dpi, figure_image_height / image_dpi), dpi=image_dpi)
    sns.heatmap(d, fmt="", linewidths=.5, cmap="YlGnBu", annot_kws={"size": 7},
                cbar_kws={'label': 'Read number per pore channel', "orientation": "horizontal"})

    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    table_html = None
    return graph_name, output_file, table_html


#
# For each barcode 1D
#


def barcode_percentage_pie_chart_pass(dataframe_dict, barcode_selection, result_directory):
    """
    Plots a pie chart of 1D read pass percentage per barcode of a run.
    """

    graph_name = "Pass barcoded reads distribution"

    for element in barcode_selection:

        if all(dataframe_dict['barcode.arrangement'] != element):
            print("The barcode {} doesn't exist".format(element))
            return False

    count_sorted = dataframe_dict["read.pass.barcoded"]

    return _pie_chart_graph(graph_name=graph_name,
                            count_sorted=count_sorted,
                            color_palette=toulligqc_colors['pie_chart_palette'],
                            one_d_square=False,
                            result_directory=result_directory)


def barcode_percentage_pie_chart_fail(dataframe_dict, barcode_selection, result_directory):
    """
    Plots a pie chart of 1D read fail percentage per barcode of a run.
    Needs the samplesheet file describing the barcodes to run
    """

    graph_name = "Fail barcoded reads distribution"

    for element in barcode_selection:

        if all(dataframe_dict['barcode.arrangement'] != element):
            print("The barcode {} doesn't exist".format(element))
            return False

    count_sorted = dataframe_dict["read.fail.barcoded"]

    return _pie_chart_graph(graph_name=graph_name,
                            count_sorted=count_sorted,
                            color_palette=toulligqc_colors['pie_chart_palette'],
                            one_d_square=False,
                            result_directory=result_directory)


def barcode_length_boxplot(datafame_dict, result_directory):
    """
    Boxplots all the 1D pass and fail read length for each barcode indicated in the sample sheet
    """

    graph_name = "Read size distribution for barcodes"

    df = datafame_dict['barcode_selection_sequence_length_dataframe']

    return _barcode_boxplot_graph(graph_name=graph_name,
                                  df=df,
                                  qscore=False,
                                  barcode_selection=df.columns.drop('passes_filtering'),
                                  pass_color=toulligqc_colors['pass'],
                                  fail_color=toulligqc_colors['fail'],
                                  yaxis_title="Sequence length (bp)",
                                  legend_title="Read type",
                                  result_directory=result_directory)


def barcoded_phred_score_frequency(barcode_selection, dataframe_dict, result_directory):
    """
    Plot boxplot of the 1D pass and fail read qscore for each barcode indicated in the sample sheet
    """

    graph_name = "PHRED score distribution for barcodes"

    df = dataframe_dict['barcode_selection_sequence_phred_melted_dataframe']

    return _barcode_boxplot_graph(graph_name=graph_name,
                                  df=df,
                                  qscore=True,
                                  barcode_selection=barcode_selection,
                                  pass_color=toulligqc_colors['pass'],
                                  fail_color=toulligqc_colors['fail'],
                                  yaxis_title="PHRED score",
                                  legend_title="Read type",
                                  result_directory=result_directory)


def sequence_length_over_time(time_df, dataframe_dict, result_directory):
    graph_name = "Read length over time"

    return _over_time_graph(data_series=dataframe_dict.get('sequence.length'),
                            time_series=time_df,
                            result_directory=result_directory,
                            graph_name=graph_name,
                            color=toulligqc_colors['sequence_length_over_time'],
                            yaxis_title='Read length (bp)',
                            log=False)


def phred_score_over_time(qscore_df, time_df, result_directory):
    graph_name = "PHRED score over time"

    return _over_time_graph(data_series=qscore_df,
                            time_series=time_df,
                            result_directory=result_directory,
                            graph_name=graph_name,
                            color=toulligqc_colors['phred_score_over_time'],
                            yaxis_title='PHRED quality score',
                            log=False)


def speed_over_time(duration_df, sequence_length_df, time_df, result_directory):
    graph_name = "Speed over time"

    speed = pd.Series(sequence_length_df / duration_df)

    return _over_time_graph(data_series=speed,
                            time_series=time_df,
                            result_directory=result_directory,
                            graph_name=graph_name,
                            color=toulligqc_colors['speed_over_time'],
                            yaxis_title='Speed (bases per second)',
                            log=True)

