from django.shortcuts import get_object_or_404, render
from . import forms
from . import plots
import numpy as np
from . import slot_profile as sp


def read_params(request, form):
    alpha = form.cleaned_data['alpha']
    L = form.cleaned_data['L']
    b = form.cleaned_data['b']
    hs = form.cleaned_data['hs'] +  b
    invs = form.cleaned_data['invs']
    M = form.cleaned_data['M']
    return hs, invs, alpha, L, M


# Create your views here.
def tool_home(request):

    if request.method == 'POST':
        form = forms.SlotProfileDataForm(request.POST, request.FILES)
        test_info = str("")
        if form.is_valid():
            hs, invs, alpha, L, M = read_params(request, form)
            prob = sp.SlotHeights(hs, invs, alpha, L, M)
            result, fvals = prob.solve()
            x, N = result['heights'][0], result['quants'][0]
            script_graph1, div_graph1 = plots.graph_groups_inventory(x, N*M, hs, invs)
            script_graph2, div_graph2 = plots.graph_fvals(fvals)

            test_info = ""

            info = {
                'form': form,
                'submitted': True,
                'profile': zip(x, N),
                'L': L,
                'div_graph1': div_graph1,
                'script_graph1': script_graph1,
                'div_graph2': div_graph2,
                'script_graph2': script_graph2,
                'test_info': test_info,
             }
        else:
            info = {
                'form': form,
                'submitted': False,
                'test_info': test_info,
             }

        return render(request, 'slotting/tool_home.html', info)



    else:
        form = forms.SlotProfileDataForm()
        return render(request, 'slotting/tool_home.html', {'form': form, 'submitted': False})


