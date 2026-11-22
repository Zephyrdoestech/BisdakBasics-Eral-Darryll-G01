from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .storage import SupabaseAudioStorage


class StaticAssetURLTests(SimpleTestCase):
    def test_nested_login_page_uses_root_relative_static_assets(self):
        response = self.client.get("/accounts/login/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/static/')


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
