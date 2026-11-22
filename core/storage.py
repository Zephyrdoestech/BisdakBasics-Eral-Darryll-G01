import json
import mimetypes
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.storage import FileSystemStorage, Storage
from django.core.exceptions import ImproperlyConfigured, SuspiciousFileOperation
from django.utils.deconstruct import deconstructible
from django.utils.text import get_valid_filename


@deconstructible
class SupabaseAudioStorage(Storage):
    """Use local media in development and a public Supabase bucket in production."""

    def __init__(self):
        self.local = FileSystemStorage() if settings.DEBUG else None

    def _configuration(self):
        base_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
        service_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
        bucket = getattr(settings, "SUPABASE_STORAGE_BUCKET", "lesson-audio")
        if not base_url or not service_key:
            raise ImproperlyConfigured(
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to upload production lesson audio."
            )
        return base_url, service_key, bucket

    def _request(self, method, path, body=None, content_type="application/json"):
        base_url, key, _ = self._configuration()
        request = Request(
            f"{base_url}/storage/v1/{path}",
            data=body,
            method=method,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": content_type,
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                return response.read()
        except (HTTPError, URLError) as error:
            detail = error.read().decode("utf-8", "replace") if isinstance(error, HTTPError) else str(error)
            raise OSError(f"Supabase Storage request failed: {detail}") from error

    def _save(self, name, content):
        if self.local:
            return self.local.save(name, content)
        base_url, _, bucket = self._configuration()
        del base_url
        safe_name = "/".join(get_valid_filename(part) for part in name.split("/"))
        if safe_name.startswith("/") or ".." in safe_name.split("/"):
            raise SuspiciousFileOperation("Invalid audio object name")
        content_type, _ = mimetypes.guess_type(safe_name)
        content_type = content_type or "application/octet-stream"
        encoded_name = quote(safe_name, safe="/")
        self._request(
            "POST",
            f"object/{quote(bucket, safe='')}/{encoded_name}",
            body=content.read(),
            content_type=content_type,
        )
        return safe_name

    def _open(self, name, mode="rb"):
        if self.local:
            return self.local.open(name, mode)
        from django.core.files.base import ContentFile

        _, _, bucket = self._configuration()
        data = self._request(
            "GET", f"object/{quote(bucket, safe='')}/{quote(name, safe='/')}"
        )
        return ContentFile(data)

    def delete(self, name):
        if not name:
            return
        self.delete_many([name])

    def delete_many(self, names):
        valid_names = [name for name in names if name]
        if not valid_names:
            return
        if self.local:
            for name in valid_names:
                self.local.delete(name)
            return
        _, _, bucket = self._configuration()
        self._request(
            "DELETE",
            f"object/{quote(bucket, safe='')}",
            body=json.dumps({"prefixes": valid_names}).encode("utf-8"),
        )

    def exists(self, name):
        if self.local:
            return self.local.exists(name)
        # Supabase does not expose an inexpensive object HEAD endpoint through
        # the same REST route; Django only needs unique names for lesson uploads.
        return False

    def get_available_name(self, name, max_length=None):
        if self.local:
            return self.local.get_available_name(name, max_length)
        path, filename = os.path.split(name)
        stem, extension = os.path.splitext(filename)
        unique_name = f"{stem}-{uuid.uuid4().hex}{extension}"
        return os.path.join(path, unique_name) if path else unique_name

    def url(self, name):
        if self.local:
            return self.local.url(name)
        base_url, _, bucket = self._configuration()
        return (
            f"{base_url}/storage/v1/object/public/"
            f"{quote(bucket, safe='')}/{quote(name, safe='/')}"
        )


audio_storage = SupabaseAudioStorage()
