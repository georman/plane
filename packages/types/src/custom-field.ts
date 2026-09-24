/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: custom fields on work items.
 */

export type TCustomFieldType = "text" | "number" | "date" | "select" | "checkbox";

export interface ICustomField {
  id: string;
  project_id: string;
  name: string;
  field_type: TCustomFieldType;
  options: string[];
  sequence: number;
}

/** A work item's values by field id ("" = empty; checkboxes are "true" or "") */
export type TCustomFieldValues = Record<string, string>;
