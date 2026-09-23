# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: build monthly billing statements by hand (they normally run
# on the 1st of the month). Drafts go to GAM's review address, never to clients.
#   python manage.py gam_billing --month 2026-09 [--customer "Name"]

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from plane.bgtasks.gam_billing_task import generate_statement, previous_month
from plane.db.models import Customer


class Command(BaseCommand):
    help = "Build monthly billing statements and email them to GAM for review"

    def add_arguments(self, parser):
        parser.add_argument("--month", help="YYYY-MM (default: last month)")
        parser.add_argument("--customer", help="Customer name (default: all active customers)")

    def handle(self, *args, **options):
        try:
            period = date.fromisoformat(f"{options['month']}-01") if options["month"] else previous_month()
        except ValueError:
            raise CommandError("--month must look like 2026-09")
        customers = Customer.objects.filter(is_active=True)
        if options["customer"]:
            customers = customers.filter(name=options["customer"])
        for customer in customers:
            statement = generate_statement(customer, period)
            self.stdout.write(f"{customer.name}: {len(statement.lines)} lines, total {statement.total} ({statement.status})")
