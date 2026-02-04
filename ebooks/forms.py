from django import forms
from .models import Ebook

class RegenerateForm(forms.Form):
    voice_style = forms.ChoiceField(choices=Ebook.VOICE_STYLES, widget=forms.Select(attrs={'class': 'form-select'}))
    accent = forms.ChoiceField(choices=Ebook.ACCENT_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

class EbookForm(forms.ModelForm):
    class Meta:
        model = Ebook
        fields = ['title', 'pdf_file', 'voice_style', 'accent', 'background_animation', 'background_voice']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a title for your ebook'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'voice_style': forms.Select(attrs={
                'class': 'form-select'
            }),
            'accent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'background_animation': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*'
            }),
            'background_voice': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add help text for voice options
        self.fields['voice_style'].help_text = 'Choose the reading style for your audiobook'
        self.fields['accent'].help_text = 'Select the accent for the voice'
        
        # Make file field required
        self.fields['pdf_file'].required = True
        self.fields['pdf_file'].widget.attrs['required'] = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.uploaded_by = self.user
        if commit:
            instance.save()
        return instance