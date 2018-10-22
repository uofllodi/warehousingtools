from . import forms

import json
from django.shortcuts import render
from celery.result import AsyncResult
from django.http import HttpResponse
from . import tasks
import boto3
from botocore.client import Config
from django.conf import settings
import numpy as np

def read_params(request, form):
    alpha = form.cleaned_data['alpha']
    L = form.cleaned_data['L']
    b = form.cleaned_data['b']
    hs = form.cleaned_data['hsurl'] + b
    invs = form.cleaned_data['invsurl']
    ind = np.argsort(hs)
    hs = hs[ind]
    invs = invs[ind, :]
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
            msn = form.errors.as_json()
            return HttpResponse(json.dumps({'task_id': None, 'errors': json.loads(msn)}), content_type='application/json')

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



def sign_s3(request):

    file_name = request.GET.get('filename', None)
    file_type = request.GET.get('filetype', None)

    if (file_name is not None) and (file_type is not None):

        # Load necessary information into the application
        S3_BUCKET = settings.AWS_STORAGE_BUCKET_NAME

        # Initialise the S3 client
        s3 = boto3.client('s3', 'us-east-2',
            #aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            #aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
        )

        presigned_post = s3.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=file_name,
            Fields={"acl": "public-read", "Content-Type": file_type},
            Conditions=[
                {"acl": "public-read"},
                {"Content-Type": file_type}
            ],
            ExpiresIn=3600
        )

        url = 'https://{}.s3.amazonaws.com/{}'.format(S3_BUCKET, file_name)
        data = {'presigned': presigned_post, 'url': url}

        # Return the data to the client
        return HttpResponse(json.dumps(data), content_type='application/json')

    else:
        return HttpResponse('No job id given.')


