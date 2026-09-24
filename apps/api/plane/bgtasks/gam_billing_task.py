# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: monthly billing statements.
# On the 1st of each month a statement for the previous month is built for
# every active customer: one fixed line per monthly service (with the list of
# what was delivered under those services) and one priced line per completed
# work item of a per-job service. Each statement is a PDF (WeasyPrint) emailed to GAM for
# review with an "Approve & send" link; only that sends it to the client, in
# the client's language, through the client-email test/live switch.

import calendar
import logging
import uuid
from datetime import date
from decimal import Decimal
from html import escape

from celery import shared_task
from django.utils import timezone

from plane.db.models import BillingStatement, Customer, CustomerServiceRate, IssueCustomerService
from plane.license.utils.gam_brand import get_brand, web_url
from plane.settings.storage import S3Storage
from plane.utils.exception_logger import log_exception
from plane.utils.gam_worktime import TZ

BILLING_TOKEN_SALT = "gam-billing-statement"

MONTHS = {
    "el": ["Ιανουάριος", "Φεβρουάριος", "Μάρτιος", "Απρίλιος", "Μάιος", "Ιούνιος", "Ιούλιος", "Αύγουστος",
           "Σεπτέμβριος", "Οκτώβριος", "Νοέμβριος", "Δεκέμβριος"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"],
}
TEXTS = {
    "el": {
        "title": "Μηνιαία κατάσταση", "period": "Περίοδος", "customer": "Πελάτης", "service": "Υπηρεσία",
        "item": "Εργασία", "date": "Ολοκλήρωση", "amount": "Ποσό", "total": "Σύνολο",
        "retainer_note": "Σταθερή μηνιαία συνεργασία.", "delivered": "Τι παραδόθηκε αυτόν τον μήνα",
        "monthly": "μηνιαία χρέωση",
        "nothing": "Δεν ολοκληρώθηκαν εργασίες αυτόν τον μήνα.", "no_price": "χωρίς συμφωνημένη τιμή",
        "email_subject": "Μηνιαία κατάσταση {month} – {brand}",
        "email_body": "Σας στέλνουμε συνημμένη τη μηνιαία κατάσταση για τον μήνα {month}.",
    },
    "en": {
        "title": "Monthly statement", "period": "Period", "customer": "Customer", "service": "Service",
        "item": "Work item", "date": "Completed", "amount": "Amount", "total": "Total",
        "retainer_note": "Fixed monthly agreement.", "delivered": "Delivered this month",
        "monthly": "monthly fee",
        "nothing": "No work items were completed this month.", "no_price": "no agreed price",
        "email_subject": "Monthly statement {month} – {brand}",
        "email_body": "Please find attached your monthly statement for {month}.",
    },
}


def month_label(period, language):
    return f"{MONTHS.get(language, MONTHS['el'])[period.month - 1]} {period.year}"


def previous_month(today=None):
    today = today or timezone.now().astimezone(TZ).date()
    year, month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    return date(year, month, 1)


def t_monthly(customer):
    return TEXTS.get(customer.language, TEXTS["el"])["monthly"]


def build_statement(customer, period):
    """Lines, deliverables and total for one customer and month (nothing is saved)."""
    last_day = date(period.year, period.month, calendar.monthrange(period.year, period.month)[1])
    rates = {r.service_id: r for r in CustomerServiceRate.objects.filter(customer=customer).select_related("service")}
    completed = (
        IssueCustomerService.objects.filter(
            customer=customer,
            issue__deleted_at__isnull=True,
            issue__state__group="completed",
            issue__completed_at__date__gte=period,
            issue__completed_at__date__lte=last_day,
        )
        .select_related("issue", "issue__project", "service")
        .order_by("issue__completed_at")
    )
    deliverables = [
        {
            "ref": f"{link.issue.project.identifier}-{link.issue.sequence_id}",
            "name": link.issue.name,
            "service": link.service.name,
            "date": link.issue.completed_at.astimezone(TZ).strftime("%d/%m/%Y"),
            "price": str(rates[link.service_id].price) if link.service_id in rates else None,
            "monthly": link.service.billing_type == "monthly",
        }
        for link in completed
    ]
    # Monthly services: one fixed line each; their work items are listed as deliverables only
    lines = [
        {"label": f"{r.service.name} – {t_monthly(customer)}", "amount": str(r.price)}
        for r in rates.values()
        if r.service.billing_type == "monthly"
    ]
    lines += [
        {"label": f"{d['ref']} {d['name']} ({d['service']})", "date": d["date"], "amount": d["price"]}
        for d in deliverables
        if not d["monthly"]
    ]
    deliverables = [d for d in deliverables if d["monthly"]]
    total = sum((Decimal(line["amount"]) for line in lines if line.get("amount")), Decimal("0"))
    return lines, deliverables, total


def render_statement_html(statement):
    t = TEXTS.get(statement.language, TEXTS["el"])
    brand = get_brand()
    customer = statement.customer
    money = lambda value: f"€ {Decimal(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # noqa: E731
    rows = "".join(
        f"<tr><td>{escape(line['label'])}</td><td class='d'>{escape(line.get('date', ''))}</td>"
        f"<td class='n'>{money(line['amount']) if line.get('amount') else '<em>' + t['no_price'] + '</em>'}</td></tr>"
        for line in statement.lines
    ) or f"<tr><td colspan='3'><em>{t['nothing']}</em></td></tr>"
    delivered = ""
    if statement.deliverables:
        items = "".join(
            f"<li>{escape(d['ref'])} {escape(d['name'])} <span class='muted'>({escape(d['service'])}, {d['date']})</span></li>"
            for d in statement.deliverables
        ) or f"<li><em>{t['nothing']}</em></li>"
        delivered = f"<p class='muted'>{t['retainer_note']}</p><h2>{t['delivered']}</h2><ul>{items}</ul>"
    return f"""<!doctype html><html lang="{statement.language}"><head><meta charset="utf-8"><style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{ font-family: "DejaVu Sans", sans-serif; font-size: 10.5pt; color: #17201c; }}
  table.head {{ margin: 0 0 18px; }} table.head td {{ border: none; padding: 0; }}
  h1 {{ font-size: 18pt; margin: 0 0 4px; }} h2 {{ font-size: 12pt; margin: 22px 0 6px; }}
  .muted {{ color: #5a6862; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ padding: 7px 6px; border-bottom: 1px solid #d7dfdb; text-align: left; vertical-align: top; }}
  th {{ font-size: 9pt; font-weight: bold; color: #5a6862; }}
  td.n, th.n {{ text-align: right; white-space: nowrap; }} td.d {{ white-space: nowrap; color: #5a6862; }}
  tfoot td {{ font-weight: bold; font-size: 12pt; border-bottom: none; }}
</style></head><body>
<table class="head"><tr>
  <td><h1>{t['title']}</h1>
    <div>{t['customer']}: <strong>{escape(customer.name)}</strong></div>
    <div>{t['period']}: {month_label(statement.period, statement.language)}</div></td>
  <td style="text-align:right;width:110px"><img src="{escape(brand['logo_url'])}" style="width:90px"></td>
</tr></table>
<table><thead><tr><th>{t['item']}</th><th>{t['date']}</th><th class="n">{t['amount']}</th></tr></thead>
<tbody>{rows}</tbody>
<tfoot><tr><td colspan="2">{t['total']}</td><td class="n">{money(statement.total)}</td></tr></tfoot></table>
{delivered}
<p class="muted" style="margin-top:28px">{escape(brand['name'])}{' · ' + escape(brand['support_email']) if brand['support_email'] else ''}</p>
</body></html>"""


def render_pdf(statement):
    from weasyprint import HTML

    return HTML(string=render_statement_html(statement), base_url=web_url()).write_pdf()


def store_pdf(statement, pdf):
    storage = S3Storage()
    key = f"billing/{statement.period:%Y-%m}/{uuid.uuid4().hex}.pdf"
    storage.s3_client.put_object(Bucket=storage.aws_storage_bucket_name, Key=key, Body=pdf, ContentType="application/pdf")
    if statement.pdf_key:
        storage.s3_client.delete_object(Bucket=storage.aws_storage_bucket_name, Key=statement.pdf_key)
    statement.pdf_key = key


def read_pdf(statement):
    storage = S3Storage()
    return storage.s3_client.get_object(Bucket=storage.aws_storage_bucket_name, Key=statement.pdf_key)["Body"].read()


def pdf_filename(statement):
    return f"{statement.customer.name}-{statement.period:%Y-%m}.pdf".replace("/", "-")


def review_url(statement):
    from django.core import signing

    token = signing.dumps(f"{statement.id}:{statement.token_version}", salt=BILLING_TOKEN_SALT)
    return f"{web_url()}/api/gam/billing/{token}/"


def send_review_email(statement, pdf):
    from plane.bgtasks.gam_approval_task import email_button, send_email

    brand = get_brand()
    reviewer = brand["support_email"]
    if not reviewer:
        logging.getLogger("plane.worker").warning("No support email in Branding; billing statement %s not sent for review", statement.id)
        return
    customer = statement.customer
    period = month_label(statement.period, "el")
    target = customer.contact_email or "(χωρίς email πελάτη)"
    html = f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;color:#17201c">
  <p>Μηνιαία κατάσταση για έλεγχο: <strong>{escape(customer.name)}</strong>, {period}.</p>
  <p>Σύνολο: <strong>€ {statement.total}</strong> · Γλώσσα πελάτη: {statement.language.upper()} · Θα σταλεί στο: {escape(target)}</p>
  <p>Το PDF είναι συνημμένο. Αν όλα είναι σωστά, πατήστε το κουμπί για να σταλεί στον πελάτη.</p>
  {email_button(review_url(statement), "Έγκριση & αποστολή στον πελάτη")}
  <p style="color:#5a6862;font-size:13px">Αν κάτι δεν είναι σωστό, διορθώστε τις εργασίες/τιμές στο {escape(brand['name'])} και δημιουργήστε ξανά την κατάσταση.</p>
</div>"""
    send_email(reviewer, f"[Έλεγχος] Μηνιαία κατάσταση {customer.name} – {period}", html,
               f"Μηνιαία κατάσταση {customer.name} {period}: {review_url(statement)}",
               [(pdf_filename(statement), pdf, "application/pdf")])


def generate_statement(customer, period):
    lines, deliverables, total = build_statement(customer, period)
    statement, _ = BillingStatement.objects.get_or_create(customer=customer, period=period)
    if statement.status == "sent":
        return statement  # never rewrite what the client already has
    statement.lines, statement.deliverables, statement.total = lines, deliverables, total
    statement.language = getattr(customer, "language", "el") or "el"
    statement.token_version += 1  # a regenerated draft invalidates the previous review link
    pdf = render_pdf(statement)
    store_pdf(statement, pdf)
    statement.save()
    send_review_email(statement, pdf)
    return statement


@shared_task
def generate_monthly_statements(period_iso=None, customer_id=None):
    period = date.fromisoformat(period_iso) if period_iso else previous_month()
    customers = Customer.objects.filter(is_active=True)
    if customer_id:
        customers = customers.filter(pk=customer_id)
    for customer in customers:
        try:
            lines, deliverables, _ = build_statement(customer, period)
            if not lines and not deliverables:
                continue  # nothing to bill or report
            generate_statement(customer, period)
        except Exception as e:
            log_exception(e)


def send_statement_to_client(statement):
    from plane.bgtasks.gam_approval_task import email_shell, send_client_email

    brand = get_brand()
    t = TEXTS.get(statement.language, TEXTS["el"])
    month = month_label(statement.period, statement.language)
    html = email_shell(brand, statement.language, f"<p>{t['email_body'].format(month=month)}</p>")
    delivered_to = send_client_email(
        statement.customer.contact_email,
        t["email_subject"].format(month=month, brand=brand["name"]),
        html,
        t["email_body"].format(month=month),
        [(pdf_filename(statement), read_pdf(statement), "application/pdf")],
    )
    statement.sent_at = timezone.now()
    statement.sent_to = delivered_to or ""
    # In test mode the email went to the test address: the statement stays a draft
    if delivered_to == statement.customer.contact_email:
        statement.status = "sent"
    statement.save(update_fields=["status", "sent_at", "sent_to"])
    return delivered_to
