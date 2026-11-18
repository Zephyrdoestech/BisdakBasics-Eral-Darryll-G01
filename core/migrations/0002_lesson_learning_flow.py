import core.storage
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="learning_objectives",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="lesson",
            name="difficulty",
            field=models.CharField(
                choices=[
                    ("BEGINNER", "Beginner"),
                    ("INTERMEDIATE", "Intermediate"),
                    ("ADVANCED", "Advanced"),
                ],
                default="BEGINNER",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="estimated_minutes",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name="lesson",
            name="checkpoint_question",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="lesson",
            name="checkpoint_option_a",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="lesson",
            name="checkpoint_option_b",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="lesson",
            name="checkpoint_correct_answer",
            field=models.CharField(
                blank=True,
                choices=[("A", "Option A"), ("B", "Option B")],
                max_length=1,
            ),
        ),
        migrations.CreateModel(
            name="LessonPhrase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cebuano_text", models.CharField(max_length=300)),
                ("english_translation", models.CharField(max_length=300)),
                ("usage_note", models.CharField(blank=True, max_length=300)),
                (
                    "audio",
                    models.FileField(
                        blank=True,
                        storage=core.storage.SupabaseAudioStorage(),
                        upload_to="lesson-audio/phrases/",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                ["mp3", "wav", "ogg", "m4a"]
                            )
                        ],
                    ),
                ),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="phrases",
                        to="core.lesson",
                    ),
                ),
            ],
            options={"ordering": ["position", "id"]},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="progress_records",
                        to="core.lesson",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_progress",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PhrasePractice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("practice_count", models.PositiveIntegerField(default=1)),
                ("last_practiced_at", models.DateTimeField(auto_now=True)),
                (
                    "phrase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="practice_records",
                        to="core.lessonphrase",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="phrase_practices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LessonAttempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "selected_answer",
                    models.CharField(
                        choices=[("A", "Option A"), ("B", "Option B")], max_length=1
                    ),
                ),
                ("is_correct", models.BooleanField(default=False)),
                ("score", models.PositiveSmallIntegerField(default=0)),
                ("attempted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attempts",
                        to="core.lesson",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lesson_attempts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-attempted_at"]},
        ),
        migrations.AddConstraint(
            model_name="lessonprogress",
            constraint=models.UniqueConstraint(
                fields=("user", "lesson"), name="core_unique_lesson_progress"
            ),
        ),
        migrations.AddConstraint(
            model_name="phrasepractice",
            constraint=models.UniqueConstraint(
                fields=("user", "phrase"), name="core_unique_phrase_practice"
            ),
        ),
    ]
