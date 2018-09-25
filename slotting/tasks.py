from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
from . import plots
from . import slot_profile as sp
from itertools import combinations
import numpy as np

@shared_task
def solve_problem(hs, invs, alpha, L, M):
    hs = np.array(hs)
    invs = np.array(invs)
    prob = sp.SlotHeights(hs, invs, alpha, L, M)
    result, fvals = prob.solve()
    x, N = result['heights'][0], result['quants'][0]
    script_graph1, div_graph1 = plots.graph_groups_inventory(x, N * M, hs, invs)
    script_graph2, div_graph2 = plots.graph_fvals(fvals)
    x = x.tolist()
    N = N.tolist()

    result = {
        'profile': (x, N),
        'script_graph1': script_graph1,
        'div_graph1': div_graph1,
        'script_graph2': script_graph2,
        'div_graph2': div_graph2,
    }

    return result
