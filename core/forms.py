from django import forms
from django.forms import inlineformset_factory

from .models import (
    Lesson,
    LessonPhrase,
    Phrase,
    PhraseCategory,
    PhraseRequest,
)


MAX_AUDIO_FILE_BYTES = 15 * 1024 * 1024


def _validate_audio_size(audio):
    if audio and audio.size > MAX_AUDIO_FILE_BYTES:
        raise forms.ValidationError("Audio files must be 15 MB or smaller.")
    return audio


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
        return _validate_audio_size(self.cleaned_data.get("audio"))


class LessonPhraseForm(forms.ModelForm):
    class Meta:
        model = LessonPhrase
        fields = ("cebuano_text", "english_translation", "usage_note", "audio", "position")
        widgets = {
            "usage_note": forms.TextInput(),
        }

    def clean_audio(self):
        return _validate_audio_size(self.cleaned_data.get("audio"))


LessonPhraseFormSet = inlineformset_factory(
    Lesson,
    LessonPhrase,
    form=LessonPhraseForm,
    extra=5,
    can_delete=True,
    max_num=20,
    validate_max=True,
)


class PhraseForm(forms.ModelForm):
    class Meta:
        model = Phrase
        fields = (
            "cebuano_text",
            "english_translation",
            "category",
            "situation",
            "pronunciation_note",
            "audio",
            "is_published",
        )
        widgets = {"pronunciation_note": forms.Textarea(attrs={"rows": 3})}

    def clean_audio(self):
        return _validate_audio_size(self.cleaned_data.get("audio"))


class PhraseCategoryForm(forms.ModelForm):
    class Meta:
        model = PhraseCategory
        fields = ("name", "description")


class PhraseSearchForm(forms.Form):
    q = forms.CharField(required=False, max_length=100, strip=True)


class PhraseRequestForm(forms.ModelForm):
    class Meta:
        model = PhraseRequest
        fields = ("requested_phrase", "english_translation", "requested_category", "situation")
        widgets = {
            "requested_phrase": forms.TextInput(attrs={"placeholder": "e.g. Can you help me?"}),
            "english_translation": forms.TextInput(attrs={"placeholder": "English meaning"}),
            "situation": forms.TextInput(attrs={"placeholder": "e.g. At a market"}),
        }


class PhraseRequestReviewForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(("APPROVED", "Approve and add phrase"), ("REJECTED", "Decline request"))
    )
    category = forms.ModelChoiceField(queryset=PhraseCategory.objects.none(), required=False)
    english_translation = forms.CharField(required=False, max_length=240)
    admin_note = forms.CharField(required=False, max_length=300)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = PhraseCategory.objects.only("id", "name")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("decision") == "APPROVED":
            if not cleaned_data.get("category"):
                self.add_error("category", "Choose a category before approving this phrase.")
            if not cleaned_data.get("english_translation"):
                self.add_error("english_translation", "Add an English translation before approving this phrase.")
        return cleaned_data
