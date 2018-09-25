from . import forms

import json
from django.shortcuts import render
from celery.result import AsyncResult
from django.http import HttpResponse
from . import tasks


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
        if form.is_valid():
            hs, invs, alpha, L, M = read_params(request, form)
            hs = hs.tolist()
            invs = invs.tolist()
            task = tasks.solve_problem.delay(hs, invs, alpha, L, M)
            return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')
        else:
            return HttpResponse(json.dumps({'task_id': None}), content_type='application/json')

    else:
        form = forms.SlotProfileDataForm()
        return render(request, 'slotting/tool_home.html', {'form': form})


def get_task_info(request):
    task_id = request.GET.get('task_id', None)
    if task_id is not None:
        task = AsyncResult(task_id)
        data = {
            'state': task.state,
            'result': task.result,
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponse('No job id given.')