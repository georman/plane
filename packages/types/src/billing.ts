/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: Customer/Service billing types.
 */

export type TCustomerBillingType = "retainer" | "per_job";

export interface IServiceTemplateItem {
  id: string;
  service_id: string;
  name: string;
  sequence: number;
}

export interface IService {
  id: string;
  workspace_id: string;
  name: string;
  is_active: boolean;
  template_items: IServiceTemplateItem[];
}

export interface ICustomerServiceRate {
  id: string;
  customer_id: string;
  service: string;
  service_name: string;
  price: string;
}

export interface ICustomer {
  id: string;
  workspace_id: string;
  name: string;
  contact_email: string;
  billing_type: TCustomerBillingType;
  is_active: boolean;
  rates: ICustomerServiceRate[];
}

export interface IIssueCustomerService {
  id: string;
  issue: string;
  customer: string;
  customer_name: string;
  service: string;
  service_name: string;
}

// GAM addition: repeating work items
export type TIssueRecurrenceFrequency = "weekly" | "monthly" | "yearly";

export interface IIssueRecurrence {
  id: string;
  issue: string;
  frequency: TIssueRecurrenceFrequency;
  next_run_date: string;
}
