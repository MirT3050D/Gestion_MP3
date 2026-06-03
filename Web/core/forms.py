from django import forms
from .models import FichierMP3
import json

class FichierMP3Form(forms.ModelForm):
    metadonnees_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'class': 'form-control', 'placeholder': '{\n  "artiste": "Nom",\n  "titre": "Chanson"\n}'}),
        required=False,
        label="Métadonnées (Format JSON)"
    )

    class Meta:
        model = FichierMP3
        fields = ['fichier', 'duree_secondes']
        widgets = {
            'duree_secondes': forms.NumberInput(attrs={'class': 'form-control'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control-file'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['metadonnees_text'].initial = json.dumps(self.instance.metadonnees, indent=4, ensure_ascii=False)

    def clean_metadonnees_text(self):
        data = self.cleaned_data.get('metadonnees_text')
        if not data:
            return {}
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            raise forms.ValidationError("Le format JSON est invalide.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.metadonnees = self.cleaned_data.get('metadonnees_text', {})
        if commit:
            instance.save()
        return instance
