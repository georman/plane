# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: "Approve & send" page for a monthly billing statement. The
# link is only emailed to GAM's review address. GET shows the summary, the
# POST sends the PDF to the client (through the client-email test/live switch).

from html import escape

from django.core import signing
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from plane.bgtasks.gam_billing_task import BILLING_TOKEN_SALT, month_label, send_statement_to_client
from plane.db.models import BillingStatement
from plane.license.utils.gam_brand import client_email_settings, get_brand
from plane.utils.gam_approval import TOKEN_MAX_AGE
from plane.utils.gam_worktime import TZ


def page(body):
    brand = get_brand()
    return HttpResponse(f"""<!doctype html><html lang="el"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>Μηνιαία κατάσταση – {escape(brand['name'])}</title>
<style>body{{margin:0;background:#f5f7f6;color:#17201c;font:16px/1.55 Arial,sans-serif}}
main{{max-width:640px;margin:0 auto;padding:24px 16px}}.card{{background:#fff;border:1px solid #d7dfdb;border-radius:10px;padding:20px;margin-top:16px}}
button{{font:inherit;font-weight:bold;border:0;border-radius:8px;padding:14px 22px;background:#1f6f4a;color:#fff;cursor:pointer;width:100%}}
.muted{{color:#5a6862}}.warn{{color:#b42318}}.ok{{color:#1f6f4a}}</style></head>
<body><main><img src="{escape(brand['logo_url'])}" alt="{escape(brand['name'])}" width="100">{body}</main></body></html>""")


@csrf_exempt
def billing_review(request, token):
    try:
        value = signing.loads(token, salt=BILLING_TOKEN_SALT, max_age=TOKEN_MAX_AGE)
        statement_id, _, version = str(value).partition(":")
        statement = BillingStatement.objects.select_related("customer").get(pk=statement_id)
        valid = str(statement.token_version) == version
    except Exception:
        valid, statement = False, None
    if not valid:
        return page('<div class="card"><h1 class="warn">Ο σύνδεσμος δεν ισχύει</h1>'
                    "<p>Η κατάσταση άλλαξε ή δημιουργήθηκε ξανά. Χρησιμοποιήστε το πιο πρόσφατο email ελέγχου.</p></div>")
    customer = statement.customer
    period = month_label(statement.period, "el")
    if statement.status == "sent":
        when = statement.sent_at.astimezone(TZ).strftime("%d/%m/%Y %H:%M")
        return page(f'<div class="card"><h1 class="ok">Έχει ήδη σταλεί</h1><p>Η κατάσταση {escape(customer.name)} '
                    f"({period}) στάλθηκε στο {escape(statement.sent_to)} στις {when}.</p></div>")
    if not customer.contact_email:
        return page(f'<div class="card"><h1 class="warn">Λείπει το email του πελάτη</h1><p>Ορίστε email για τον '
                    f"πελάτη {escape(customer.name)} στο Settings → Customers.</p></div>")

    mode, test_email = client_email_settings()
    if request.method == "POST":
        delivered_to = send_statement_to_client(statement)
        note = "" if mode == "live" else " (δοκιμαστική λειτουργία – ο πελάτης δεν έλαβε τίποτα)"
        return page(f'<div class="card"><h1 class="ok">Στάλθηκε</h1><p>Η κατάσταση στάλθηκε στο '
                    f"{escape(delivered_to)}{note}.</p></div>")

    mode_note = (
        f'<p class="warn"><strong>Δοκιμαστική λειτουργία:</strong> θα σταλεί στο {escape(test_email)}, όχι στον πελάτη.</p>'
        if mode != "live" else ""
    )
    return page(f"""<div class="card"><h1>Μηνιαία κατάσταση</h1>
<p><strong>{escape(customer.name)}</strong> · {period}<br>Σύνολο: <strong>€ {statement.total}</strong><br>
Γλώσσα: {statement.language.upper()} · Προς: {escape(customer.contact_email)}</p>{mode_note}
<form method="post"><button type="submit">Έγκριση & αποστολή στον πελάτη</button></form>
<p class="muted">Το PDF είναι συνημμένο στο email ελέγχου.</p></div>""")
