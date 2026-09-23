# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: admin screens for the Customer/Service billing system -
# add/remove Services, add/remove Customers, and set the agreed price per
# (customer, service). Workspace-admin only, this is financial config data.

from django.db import IntegrityError

from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.serializers import (
    CustomerSerializer,
    CustomerServiceRateSerializer,
    IssueCustomerServiceSerializer,
    ServiceSerializer,
    ServiceTemplateItemSerializer,
)
from plane.db.models import (
    Customer,
    CustomerServiceRate,
    Issue,
    IssueCustomerService,
    Service,
    ServiceTemplateItem,
    Workspace,
)

from .base import BaseAPIView, BaseViewSet


class ServiceViewSet(BaseViewSet):
    serializer_class = ServiceSerializer
    model = Service

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("slug"))
            .prefetch_related("template_items")
            .order_by("name")
        )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def list(self, request, slug):
        services = self.get_queryset()
        return Response(ServiceSerializer(services, many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def create(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        try:
            serializer = ServiceSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(workspace_id=workspace.id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"error": "A service with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def partial_update(self, request, *args, **kwargs):
        serializer = ServiceSerializer(instance=self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CustomerViewSet(BaseViewSet):
    serializer_class = CustomerSerializer
    model = Customer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("slug"))
            .prefetch_related("rates", "rates__service")
            .order_by("name")
        )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def list(self, request, slug):
        customers = self.get_queryset()
        return Response(CustomerSerializer(customers, many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def retrieve(self, request, slug, pk):
        customer = self.get_queryset().get(pk=pk)
        return Response(CustomerSerializer(customer).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def create(self, request, slug):
        workspace = Workspace.objects.get(slug=slug)
        try:
            serializer = CustomerSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(workspace_id=workspace.id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"error": "A customer with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def partial_update(self, request, *args, **kwargs):
        serializer = CustomerSerializer(instance=self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CustomerServiceRateViewSet(BaseViewSet):
    """Nested under a Customer: the price they pay for each service."""

    serializer_class = CustomerServiceRateSerializer
    model = CustomerServiceRate

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(customer__workspace__slug=self.kwargs.get("slug"))
            .filter(customer_id=self.kwargs.get("customer_id"))
            .select_related("service")
            .order_by("service__name")
        )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def list(self, request, slug, customer_id):
        rates = self.get_queryset()
        return Response(CustomerServiceRateSerializer(rates, many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def create(self, request, slug, customer_id):
        try:
            serializer = CustomerServiceRateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(customer_id=customer_id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response(
                {"error": "This customer already has a rate set for that service - edit it instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def partial_update(self, request, *args, **kwargs):
        serializer = CustomerServiceRateSerializer(
            instance=self.get_object(), data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ServiceTemplateItemViewSet(BaseViewSet):
    """Nested under a Service: the checklist steps created as sub-items of new work items."""

    serializer_class = ServiceTemplateItemSerializer
    model = ServiceTemplateItem

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(service__workspace__slug=self.kwargs.get("slug"))
            .filter(service_id=self.kwargs.get("service_id"))
            .order_by("sequence", "created_at")
        )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def list(self, request, slug, service_id):
        items = self.get_queryset()
        return Response(ServiceTemplateItemSerializer(items, many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def create(self, request, slug, service_id):
        service = Service.objects.get(pk=service_id, workspace__slug=slug)
        serializer = ServiceTemplateItemSerializer(data=request.data)
        if serializer.is_valid():
            if "sequence" not in request.data:
                last = self.get_queryset().order_by("-sequence").first()
                serializer.save(service=service, sequence=(last.sequence + 10000) if last else 10000)
            else:
                serializer.save(service=service)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def partial_update(self, request, *args, **kwargs):
        serializer = ServiceTemplateItemSerializer(instance=self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


def create_service_sub_items(issue, service_id, user):
    """Create the service's checklist steps as sub-items, unless the item already has sub-items."""
    if Issue.issue_objects.filter(parent=issue).exists():
        return
    for step in ServiceTemplateItem.objects.filter(service_id=service_id).order_by("sequence", "created_at"):
        Issue(
            name=step.name,
            parent=issue,
            project_id=issue.project_id,
            workspace_id=issue.workspace_id,
            created_by=user,
        ).save()


class IssueCustomerServiceEndpoint(BaseAPIView):
    """Which customer + service a specific work item is for. One per issue (upsert)."""

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="PROJECT")
    def get(self, request, slug, project_id, issue_id):
        link = IssueCustomerService.objects.filter(
            issue_id=issue_id, issue__project_id=project_id, issue__workspace__slug=slug
        ).first()
        if not link:
            return Response(None, status=status.HTTP_200_OK)
        return Response(IssueCustomerServiceSerializer(link).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="PROJECT")
    def put(self, request, slug, project_id, issue_id):
        customer_id = request.data.get("customer")
        service_id = request.data.get("service")
        if not customer_id or not service_id:
            return Response(
                {"error": "Both customer and service are required."}, status=status.HTTP_400_BAD_REQUEST
            )
        issue = Issue.objects.get(pk=issue_id, project_id=project_id, workspace__slug=slug)
        previous_service_id = (
            IssueCustomerService.objects.filter(issue=issue).values_list("service_id", flat=True).first()
        )
        link, _ = IssueCustomerService.objects.update_or_create(
            issue=issue, defaults={"customer_id": customer_id, "service_id": service_id}
        )
        if str(previous_service_id) != str(service_id):
            create_service_sub_items(issue, service_id, request.user)
        return Response(IssueCustomerServiceSerializer(link).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="PROJECT")
    def delete(self, request, slug, project_id, issue_id):
        IssueCustomerService.objects.filter(
            issue_id=issue_id, issue__project_id=project_id, issue__workspace__slug=slug
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
