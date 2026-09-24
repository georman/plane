# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: public Terms of Service / Privacy Policy pages
# (https://<domain>/legal/terms, /legal/privacy - the web container's nginx
# forwards /legal/ here). Text is edited in God mode > Legal.

from html import escape

from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from plane.license.utils.gam_brand import get_brand
from plane.license.utils.gam_legal import DOCS, LANGUAGES, TITLES, UPDATED, legal_config, legal_html


def pick_language(request):
    requested = (request.GET.get("lang") or "").lower()
    if requested in LANGUAGES:
        return requested
    accept = request.headers.get("Accept-Language", "").lower()
    return "en" if accept.startswith("en") else "el"


@require_GET
def legal_page(request, doc):
    if doc not in DOCS:
        raise Http404
    language = pick_language(request)
    other_language = "en" if language == "el" else "el"
    other_doc = "privacy" if doc == "terms" else "terms"
    brand = get_brand()
    config = legal_config()
    title = TITLES[doc][language]
    updated = (config.get("GAM_LEGAL_UPDATED") or "").strip()
    updated_line = f'<p class="muted">{UPDATED[language]}: {escape(updated)}</p>' if updated else ""
    page = f"""<!doctype html>
<html lang="{language}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} – {escape(brand["name"])}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; max-width: 780px; margin: 0 auto;
         padding: 32px 20px 96px; line-height: 1.6; color: #1a1a1a; background: #fff; }}
  @media (prefers-color-scheme: dark) {{
    body {{ color: #e5e5e5; background: #111214; }} a {{ color: #6ea8ff; }}
    th, td {{ border-color: #333 !important; }}
  }}
  header {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 28px; }}
  header img {{ height: 40px; }}
  nav a {{ margin-left: 14px; font-size: 14px; }}
  h1 {{ font-size: 28px; margin: 0 0 4px; }} h2 {{ font-size: 18px; margin-top: 32px; }}
  p, li {{ font-size: 15px; }} a {{ color: #1080bc; }}
  .muted {{ color: #767676; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; vertical-align: top; }}
</style>
</head>
<body>
<header>
  <img src="{escape(brand["logo_url"])}" alt="{escape(brand["name"])}">
  <nav>
    <a href="/legal/{other_doc}?lang={language}">{escape(TITLES[other_doc][language])}</a>
    <a href="/legal/{doc}?lang={other_language}">{"English" if other_language == "en" else "Ελληνικά"}</a>
  </nav>
</header>
<h1>{escape(title)}</h1>
{updated_line}
{legal_html(doc, language, config)}
</body>
</html>"""
    response = HttpResponse(page)
    response["Cache-Control"] = "public, max-age=300"
    return response
