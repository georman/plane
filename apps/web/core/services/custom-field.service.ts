/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: custom fields API client.
 */

import { API_BASE_URL } from "@plane/constants";
import type { ICustomField, TCustomFieldValues } from "@plane/types";
import { APIService } from "@/services/api.service";

export class CustomFieldService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  private base(workspaceSlug: string, projectId: string) {
    return `/api/workspaces/${workspaceSlug}/projects/${projectId}`;
  }

  async fetchFields(workspaceSlug: string, projectId: string): Promise<ICustomField[]> {
    return this.get(`${this.base(workspaceSlug, projectId)}/custom-fields/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async createField(workspaceSlug: string, projectId: string, data: Partial<ICustomField>): Promise<ICustomField> {
    return this.post(`${this.base(workspaceSlug, projectId)}/custom-fields/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateField(
    workspaceSlug: string,
    projectId: string,
    fieldId: string,
    data: Partial<ICustomField>
  ): Promise<ICustomField> {
    return this.patch(`${this.base(workspaceSlug, projectId)}/custom-fields/${fieldId}/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteField(workspaceSlug: string, projectId: string, fieldId: string): Promise<void> {
    return this.delete(`${this.base(workspaceSlug, projectId)}/custom-fields/${fieldId}/`)
      .then(() => undefined)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async fetchValues(workspaceSlug: string, projectId: string, issueId: string): Promise<TCustomFieldValues> {
    return this.get(`${this.base(workspaceSlug, projectId)}/issues/${issueId}/custom-field-values/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateValues(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    values: TCustomFieldValues
  ): Promise<TCustomFieldValues> {
    return this.patch(`${this.base(workspaceSlug, projectId)}/issues/${issueId}/custom-field-values/`, values)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}

export const customFieldService = new CustomFieldService();
