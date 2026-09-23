/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: Customer/Service billing API client.
 */

import { API_BASE_URL } from "@plane/constants";
import type { ICustomer, ICustomerServiceRate, IIssueCustomerService, IService } from "@plane/types";
import { APIService } from "@/services/api.service";

export class BillingService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async fetchServices(workspaceSlug: string): Promise<IService[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/services/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async createService(workspaceSlug: string, data: Partial<IService>): Promise<IService> {
    return this.post(`/api/workspaces/${workspaceSlug}/services/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateService(workspaceSlug: string, serviceId: string, data: Partial<IService>): Promise<IService> {
    return this.patch(`/api/workspaces/${workspaceSlug}/services/${serviceId}/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteService(workspaceSlug: string, serviceId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/services/${serviceId}/`).catch((error) => {
      throw error?.response?.data;
    });
  }

  async fetchCustomers(workspaceSlug: string): Promise<ICustomer[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/customers/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async createCustomer(workspaceSlug: string, data: Partial<ICustomer>): Promise<ICustomer> {
    return this.post(`/api/workspaces/${workspaceSlug}/customers/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateCustomer(workspaceSlug: string, customerId: string, data: Partial<ICustomer>): Promise<ICustomer> {
    return this.patch(`/api/workspaces/${workspaceSlug}/customers/${customerId}/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteCustomer(workspaceSlug: string, customerId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/customers/${customerId}/`).catch((error) => {
      throw error?.response?.data;
    });
  }

  async createCustomerRate(
    workspaceSlug: string,
    customerId: string,
    data: { service: string; price: string }
  ): Promise<ICustomerServiceRate> {
    return this.post(`/api/workspaces/${workspaceSlug}/customers/${customerId}/rates/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateCustomerRate(
    workspaceSlug: string,
    customerId: string,
    rateId: string,
    data: { price: string }
  ): Promise<ICustomerServiceRate> {
    return this.patch(`/api/workspaces/${workspaceSlug}/customers/${customerId}/rates/${rateId}/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteCustomerRate(workspaceSlug: string, customerId: string, rateId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/customers/${customerId}/rates/${rateId}/`).catch(
      (error) => {
        throw error?.response?.data;
      }
    );
  }

  async fetchIssueCustomerService(
    workspaceSlug: string,
    projectId: string,
    issueId: string
  ): Promise<IIssueCustomerService | null> {
    return this.get(`/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/customer-service/`)
      .then((response) => response?.data ?? null)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async setIssueCustomerService(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    data: { customer: string; service: string }
  ): Promise<IIssueCustomerService> {
    return this.put(`/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/customer-service/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}

export const billingService = new BillingService();
