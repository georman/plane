# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: custom fields

from rest_framework import serializers

from plane.db.models import CustomField

from .base import BaseSerializer


class CustomFieldSerializer(BaseSerializer):
    class Meta:
        model = CustomField
        fields = ["id", "project_id", "name", "field_type", "options", "sequence"]
        read_only_fields = ["workspace", "project"]

    def validate_name(self, name):
        name = name.strip()
        if not name:
            raise serializers.ValidationError("The field needs a name.")
        return name

    def validate_options(self, options):
        if not isinstance(options, list):
            raise serializers.ValidationError("Options must be a list.")
        cleaned = []
        for option in options:
            text = str(option).strip()
            if text and text not in cleaned:
                cleaned.append(text)
        return cleaned
