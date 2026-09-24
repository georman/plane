# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: white-label brand settings (name, support email, website,
# logo), editable in the admin panel (God mode > Branding) and used by the
# apps, emails and error pages instead of "Plane".

import os

from plane.license.models import InstanceConfiguration

# Neutral defaults: a new installation shows no company until its admin fills in Branding
BRAND_KEYS = {
    "GAM_BRAND_NAME": "Projects",
    "GAM_SUPPORT_EMAIL": "",
    "GAM_BRAND_WEBSITE": "",
    "GAM_BRAND_LOGO": "",  # storage key of the uploaded logo; empty = built-in logo
    # Client emails stay in test mode (all sent to GAM_TEST_EMAIL) until switched to "live"
    "GAM_CLIENT_EMAILS": "test",
    "GAM_TEST_EMAIL": "",
}
BRAND_CATEGORY = "BRANDING"
LOGO_PATH = "/api/instances/brand-logo/"
DEFAULT_LOGO_PATH = "/assets/gam-logo.png"


def web_url():
    return os.environ.get("WEB_URL", "http://localhost").rstrip("/")


def get_brand():
    values = dict(InstanceConfiguration.objects.filter(key__in=BRAND_KEYS).values_list("key", "value"))
    value = lambda key: (values.get(key) or BRAND_KEYS[key]).strip()  # noqa: E731
    logo_key = value("GAM_BRAND_LOGO")
    return {
        "name": value("GAM_BRAND_NAME") or "Projects",
        "support_email": value("GAM_SUPPORT_EMAIL"),
        "website": value("GAM_BRAND_WEBSITE"),
        "has_custom_logo": bool(logo_key),
        # Versioned so browsers and mail clients pick up a new upload
        "logo_url": f"{web_url()}{LOGO_PATH}?v={logo_key.rsplit('/', 1)[-1][:8]}" if logo_key
        else f"{web_url()}{DEFAULT_LOGO_PATH}",
    }


def client_email_settings():
    """("live", None) or ("test", address that receives every client email instead)."""
    values = dict(
        InstanceConfiguration.objects.filter(key__in=["GAM_CLIENT_EMAILS", "GAM_TEST_EMAIL"]).values_list("key", "value")
    )
    mode = (values.get("GAM_CLIENT_EMAILS") or "test").strip().lower()
    test_email = (values.get("GAM_TEST_EMAIL") or "").strip() or get_brand()["support_email"]
    return ("live", None) if mode == "live" else ("test", test_email)
