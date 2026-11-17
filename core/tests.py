from django.test import SimpleTestCase


class StaticAssetURLTests(SimpleTestCase):
    def test_nested_login_page_uses_root_relative_static_assets(self):
        response = self.client.get("/accounts/login/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/static/')
