# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: the brand logo. GET is public (login page, favicon, emails);
# uploading or removing it is for instance admins only.

import uuid

from django.http import HttpResponse, HttpResponseRedirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from plane.license.api.permissions import InstanceAdminPermission
from plane.license.models import InstanceConfiguration
from plane.license.utils.gam_brand import DEFAULT_LOGO_PATH, get_brand
from plane.settings.storage import S3Storage
from plane.utils.cache import invalidate_cache

from .base import BaseAPIView

ALLOWED_LOGO_TYPES = {"image/png", "image/jpeg", "image/svg+xml", "image/webp", "image/gif"}
MAX_LOGO_BYTES = 2 * 1024 * 1024


def logo_config():
    return InstanceConfiguration.objects.filter(key="GAM_BRAND_LOGO").first()


class BrandLogoEndpoint(BaseAPIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [InstanceAdminPermission()]

    def get(self, request):
        config = logo_config()
        if not config or not config.value:
            return HttpResponseRedirect(DEFAULT_LOGO_PATH)
        storage = S3Storage()
        try:
            obj = storage.s3_client.get_object(Bucket=storage.aws_storage_bucket_name, Key=config.value)
        except Exception:
            return HttpResponseRedirect(DEFAULT_LOGO_PATH)
        response = HttpResponse(obj["Body"].read(), content_type=obj.get("ContentType") or "image/png")
        response["Cache-Control"] = "public, max-age=3600"
        return response

    @invalidate_cache(path="/api/instances/", user=False)
    def post(self, request):
        upload = request.FILES.get("logo")
        if not upload:
            return Response({"error": "Choose an image file to upload."}, status=status.HTTP_400_BAD_REQUEST)
        if upload.content_type not in ALLOWED_LOGO_TYPES:
            return Response({"error": "The logo must be a PNG, JPG, SVG, WebP or GIF image."},
                            status=status.HTTP_400_BAD_REQUEST)
        if upload.size > MAX_LOGO_BYTES:
            return Response({"error": "The logo must be 2 MB or smaller."}, status=status.HTTP_400_BAD_REQUEST)

        storage = S3Storage()
        key = f"brand/{uuid.uuid4().hex}-{upload.name}"
        storage.s3_client.put_object(
            Bucket=storage.aws_storage_bucket_name, Key=key, Body=upload.read(), ContentType=upload.content_type
        )
        config = logo_config()
        old_key = config.value if config else ""
        InstanceConfiguration.objects.update_or_create(
            key="GAM_BRAND_LOGO", defaults={"value": key, "category": "BRANDING", "is_encrypted": False}
        )
        if old_key:
            storage.s3_client.delete_object(Bucket=storage.aws_storage_bucket_name, Key=old_key)
        return Response(get_brand(), status=status.HTTP_200_OK)

    @invalidate_cache(path="/api/instances/", user=False)
    def delete(self, request):
        config = logo_config()
        if config and config.value:
            storage = S3Storage()
            storage.s3_client.delete_object(Bucket=storage.aws_storage_bucket_name, Key=config.value)
            config.value = ""
            config.save()
        return Response(get_brand(), status=status.HTTP_200_OK)
