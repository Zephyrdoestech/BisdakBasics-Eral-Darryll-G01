from django import forms
from django.forms import inlineformset_factory

from .models import Lesson, LessonPhrase


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = (
            "title",
            "category",
            "situation",
            "summary",
            "learning_objectives",
            "difficulty",
            "estimated_minutes",
            "cebuano_text",
            "english_translation",
            "notes",
            "audio",
            "checkpoint_question",
            "checkpoint_option_a",
            "checkpoint_option_b",
            "checkpoint_correct_answer",
            "position",
            "is_published",
        )
        widgets = {
            "cebuano_text": forms.Textarea(attrs={"rows": 6}),
            "english_translation": forms.Textarea(attrs={"rows": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "learning_objectives": forms.Textarea(attrs={"rows": 3}),
            "checkpoint_question": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        checkpoint_fields = (
            "checkpoint_question",
            "checkpoint_option_a",
            "checkpoint_option_b",
            "checkpoint_correct_answer",
        )
        if any(cleaned_data.get(field) for field in checkpoint_fields):
            for field in checkpoint_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "Complete all checkpoint fields or leave them blank.")
        return cleaned_data

    def clean_audio(self):
        audio = self.cleaned_data.get("audio")
        if audio and audio.size > 15 * 1024 * 1024:
            raise forms.ValidationError("Audio files must be 15 MB or smaller.")
        return audio


class LessonPhraseForm(forms.ModelForm):
    class Meta:
        model = LessonPhrase
        fields = ("cebuano_text", "english_translation", "usage_note", "audio", "position")
        widgets = {
            "usage_note": forms.TextInput(),
        }

    def clean_audio(self):
        audio = self.cleaned_data.get("audio")
        if audio and audio.size > 15 * 1024 * 1024:
            raise forms.ValidationError("Audio files must be 15 MB or smaller.")
        return audio


LessonPhraseFormSet = inlineformset_factory(
    Lesson,
    LessonPhrase,
    form=LessonPhraseForm,
    extra=5,
    can_delete=True,
    max_num=20,
    validate_max=True,
)
