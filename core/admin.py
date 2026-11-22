from django.contrib import admin

from .models import (
    Lesson,
    LessonCategory,
    LessonPhrase,
    Phrase,
    PhraseCategory,
    PhraseRequest,
)


class LessonPhraseInline(admin.TabularInline):
    model = LessonPhrase
    extra = 1


@admin.register(LessonCategory)
class LessonCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    inlines = [LessonPhraseInline]
    list_display = ("title", "category", "is_published", "created_by", "updated_at")
    list_filter = ("category", "is_published")
    list_select_related = ("category", "created_by")
    search_fields = ("title", "situation", "summary")


@admin.register(PhraseCategory)
class PhraseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ("cebuano_text", "english_translation", "category", "is_published")
    list_filter = ("category", "is_published")
    list_select_related = ("category",)
    search_fields = ("cebuano_text", "english_translation", "situation")


@admin.register(PhraseRequest)
class PhraseRequestAdmin(admin.ModelAdmin):
    list_display = ("requested_phrase", "submitted_by", "status", "created_at")
    list_filter = ("status", "requested_category")
    list_select_related = ("submitted_by", "requested_category")
    search_fields = ("requested_phrase", "english_translation", "submitted_by__username")
    readonly_fields = ("created_at", "reviewed_at")
