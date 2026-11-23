import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.db.models import Q
from django.db.models.functions import Lower
from django.test import SimpleTestCase, override_settings

from accounts.forms import ProfileForm
from accounts.models import User
from .storage import SupabaseAudioStorage
from .views import _calculate_streak_days, _delete_audio_files, _extract_daily_goal_minutes


class StaticAssetURLTests(SimpleTestCase):
    def test_nested_login_page_uses_root_relative_static_assets(self):
        response = self.client.get("/accounts/login/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/static/')
        self.assertContains(response, 'width="48" height="41" decoding="async"')

    def test_home_hero_image_sets_fetchpriority_and_dimensions(self):
        response = self.client.get("/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'width="340" height="210" decoding="async" fetchpriority="high"')


class LearnerDashboardStreakTests(SimpleTestCase):
    def test_calculate_streak_days_counts_consecutive_days(self):
        today = datetime.date(2026, 11, 22)
        dates = {
            datetime.date(2026, 11, 22),
            datetime.date(2026, 11, 21),
            datetime.date(2026, 11, 20),
            datetime.date(2026, 11, 18),
        }
        self.assertEqual(_calculate_streak_days(dates, today), 3)

    def test_calculate_streak_days_returns_zero_when_broken(self):
        today = datetime.date(2026, 11, 22)
        dates = {datetime.date(2026, 11, 19)}
        self.assertEqual(_calculate_streak_days(dates, today), 0)

    def test_extract_daily_goal_minutes_parses_goal_and_defaults(self):
        user_with_goal = SimpleNamespace(profile=SimpleNamespace(learning_goal="Practice 25 minutes daily"))
        user_out_of_range = SimpleNamespace(profile=SimpleNamespace(learning_goal="500 minutes"))
        user_without_profile = SimpleNamespace(profile=None)

        self.assertEqual(_extract_daily_goal_minutes(user_with_goal), 25)
        self.assertEqual(_extract_daily_goal_minutes(user_out_of_range), 10)
        self.assertEqual(_extract_daily_goal_minutes(user_without_profile), 10)


class QueryAndFormOptimizationTests(SimpleTestCase):
    def test_lower_alias_query_aligns_with_case_insensitive_indexes(self):
        sql = str(
            User.objects.alias(
                username_lower=Lower("username"),
                email_lower=Lower("email"),
            )
            .filter(Q(username_lower="maria") | Q(email_lower="maria"))
            .query
        )
        self.assertIn('LOWER("accounts_user"."username")', sql)
        self.assertIn('LOWER("accounts_user"."email")', sql)
        self.assertNotIn("UPPER(", sql)

    def test_profile_form_skips_db_check_and_writes_when_unchanged(self):
        user = MagicMock(
            pk=1,
            first_name="Maria",
            last_name="Santos",
            email="maria@example.com",
        )
        user.get_full_name.return_value = "Maria Santos"
        profile = MagicMock(
            contact_number="09171234567",
            location="Cebu City",
            learning_goal="15 min daily",
        )
        form = ProfileForm(
            data={
                "full_name": "Maria Santos",
                "email": "MARIA@example.com",
                "contact_number": "09171234567",
                "location": "Cebu City",
                "learning_goal": "15 min daily",
            },
            user=user,
            profile=profile,
        )
        with patch.object(User.objects, "exclude") as mock_exclude:
            self.assertTrue(form.is_valid())
            mock_exclude.assert_not_called()

        form.save()
        user.save.assert_not_called()
        profile.save.assert_not_called()

    def test_delete_audio_files_batches_when_supported_and_falls_back(self):
        batched_storage = MagicMock()
        _delete_audio_files(batched_storage, ["a.mp3", "", "b.mp3"])
        batched_storage.delete_many.assert_called_once_with(["a.mp3", "b.mp3"])

        simple_storage = MagicMock(spec=["delete"])
        _delete_audio_files(simple_storage, ["a.mp3", "", "b.mp3"])
        self.assertEqual(simple_storage.delete.call_count, 2)


class SupabaseAudioStorageTests(SimpleTestCase):
    @override_settings(
        DEBUG=False,
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="test-key",
        SUPABASE_STORAGE_BUCKET="lesson-audio",
    )
    def test_delete_many_batches_prefixes_in_single_request(self):
        storage = SupabaseAudioStorage()
        with patch.object(storage, "_request") as mock_request:
            storage.delete_many(["lesson-audio/a.mp3", "", "lesson-audio/b.mp3"])

            mock_request.assert_called_once_with(
                "DELETE",
                "object/lesson-audio",
                body=b'{"prefixes": ["lesson-audio/a.mp3", "lesson-audio/b.mp3"]}',
            )
