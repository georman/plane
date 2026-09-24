/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: the project's custom fields on a work item (properties panel).
 */

import { ListPlus } from "lucide-react";
import useSWR from "swr";
import { translate } from "@plane/i18n";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { ICustomField, TCustomFieldValues } from "@plane/types";
import { SidebarPropertyListItem } from "@/components/common/layout/sidebar/property-list-item";
import { customFieldService } from "@/services/custom-field.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
  disabled: boolean;
};

const inputClass =
  "h-7 w-full rounded-sm border border-transparent bg-transparent px-2 text-body-xs-regular hover:border-subtle focus:border-subtle focus:outline-none disabled:cursor-not-allowed";

export function IssueCustomFields({ workspaceSlug, projectId, issueId, disabled }: Props) {
  const { data: fields } = useSWR(`GAM_CUSTOM_FIELDS_${projectId}`, () =>
    customFieldService.fetchFields(workspaceSlug, projectId)
  );
  const valuesKey = fields?.length ? `GAM_CUSTOM_FIELD_VALUES_${issueId}` : null;
  const { data: values, mutate } = useSWR(valuesKey, () =>
    customFieldService.fetchValues(workspaceSlug, projectId, issueId)
  );

  if (!fields?.length) return null;

  const save = async (field: ICustomField, value: string) => {
    if ((values?.[field.id] ?? "") === value) return;
    try {
      const updated = await customFieldService.updateValues(workspaceSlug, projectId, issueId, { [field.id]: value });
      mutate(updated as TCustomFieldValues, false);
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Error", message: error?.error ?? "Could not save the value." });
      mutate();
    }
  };

  const renderInput = (field: ICustomField) => {
    const value = values?.[field.id] ?? "";
    const blurSave = (e: React.FocusEvent<HTMLInputElement>) => save(field, e.target.value.trim());
    const enterBlurs = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") (e.target as HTMLInputElement).blur();
    };
    switch (field.field_type) {
      case "checkbox":
        return (
          <input
            type="checkbox"
            checked={value === "true"}
            disabled={disabled}
            onChange={(e) => save(field, e.target.checked ? "true" : "")}
            className="ml-2 size-4"
            aria-label={field.name}
          />
        );
      case "select":
        return (
          <select
            value={value}
            disabled={disabled}
            onChange={(e) => save(field, e.target.value)}
            className={inputClass}
            aria-label={field.name}
          >
            <option value="">{translate("gam.cf.empty")}</option>
            {field.options.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      default:
        return (
          <input
            // Remount when the saved value changes so the field shows it
            key={`${field.id}-${value}`}
            type={field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : "text"}
            step={field.field_type === "number" ? "any" : undefined}
            defaultValue={value}
            disabled={disabled}
            onBlur={blurSave}
            onKeyDown={enterBlurs}
            placeholder={translate("gam.cf.empty")}
            className={inputClass}
            aria-label={field.name}
          />
        );
    }
  };

  return (
    <>
      {fields.map((field) => (
        <SidebarPropertyListItem key={field.id} icon={ListPlus} label={field.name}>
          {renderInput(field)}
        </SidebarPropertyListItem>
      ))}
    </>
  );
}
