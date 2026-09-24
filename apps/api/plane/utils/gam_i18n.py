# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: messages from GAM endpoints in the signed-in user's language.

from plane.db.models import Profile


def user_language(user):
    language = Profile.objects.filter(user_id=getattr(user, "id", None)).values_list("language", flat=True).first()
    return "en" if language == "en" else "el"


def message(request, en, el):
    return en if user_language(request.user) == "en" else el
