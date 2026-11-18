from django import forms

from .models import Lesson


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = (
            "title",
            "category",
            "situation",
            "summary",
            "cebuano_text",
            "english_translation",
            "notes",
            "audio",
            "position",
            "is_published",
        )
        widgets = {
            "cebuano_text": forms.Textarea(attrs={"rows": 6}),
            "english_translation": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_audio(self):
        audio = self.cleaned_data.get("audio")
        if audio and audio.size > 15 * 1024 * 1024:
            raise forms.ValidationError("Audio files must be 15 MB or smaller.")
        return audio
