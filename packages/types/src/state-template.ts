/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: state templates.
 */

export type TStateTemplateGroup = "backlog" | "unstarted" | "started" | "completed" | "cancelled";

export interface IStateTemplateItem {
  id: string;
  template_id: string;
  name: string;
  color: string;
  group: TStateTemplateGroup;
  sequence: number;
  default: boolean;
}

export interface IStateTemplate {
  id: string;
  workspace_id: string;
  name: string;
  // New projects start from this template unless another one is picked
  is_default: boolean;
  items: IStateTemplateItem[];
}

export interface IStateTemplateApplyResult {
  added: number;
  updated: number;
  removed: number;
  kept: string[];
}
