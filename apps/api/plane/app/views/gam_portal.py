# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: client portal. A customer opens their personal link (from
# Settings > Customers) and sees, in their language: what waits for their
# approval, their open jobs, recently finished jobs and their monthly
# statements. Read-only; approvals still happen on the approval page.

from datetime import timedelta
from html import escape
from urllib.parse import quote

from django.http import Http404, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from plane.bgtasks.gam_approval_task import approval_url
from plane.bgtasks.gam_billing_task import month_label, pdf_filename, read_pdf
from plane.db.models import ApprovalRequest, BillingStatement, IssueCustomerService
from plane.license.utils.gam_brand import get_brand
from plane.utils.gam_worktime import TZ
from plane.utils.gam_portal import customer_from_token

RECENT_DAYS = 90

# What the client sees as the status. Internal stages show as "In progress".
CLIENT_STATES = {
    "Έγκριση πελάτη": ("Περιμένει την έγκρισή σας", "Waiting for your approval"),
    "Client approval": ("Περιμένει την έγκρισή σας", "Waiting for your approval"),
    "Διορθώσεις": ("Γίνονται οι διορθώσεις", "Making your changes"),
    "Corrections": ("Γίνονται οι διορθώσεις", "Making your changes"),
    "Έτοιμο για παράδοση": ("Έτοιμο για παράδοση", "Ready for delivery"),
    "Ready for delivery": ("Έτοιμο για παράδοση", "Ready for delivery"),
    "Παραδόθηκε": ("Παραδόθηκε", "Delivered"),
    "Delivered": ("Παραδόθηκε", "Delivered"),
    "Τιμολογήθηκε": ("Ολοκληρώθηκε", "Completed"),
    "Invoiced": ("Ολοκληρώθηκε", "Completed"),
}
IN_PROGRESS = ("Σε επεξεργασία", "In progress")
DONE = ("Ολοκληρώθηκε", "Completed")

TEXTS = {
    "el": {
        "title": "Οι εργασίες σας",
        "hello": "Γεια σας, {name}",
        "waiting": "Περιμένουν την έγκρισή σας",
        "review": "Προβολή και έγκριση",
        "open": "Σε εξέλιξη",
        "done": "Ολοκληρώθηκαν πρόσφατα",
        "statements": "Μηνιαίες καταστάσεις",
        "download": "Λήψη PDF",
        "due": "Παράδοση έως",
        "none": "Τίποτα αυτή τη στιγμή.",
        "contact": "Για οτιδήποτε χρειαστείτε: {email}",
        "invalid_title": "Ο σύνδεσμος δεν ισχύει",
        "invalid_text": "Ο σύνδεσμος έχει αντικατασταθεί ή δεν είναι σωστός. Ζητήστε μας τον νέο σας σύνδεσμο.",
    },
    "en": {
        "title": "Your jobs",
        "hello": "Hello, {name}",
        "waiting": "Waiting for your approval",
        "review": "Review and approve",
        "open": "In progress",
        "done": "Recently completed",
        "statements": "Monthly statements",
        "download": "Download PDF",
        "due": "Due",
        "none": "Nothing at the moment.",
        "contact": "For anything you need: {email}",
        "invalid_title": "This link is not valid",
        "invalid_text": "The link has been replaced or is incorrect. Please ask us for your new link.",
    },
}

PAGE = """<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{title} – {brand}</title>
<style>
  body {{ margin:0; background:#f5f7f6; color:#17201c; font:16px/1.55 Arial, Helvetica, sans-serif; }}
  main {{ max-width:760px; margin:0 auto; padding:24px 16px 48px; }}
  h1 {{ font-size:1.4rem; margin:12px 0 4px; }} h2 {{ font-size:1.05rem; margin:0 0 10px; }}
  .card {{ background:#fff; border:1px solid #d7dfdb; border-radius:10px; padding:18px 20px; margin-top:16px; }}
  .muted {{ color:#5a6862; font-size:14px; }}
  ul {{ list-style:none; margin:0; padding:0; }}
  li {{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:6px 12px; padding:10px 0;
        border-top:1px solid #eef2f0; }}
  li:first-child {{ border-top:0; }}
  .ref {{ color:#5a6862; font-size:13px; margin-right:6px; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:13px; background:#eef2f0; }}
  .badge.wait {{ background:#fff4e5; color:#9a5b00; }} .badge.ok {{ background:#e3f3ea; color:#1f6f4a; }}
  a.button {{ display:inline-block; background:#1f6f4a; color:#fff; text-decoration:none; font-weight:bold;
              padding:8px 14px; border-radius:8px; font-size:14px; }}
  a {{ color:#1080bc; }}
</style></head>
<body><main>
<img src="{logo}" alt="{brand}" width="110">
{body}
</main></body></html>"""


