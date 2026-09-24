/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: Customer/Service billing types.
 */

// GAM: monthly services are one fixed line a month; per-job services are billed per completed item
export type TServiceBillingType = "per_job" | "monthly";

// GAM: language of everything the client receives
export type TCustomerLanguage = "el" | "en";

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
  billing_type: TServiceBillingType;
  is_active: boolean;
  template_items: IServiceTemplateItem[];
}

export interface ICustomerServiceRate {
  id: string;
  customer_id: string;
  service: string;
  service_name: string;
  service_billing_type: TServiceBillingType;
  price: string;
}

export interface ICustomer {
  id: string;
  workspace_id: string;
  name: string;
  contact_email: string;
  language: TCustomerLanguage;
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
