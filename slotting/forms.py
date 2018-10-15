from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import numpy as np
from django.utils.safestring import mark_safe
import certifi
import urllib3
from botocore.client import Config
import boto3
from django.conf import settings


def read_array(urlname, dim):
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())

    r = http.request('GET', urlname)
    csvfile = r.data.decode('utf-8')

    if dim == 1:
        rel = csvfile.splitlines()
        if len(rel) == 1:
            rel = csvfile.split(',')
    elif dim == 2:
        lines = csvfile.splitlines()
        rel = []
        for line in lines:
            rel.append(line.split(','))

    rel = np.array(rel, dtype=np.float)

    return rel


def delete_file(urlname):
    # delete file
    try:
        s3 = boto3.client('s3', 'us-east-2', config=Config(signature_version='s3v4'))
        S3_BUCKET = settings.AWS_STORAGE_BUCKET_NAME
        s3.delete_object(Bucket=S3_BUCKET, Key=urlname.split('/')[-1])
    except:
        print("Boto3 connection failing")


class SlotProfileDataForm(forms.Form):
    L = forms.IntegerField(min_value=2, max_value=4, label='Number of slot types', initial=3 )
    nskus = forms.IntegerField(min_value=10, max_value=1000, label='Number of skus', initial=100)
    alpha = forms.DecimalField(min_value=50, max_value=99.99999, label='Desired Storage Service Level (%)', initial=97.5)
    b = forms.DecimalField(min_value=0, label='Vertical clearance within slot (inches)', initial=10)
    M = forms.IntegerField(min_value=1, label= 'Pallet positions per slot', initial=2)
    hs = forms.FileField(label = mark_safe("Pallet height of each sku (inches) <i class='fa fa-question-circle' aria-hidden='true' title='Upload a csv file with one column and as many rows as skus, " +
                                           "such that the pallet height for SKU 1 is the cell on the first row of the column, the pallet height for SKU 2 is the cell on the second row of the column. " +
                                           "Do not include labels'></i>"),
                         help_text = mark_safe("Download an <a href='/static/files/hs.csv'> example </a> with 100 skus"),
                         widget=forms.FileInput(attrs={'accept': ".csv"}), required=False) #validators = [validators.validate_hs])
    invs = forms.FileField(label= mark_safe("Inventory level of each sku <i class='fa fa-question-circle' aria-hidden='true' title='Upload a csv file with as" +
                                            " many rows as skus and as many columns as time-periods, such that the number of pallets of SKU 3 at period 5 is the cell on the third row and fifth column. " +
                                            " Do not include labels. Include at least 100 time-periods for a good analysis.'></i>"),
                           help_text= mark_safe("Download an <a href='/static/files/invs.csv'> example </a> with 100 skus"),
                           widget=forms.FileInput(attrs={'accept': ".csv"}), required=False)
    hsurl = forms.CharField(widget=forms.HiddenInput(), required=False)
    invsurl = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_L(self):
        return int(self.cleaned_data.get("L"))

    def clean_nskus(self):
        return int(self.cleaned_data.get("nskus"))

    def clean_alpha(self):
        return float(self.cleaned_data.get("alpha")) / 100

    def clean_b(self):
        return float(self.cleaned_data.get("b"))

    def clean_M(self):
        return int(self.cleaned_data.get("M"))

    def clean_hsurl(self):
        urlname = self.cleaned_data.get("hsurl")

        if urlname:
            try:
                hs = read_array(urlname, 1)
            except:
                raise ValidationError(
                    _(' The pallet heights file could not be read as an array of numbers'),
                )

            delete_file(urlname)

            nskus = int(self.cleaned_data.get("nskus"))

            if len(hs.shape) > 1:
                raise ValidationError(
                    _('The pallet heights file must be a one-dimensional array'),
                )
            elif hs.shape[0] != nskus:
                raise ValidationError(
                    _('There are {} pallet height, but {} skus'.format(str(hs.shape[0]), str(nskus))),
                )

            if np.min(hs) < 0:
                raise ValidationError(
                    _('There are negative pallet heights'),
                )

            if np.isnan(np.sum(hs)):
                raise ValidationError(
                    _('The pallet heights file have non-numeric characters'),
                )

        else:
            raise ValidationError(
                _(' Upload pallet heights file'),
            )

        return hs

    def clean_invsurl(self):
        urlname = self.cleaned_data.get("invsurl")

        if urlname:
            try:
                invs = read_array(urlname, 2)
            except:
                raise ValidationError(
                    _('The inventory levels file could not be read as an 2D array of numbers'),
                )

            delete_file(urlname)
            nskus = int(self.cleaned_data.get("nskus"))

            if len(invs.shape) != 2:
                raise ValidationError(
                    _('The inventory levels file must be a 2D array'),
                )
            elif invs.shape[0] != nskus:
                raise ValidationError(
                    _('There are {} rows of inventory levels, but {} skus'.format(str(invs.shape[0]), str(nskus))),
                )

            if np.min(invs) < 0:
                raise ValidationError(
                    _('There are negative inventory levels'),
                )

            if np.isnan(np.sum(invs)):
                raise ValidationError(
                    _('The inventory levels file have non-numeric characters'),
                )
        else:
            raise ValidationError(
                _(' Upload inventory levels file'),
            )

        return invs
