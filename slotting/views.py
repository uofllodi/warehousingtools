from django.shortcuts import get_object_or_404, render
from . import forms


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
        return render(request, 'slotting/tool_home.html', {'form': form, 'submitted': False})


