# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: public Terms of Service / Privacy Policy pages, edited in
# God mode > Legal (Markdown, Greek and English).

from urllib.parse import urlparse

from plane.license.models import InstanceConfiguration
from plane.license.utils.gam_brand import get_brand, web_url
from plane.license.utils.gam_legal_defaults import DEFAULTS

DOCS = ("terms", "privacy")
LANGUAGES = ("el", "en")
LEGAL_KEYS = [
    "GAM_LEGAL_COMPANY",
    "GAM_LEGAL_ADDRESS",
    "GAM_LEGAL_UPDATED",
    *[f"GAM_LEGAL_{doc.upper()}_{lang.upper()}" for doc in DOCS for lang in LANGUAGES],
]
TITLES = {
    "terms": {"el": "Όροι Χρήσης", "en": "Terms of Service"},
    "privacy": {"el": "Πολιτική Απορρήτου", "en": "Privacy Policy"},
}
UPDATED = {"el": "Τελευταία ενημέρωση", "en": "Last updated"}
MISSING = {"el": "[συμπληρώστε στο Admin > Legal]", "en": "[fill in at Admin > Legal]"}


def legal_config():
    return dict(InstanceConfiguration.objects.filter(key__in=LEGAL_KEYS).values_list("key", "value"))


def legal_markdown(doc, language, config=None):
    """The saved text, or the standard text, with company/brand details filled in."""
    config = legal_config() if config is None else config
    text = (config.get(f"GAM_LEGAL_{doc.upper()}_{language.upper()}") or "").strip() or DEFAULTS[doc][language]
    brand = get_brand()
    tokens = {
        "[company]": (config.get("GAM_LEGAL_COMPANY") or "").strip() or brand["name"],
        "[address]": (config.get("GAM_LEGAL_ADDRESS") or "").strip() or MISSING[language],
        "[brand]": brand["name"],
        "[domain]": urlparse(web_url()).netloc,
        "[email]": brand["support_email"] or MISSING[language],
    }
    for token, value in tokens.items():
        text = text.replace(token, value)
    return text


def legal_html(doc, language, config=None):
    import markdown
    import nh3

    html = markdown.markdown(legal_markdown(doc, language, config), extensions=["tables", "sane_lists"])
    return nh3.clean(html)