def render(language, title, body):
    brand = get_brand()
    return HttpResponse(
        PAGE.format(lang=language, title=escape(title), brand=escape(brand["name"]), logo=escape(brand["logo_url"]), body=body)
    )


def client_status(issue, language):
    index = 0 if language == "el" else 1
    if not issue.state:
        return IN_PROGRESS[index]
    if issue.state.group == "completed":
        return CLIENT_STATES.get(issue.state.name, DONE)[index]
    return CLIENT_STATES.get(issue.state.name, IN_PROGRESS)[index]


def job_row(issue, language, t, extra=""):
    ref = f"{issue.project.identifier}-{issue.sequence_id}"
    due = f'<span class="muted">{t["due"]} {issue.target_date:%d/%m/%Y}</span>' if issue.target_date else ""
    return (
        f'<li><span><span class="ref">{escape(ref)}</span>{escape(issue.name)}</span>'
        f'<span>{due} {extra or escape(client_status(issue, language))}</span></li>'
    )


def section(title, rows, t):
    return f'<div class="card"><h2>{title}</h2><ul>{"".join(rows) or "<li class=muted>" + t["none"] + "</li>"}</ul></div>'


@require_GET
def client_portal(request, token):
    customer = customer_from_token(token)
    if not customer:
        t = TEXTS["el"]
        return render("el", t["invalid_title"], f'<div class="card"><h1>{t["invalid_title"]}</h1><p>{t["invalid_text"]}</p></div>')
    language = customer.language if customer.language in TEXTS else "el"
    t = TEXTS[language]

    links = (
        IssueCustomerService.objects.filter(customer=customer, issue__deleted_at__isnull=True, issue__archived_at__isnull=True)
        .select_related("issue", "issue__state", "issue__project")
    )
    issues = [link.issue for link in links if not link.issue.is_draft]

    # Approvals still waiting: the newest open request per item, while the item is still in that state
    waiting_rows, waiting_ids = [], set()
    open_requests = ApprovalRequest.objects.filter(
        issue__in=issues, responded_at__isnull=True, sent_at__isnull=False
    ).order_by("-created_at")
    for request_ in open_requests:
        issue = next(i for i in issues if i.id == request_.issue_id)
        if issue.id in waiting_ids or issue.state_id != request_.state_id:
            continue
        waiting_ids.add(issue.id)
        button = f'<a class="button" href="{escape(approval_url(request_))}">{t["review"]}</a>'
        waiting_rows.append(job_row(issue, language, t, button))

    open_rows = [
        job_row(issue, language, t)
        for issue in sorted(issues, key=lambda i: (i.target_date is None, i.target_date, i.sequence_id))
        if (not issue.state or issue.state.group not in ("completed", "cancelled")) and issue.id not in waiting_ids
    ]
    since = timezone.now() - timedelta(days=RECENT_DAYS)
    done_rows = [
        job_row(issue, language, t, f'<span class="badge ok">{escape(client_status(issue, language))}</span>')
        for issue in sorted(issues, key=lambda i: i.completed_at or since, reverse=True)
        if issue.state and issue.state.group == "completed" and issue.completed_at and issue.completed_at >= since
    ]
    statement_rows = [
        f'<li><span>{escape(month_label(statement.period, language))}</span>'
        f'<a href="{escape(request.path)}statement/{statement.id}/">{t["download"]}</a></li>'
        for statement in BillingStatement.objects.filter(customer=customer, status="sent").order_by("-period")[:24]
    ]

    brand = get_brand()
    contact = (
        f'<p class="muted">{t["contact"].format(email=escape(brand["support_email"]))}</p>' if brand["support_email"] else ""
    )
    body = (
        f'<h1>{escape(t["hello"].format(name=customer.name))}</h1>'
        f'<p class="muted">{timezone.now().astimezone(TZ):%d/%m/%Y %H:%M}</p>'
        + (section(t["waiting"], waiting_rows, t) if waiting_rows else "")
        + section(t["open"], open_rows, t)
        + section(t["done"], done_rows, t)
        + section(t["statements"], statement_rows, t)
        + contact
    )
    return render(language, t["title"], body)


@require_GET
def client_portal_statement(request, token, statement_id):
    customer = customer_from_token(token)
    statement = (
        BillingStatement.objects.filter(pk=statement_id, customer=customer, status="sent").first() if customer else None
    )
    if not statement or not statement.pdf_key:
        raise Http404
    response = HttpResponse(read_pdf(statement), content_type="application/pdf")
    # Customer names can be Greek: RFC 5987 filename
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(pdf_filename(statement))}"
    return response
