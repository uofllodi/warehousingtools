
import numpy as np
from . import aux_funcs as af
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.palettes import Spectral11
from bokeh.plotting import figure
from bokeh.models import Label
from bokeh.models.tickers import FixedTicker

def graph_groups_inventory(x, N, hs, invs):

    invs_T = af.group_inventory_signals(x, hs, invs)
    Ns = np.cumsum(N[::-1])
    n, dates = invs_T.shape
    #format fig
    p = figure(plot_width=700, plot_height=400, y_range=[0, int(np.max(invs_T)*1.1)],
               x_axis_label='Time', y_axis_label='Number of Pallets',
               )
    p.xaxis.axis_label_text_font_size = "12pt"
    p.yaxis.axis_label_text_font_size = "12pt"
    p.xaxis.major_label_text_font_size = "11pt"
    p.yaxis.major_label_text_font_size = "11pt"
    p.xaxis.axis_label_text_font = "helvetica"
    p.yaxis.axis_label_text_font = "helvetica"
    p.xaxis.axis_label_text_font_style = "normal"
    p.yaxis.axis_label_text_font_style = "normal"
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    my_palette = Spectral11[0:n]

    xs_single = np.arange(dates)
    xs = [xs_single] * n
    ys = invs_T.tolist()

    #plot timeseries
    p.multi_line(xs, ys, line_color=my_palette, line_width=2)

    #plot slot quantities
    p.multi_line([[0, dates]]*n, [[k] * n for k in Ns], line_color=['red']*n, line_width=1, line_dash="dashed")

    #include the annotations
    x_end = int(dates*0.95)
    SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    for i in range(n):
        t = "x" + str(n-i)
        text = Label(x=x_end, y=Ns[i], text=t.translate(SUB), render_mode='css',
                     background_fill_color='white', background_fill_alpha=0, text_font_style='italic',
                 text_font='Times', text_font_size='13pt')
        p.add_layout(text)

    script, div = components(p, CDN)
    return script, div


def graph_fvals(fvals):
    fvals = np.asarray(fvals)
    percentages = np.round(np.divide(-np.diff(fvals), fvals[1:]) * 100, 1).tolist()

    p = figure(plot_width=600, plot_height=400, y_range=[0,int(np.max(fvals)*1.2)], x_range=[0, fvals.shape[0]+1],
               x_axis_label='Number of slot types', y_axis_label='Sum of height of all slots',
               )
    p.xaxis.axis_label_text_font_size = "12pt"
    p.yaxis.axis_label_text_font_size = "12pt"
    p.xaxis.major_label_text_font_size = "11pt"
    p.yaxis.major_label_text_font_size = "11pt"
    p.xaxis.axis_label_text_font = "helvetica"
    p.yaxis.axis_label_text_font = "helvetica"
    p.xaxis.major_label_text_font = "helvetica"
    p.yaxis.major_label_text_font = "helvetica"
    p.xaxis.axis_label_text_font_style = "normal"
    p.yaxis.axis_label_text_font_style = "normal"
    p.ygrid.grid_line_dash = [6, 4]
    p.xgrid.grid_line_dash = [6, 4]

    xs = np.arange(1,fvals.shape[0]+1)
    p.circle(xs, fvals)
    p.line(xs, fvals, line_dash="4 4", line_width=1, line_alpha=0.4)
    p.xaxis.ticker = FixedTicker(ticks=xs)

    for i, perc in enumerate(percentages):
        t = str(perc)+'%'
        text = Label(x=xs[i+1], y=fvals[i+1], text=t, render_mode='css',
                     background_fill_color='white', background_fill_alpha=0, text_font='Times', text_font_size='13pt')
        p.add_layout(text)

    script, div = components(p, CDN)
    return script, div