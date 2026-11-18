from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from .storage import audio_storage


class LessonCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "lesson categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Lesson(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"

    category = models.ForeignKey(
        LessonCategory, on_delete=models.PROTECT, related_name="lessons"
    )
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    situation = models.CharField(max_length=200, help_text="For example, ordering food")
    summary = models.CharField(max_length=300)
    learning_objectives = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=12, choices=Difficulty.choices, default=Difficulty.BEGINNER
    )
    estimated_minutes = models.PositiveSmallIntegerField(default=10)
    checkpoint_question = models.CharField(max_length=300, blank=True)
    checkpoint_option_a = models.CharField(max_length=160, blank=True)
    checkpoint_option_b = models.CharField(max_length=160, blank=True)
    checkpoint_correct_answer = models.CharField(
        max_length=1,
        choices=(("A", "Option A"), ("B", "Option B")),
        blank=True,
    )
    cebuano_text = models.TextField(help_text="Cebuano dialogue or lesson content")
    english_translation = models.TextField()
    notes = models.TextField(blank=True, help_text="Optional vocabulary or grammar notes")
    audio = models.FileField(
        storage=audio_storage,
        upload_to="lesson-audio/",
        blank=True,
        validators=[FileExtensionValidator(["mp3", "wav", "ogg", "m4a"])],
    )
    position = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_lessons",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__name", "position", "title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "lesson"
            candidate = base_slug
            suffix = 2
            while Lesson.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                candidate = f"{base_slug}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class LessonPhrase(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="phrases")
    cebuano_text = models.CharField(max_length=300)
    english_translation = models.CharField(max_length=300)
    usage_note = models.CharField(max_length=300, blank=True)
    audio = models.FileField(
        storage=audio_storage,
        upload_to="lesson-audio/phrases/",
        blank=True,
        validators=[FileExtensionValidator(["mp3", "wav", "ogg", "m4a"])],
    )
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.cebuano_text} ({self.lesson.title})"


class LessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "lesson"), name="core_unique_lesson_progress")
        ]


class PhrasePractice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="phrase_practices"
    )
    phrase = models.ForeignKey(
        LessonPhrase, on_delete=models.CASCADE, related_name="practice_records"
    )
    practice_count = models.PositiveIntegerField(default=1)
    last_practiced_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "phrase"), name="core_unique_phrase_practice")
        ]


class LessonAttempt(models.Model):
    class Choice(models.TextChoices):
        A = "A", "Option A"
        B = "B", "Option B"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_attempts"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attempts")
    selected_answer = models.CharField(max_length=1, choices=Choice.choices)
    is_correct = models.BooleanField(default=False)
    score = models.PositiveSmallIntegerField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempted_at"]
