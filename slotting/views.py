from django.shortcuts import get_object_or_404, render
from . import forms
from . import aux_funcs as af
import numpy as np

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
            rho, mus, sigmas = af.calc_mvn_params([50, 80], hs, invs)
            serv = af.calc_serv(rho, mus, sigmas, [70, 480])
            test_info =(rho, mus, sigmas, serv)

            info = {
                'form': form,
                'submitted': False,
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
        return render(request, 'slotting/tool_home.html', {'form': form, 'submitted': False, 'test_info': ""})


