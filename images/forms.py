from django import forms
from .models import Image
from urllib import request
from django.core.files.base import ContentFile
import os


class ImageCreateForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('title', 'url', 'description', 'image')  # ✅ add 'image'
        widgets = {
            'url': forms.HiddenInput(),  # still fine
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        url = self.cleaned_data.get('url')
        image = self.cleaned_data.get('image')

        # 📌 Case 1: Image via URL
        if url and not instance.image:
            name = os.path.basename(url)
            try:
                response = request.urlopen(url)
                instance.image.save(name, ContentFile(response.read()),
                                    save=False)
            except Exception as e:
                raise forms.ValidationError(f"Could not download image from URL: {e}")

        # 📌 Case 2: Uploaded image (from <input type="file">)
        if image:
            from PIL import Image as PilImage
            from io import BytesIO
            from django.core.files.base import ContentFile

            pil_image = PilImage.open(image)
            pil_image = pil_image.convert("RGB")

            # Crop to square
            width, height = pil_image.size
            min_side = min(width, height)
            left = (width - min_side) / 2
            top = (height - min_side) / 2
            right = (width + min_side) / 2
            bottom = (height + min_side) / 2
            pil_image = pil_image.crop((left, top, right, bottom))
            pil_image = pil_image.resize((1080, 1080), PilImage.LANCZOS)

            buffer = BytesIO()
            pil_image.save(fp=buffer, format='JPEG')
            file_name = image.name
            instance.image.save(file_name, ContentFile(buffer.getvalue()),
                                save=False)

        if commit:
            instance.save()
        return instance
