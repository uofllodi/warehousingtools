from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import numpy as np
from django.utils.safestring import mark_safe

class SlotProfileDataForm(forms.Form):
    L = forms.IntegerField(min_value=2, max_value=5, label='Number of slot types', initial=3 )
    nskus = forms.IntegerField(min_value=10, max_value=1000, label='Number of skus', initial=100)
    alpha = forms.DecimalField(min_value=50, max_value=99.99999, label='Desired Storage Service Level', initial=97.5)
    b = forms.DecimalField(min_value=0, label='Vertical clearance within slot', initial=10)
    M = forms.IntegerField(min_value=1, label= 'Pallet positions per slot', initial=2)
    hs = forms.FileField(label = mark_safe("Pallet height of each sku <i class='fa fa-question-circle' aria-hidden='true' title='Upload a csv file with one column and as many rows as skus.'></i>"),
                         help_text = mark_safe("Download an <a href='/static/files/hs.csv'> example </a> with 100 skus"),
                         widget=forms.FileInput(attrs={'accept': ".csv"})) #validators = [validators.validate_hs])
    invs = forms.FileField(label= mark_safe("Inventory level of each sku <i class='fa fa-question-circle' aria-hidden='true' title='Upload a csv file with as many rows as skus and as many columns as time-periods. Include at least 100 time-periods for a good analysis.'></i>"),
                           help_text= mark_safe("Download an <a href='/static/files/invs.csv'> example </a> with 100 skus"),
                           widget=forms.FileInput(attrs={'accept': ".csv"}))

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

    def clean_hs(self):
        csvfile = self.cleaned_data.get("hs")
        nskus = int(self.cleaned_data.get("nskus"))

        try:
            hs = np.genfromtxt(csvfile, delimiter=',')
        except:
            raise ValidationError(
                _('could not be read as an array of numbers'),
            )

        if len(hs.shape) > 1:
            raise ValidationError(
                _('must be a one-dimensional array'),
            )
        elif hs.shape[0] != nskus:
            raise ValidationError(
                _('There are %(v1) pallet height, but %(v2) skus'),
                params={'v1': str(hs.shape[0]), 'v2': str(nskus)},
            )

        if np.min(hs) < 0:
            raise ValidationError(
                _('There are negative pallet heights'),
            )

        if np.isnan(np.sum(hs)):
            raise ValidationError(
                _('There are non-numeric characters'),
            )

        return hs

    def clean_invs(self):
        csvfile = self.cleaned_data.get("invs")
        nskus = int(self.cleaned_data.get("nskus"))

        try:
            invs = np.genfromtxt(csvfile, delimiter=',')
        except:
            raise ValidationError(
                _('could not be read as an 2D array of numbers'),
            )

        if len(invs.shape) != 2:
            raise ValidationError(
                _('must be a 2D array'),
            )
        elif invs.shape[0] != nskus:
            raise ValidationError(
                _('There are %(v1) rows of inventory levels, but %(v2) skus'),
                params={'v1': str(invs.shape[0]), 'v2': str(nskus)},
            )

        if np.min(invs) < 0:
            raise ValidationError(
                _('There are negative inventory levels'),
            )

        if np.isnan(np.sum(invs)):
            raise ValidationError(
                _('There are non-numeric characters'),
            )

        return invs
