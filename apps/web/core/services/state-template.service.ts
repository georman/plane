/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: state templates API client.
 */

import { API_BASE_URL } from "@plane/constants";
import type { IStateTemplate, IStateTemplateApplyResult, IStateTemplateItem } from "@plane/types";
import { APIService } from "@/services/api.service";

export class StateTemplateService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async fetchTemplates(workspaceSlug: string): Promise<IStateTemplate[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/state-templates/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async createTemplate(workspaceSlug: string, data: Partial<IStateTemplate>): Promise<IStateTemplate> {
    return this.post(`/api/workspaces/${workspaceSlug}/state-templates/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateTemplate(workspaceSlug: string, templateId: string, data: Partial<IStateTemplate>): Promise<IStateTemplate> {
    return this.patch(`/api/workspaces/${workspaceSlug}/state-templates/${templateId}/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteTemplate(workspaceSlug: string, templateId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/state-templates/${templateId}/`).then(() => undefined).catch((error) => {
      throw error?.response?.data;
    });
  }

  async createItem(workspaceSlug: string, templateId: string, data: Partial<IStateTemplateItem>): Promise<IStateTemplateItem> {
    return this.post(`/api/workspaces/${workspaceSlug}/state-templates/${templateId}/items/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateItem(
    workspaceSlug: string,
    templateId: string,
    itemId: string,
    data: Partial<IStateTemplateItem>
  ): Promise<IStateTemplateItem> {
    return this.patch(`/api/workspaces/${workspaceSlug}/state-templates/${templateId}/items/${itemId}/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteItem(workspaceSlug: string, templateId: string, itemId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/state-templates/${templateId}/items/${itemId}/`).then(() => undefined).catch(
      (error) => {
        throw error?.response?.data;
      }
    );
  }

  async applyToProject(workspaceSlug: string, projectId: string, templateId: string): Promise<IStateTemplateApplyResult> {
    return this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/state-template/`, { template: templateId })
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}

export const stateTemplateService = new StateTemplateService();
