# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: brand values for email templates, e.g.
#   {% load gam_brand %} ... {% brand_name %} ... <img src="{% brand_logo_url %}">

from django import template

from plane.license.utils.gam_brand import get_brand

register = template.Library()


@register.simple_tag
def brand_name():
    return get_brand()["name"]


@register.simple_tag
def brand_logo_url():
    return get_brand()["logo_url"]


@register.simple_tag
def brand_support_email():
    return get_brand()["support_email"]


@register.simple_tag
def brand_website():
    return get_brand()["website"]
