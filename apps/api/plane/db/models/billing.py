# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: a workspace-wide Customer/Service/rate system for monthly
# billing. Plane CE has no custom-fields system and Labels/Modules are
# project-scoped, so client identity, service type, and agreed price
# couldn't be tracked consistently across projects - these models fill
# that gap. See plane_stack.md memory for the full billing model
# (retainer vs per-job customers).

from django.db import models

from .base import BaseModel


class Service(BaseModel):
    """A type of billable work (Design, CTP, SEO, IG Posts, ...). Workspace-wide."""

    workspace = models.ForeignKey(
        "db.Workspace", on_delete=models.CASCADE, related_name="services"
    )
    name = models.CharField(max_length=255)
    # Monthly services are billed as one fixed line per month (the customer's
    # price); per-job services are billed once for every completed work item.
    BILLING_TYPE_CHOICES = (
        ("per_job", "Per job"),
        ("monthly", "Monthly"),
    )
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, default="per_job")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "gam_services"
        verbose_name = "Service"
        verbose_name_plural = "Services"
        unique_together = ("workspace", "name")
        ordering = ("name",)

    def __str__(self):
        return self.name


class Customer(BaseModel):
    """A GAM client. Workspace-wide, independent of which project(s) their work lives in."""

    workspace = models.ForeignKey(
        "db.Workspace", on_delete=models.CASCADE, related_name="customers"
    )
    name = models.CharField(max_length=255)
    contact_email = models.CharField(max_length=255, blank=True)
    # Language of everything the client receives (emails, approval page, billing PDF)
    LANGUAGE_CHOICES = (("el", "Ελληνικά"), ("en", "English"))
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default="el")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "gam_customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        unique_together = ("workspace", "name")
        ordering = ("name",)

    def __str__(self):
        return self.name


class CustomerServiceRate(BaseModel):
    """The agreed price for one (customer, service) pair.

    For a monthly service this is a flat amount per month (e.g. Acme /
    IG Posts / EUR 300). For a per-job service it's the price per completed
    work item (e.g. Globex / Design / EUR 100).
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="rates"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="rates"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "gam_customer_service_rates"
        verbose_name = "Customer Service Rate"
        verbose_name_plural = "Customer Service Rates"
        unique_together = ("customer", "service")
        ordering = ("customer__name", "service__name")

    def __str__(self):
        return f"{self.customer.name} / {self.service.name}: {self.price}"


class IssueCustomerService(BaseModel):
    """Links a work item to the customer it was done for and the service it is."""

    issue = models.OneToOneField(
        "db.Issue", on_delete=models.CASCADE, related_name="customer_service"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="issues"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="issues"
    )

    class Meta:
        db_table = "gam_issue_customer_service"
        verbose_name = "Issue Customer/Service"
        verbose_name_plural = "Issue Customer/Services"

    def __str__(self):
        return f"{self.issue_id}: {self.customer.name} / {self.service.name}"


class ServiceTemplateItem(BaseModel):
    """One checklist step of a service (e.g. Logo: Brief, Sketches, 4 proposals, ...).

    When a work item is first linked to a service, each active step is created
    as a sub-item of it, in sequence order.
    """

    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="template_items"
    )
    name = models.CharField(max_length=255)
    sequence = models.FloatField(default=65535)

    class Meta:
        db_table = "gam_service_template_items"
        verbose_name = "Service Template Item"
        verbose_name_plural = "Service Template Items"
        ordering = ("sequence", "created_at")

    def __str__(self):
        return f"{self.service.name}: {self.name}"


class BillingStatement(BaseModel):
    """A customer's monthly statement. Drafts are emailed to GAM for review and
    only reach the client after someone presses "Approve & send"."""

    STATUS_CHOICES = (("draft", "Draft, waiting for review"), ("sent", "Sent to client"))

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="statements")
    period = models.DateField(help_text="First day of the billed month")
    lines = models.JSONField(default=list)
    deliverables = models.JSONField(default=list)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    language = models.CharField(max_length=5, default="el")
    pdf_key = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    token_version = models.PositiveIntegerField(default=1)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_to = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "gam_billing_statements"
        verbose_name = "Billing Statement"
        verbose_name_plural = "Billing Statements"
        unique_together = ("customer", "period")
        ordering = ("-period", "customer__name")

    def __str__(self):
        return f"{self.customer.name} {self.period:%Y-%m}: {self.total}"
