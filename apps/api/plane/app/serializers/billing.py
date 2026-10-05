# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: serializers for the Customer/Service billing system.

from rest_framework import serializers

from plane.db.models import Customer, CustomerServiceRate, IssueCustomerService, Project, Service, ServiceTemplateItem

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
        fields = ["id", "workspace_id", "name", "billing_type", "is_active", "template_items"]
        read_only_fields = ["workspace"]


class CustomerServiceRateSerializer(BaseSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_billing_type = serializers.CharField(source="service.billing_type", read_only=True)

    class Meta:
        model = CustomerServiceRate
        fields = ["id", "customer_id", "service", "service_name", "service_billing_type", "price"]
        read_only_fields = ["customer"]


class CustomerSerializer(BaseSerializer):
    rates = CustomerServiceRateSerializer(many=True, read_only=True)
    # Projects whose work is done for this customer (a project has at most one customer)
    project_ids = serializers.PrimaryKeyRelatedField(
        source="projects", many=True, required=False, queryset=Project.objects.all()
    )

    def validate_project_ids(self, projects):
        workspace_id = self.instance.workspace_id if self.instance else self.context.get("workspace_id")
        if any(str(project.workspace_id) != str(workspace_id) for project in projects):
            raise serializers.ValidationError("Project not found in this workspace.")
        return projects

    def _set_projects(self, customer, projects):
        # Projects removed from the list are unlinked; the ones added move over
        # from whichever customer they had before.
        Project.objects.filter(customer=customer).exclude(id__in=[p.id for p in projects]).update(customer=None)
        Project.objects.filter(id__in=[p.id for p in projects]).update(customer=customer)
        # the response should show the new list, not the one prefetched before saving
        getattr(customer, "_prefetched_objects_cache", {}).pop("projects", None)
        from plane.utils.gam_service_labels import ensure_service_labels

        ensure_service_labels(customer)

    def create(self, validated_data):
        projects = validated_data.pop("projects", None)
        customer = super().create(validated_data)
        if projects is not None:
            self._set_projects(customer, projects)
        return customer

    def update(self, instance, validated_data):
        projects = validated_data.pop("projects", None)
        customer = super().update(instance, validated_data)
        if projects is not None:
            self._set_projects(customer, projects)
        return customer

    class Meta:
        model = Customer
        fields = [
            "id",
            "workspace_id",
            "name",
            "contact_email",
            "language",
            "is_active",
            "rates",
            "project_ids",
        ]
        read_only_fields = ["workspace"]


class IssueCustomerServiceSerializer(BaseSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = IssueCustomerService
        fields = ["id", "issue", "customer", "customer_name", "service", "service_name"]
        read_only_fields = ["issue"]
