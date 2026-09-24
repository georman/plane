# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: state templates

from plane.db.models import StateTemplate, StateTemplateItem

from .base import BaseSerializer


class StateTemplateItemSerializer(BaseSerializer):
    class Meta:
        model = StateTemplateItem
        fields = ["id", "template_id", "name", "color", "group", "sequence", "default"]
        read_only_fields = ["template"]


class StateTemplateSerializer(BaseSerializer):
    items = StateTemplateItemSerializer(many=True, read_only=True)

    class Meta:
        model = StateTemplate
        fields = ["id", "workspace_id", "name", "is_default", "items"]
        read_only_fields = ["workspace"]
