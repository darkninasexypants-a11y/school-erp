from django import forms
from .models import Class, Section


class ClassForm(forms.ModelForm):
    numeric_value = forms.IntegerField(
        widget=forms.NumberInput(attrs={'required': True, 'min': 1, 'max': 12})
    )

    class Meta:
        model = Class
        fields = ['name', 'numeric_value']


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = '__all__'
