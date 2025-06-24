from django import forms
from .models import Image
from urllib import request
from django.core.files.base import ContentFile
import os


class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('title', 'url', 'description')  # remove 'image'
        widgets = {
            'url': forms.HiddenInput(),  # hide for manual use
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False  # Make all fields optional

    def save(self, commit=True):
        instance = super().save(commit=False)
        url = self.cleaned_data.get('url')
        if url and not instance.image:
            name = os.path.basename(url)
            try:
                response = request.urlopen(url)
                instance.image.save(name, ContentFile(response.read()), save=False)
            except Exception as e:
                raise forms.ValidationError(f"Could not download image from URL: {e}")
        if commit:
            instance.save()
        return instance
