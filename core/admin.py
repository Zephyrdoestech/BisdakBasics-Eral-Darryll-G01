from django.contrib import admin

from .models import Lesson, LessonCategory


@admin.register(LessonCategory)
class LessonCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "created_by", "updated_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "situation", "summary")
