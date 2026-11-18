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
    category = models.ForeignKey(
        LessonCategory, on_delete=models.PROTECT, related_name="lessons"
    )
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    situation = models.CharField(max_length=200, help_text="For example, ordering food")
    summary = models.CharField(max_length=300)
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
