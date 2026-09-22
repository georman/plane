/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: admin "log in as member" feature.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export type TImpersonationStatus = {
  is_impersonating: boolean;
  impersonator_email?: string;
  target_user_email?: string;
  target_user_display_name?: string;
};

export class ImpersonationService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async impersonateMember(workspaceSlug: string, memberId: string): Promise<{ message: string }> {
    return this.post(`/api/workspaces/${workspaceSlug}/members/${memberId}/impersonate/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async stopImpersonating(): Promise<{ message: string }> {
    return this.post(`/auth/stop-impersonating/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async getImpersonationStatus(): Promise<TImpersonationStatus> {
    return this.get(`/auth/impersonation-status/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}

export const impersonationService = new ImpersonationService();
