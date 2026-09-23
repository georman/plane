# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: serializers for the Customer/Service billing system.

from rest_framework import serializers

from plane.db.models import Customer, CustomerServiceRate, IssueCustomerService, Service, ServiceTemplateItem

from .base import BaseSerializer


class ServiceTemplateItemSerializer(BaseSerializer):
    class Meta:
        model = ServiceTemplateItem
        fields = ["id", "service_id", "name", "sequence"]
        read_only_fields = ["service"]


class ServiceSerializer(BaseSerializer):
    template_items = ServiceTemplateItemSerializer(many=True, read_only=True)

    class Meta:
        model = Service
        fields = ["id", "workspace_id", "name", "is_active", "template_items"]
        read_only_fields = ["workspace"]


class CustomerServiceRateSerializer(BaseSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = CustomerServiceRate
        fields = ["id", "customer_id", "service", "service_name", "price"]
        read_only_fields = ["customer"]


class CustomerSerializer(BaseSerializer):
    rates = CustomerServiceRateSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "workspace_id",
            "name",
            "contact_email",
            "billing_type",
            "is_active",
            "rates",
        ]
        read_only_fields = ["workspace"]


class IssueCustomerServiceSerializer(BaseSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = IssueCustomerService
        fields = ["id", "issue", "customer", "customer_name", "service", "service_name"]
        read_only_fields = ["issue"]
