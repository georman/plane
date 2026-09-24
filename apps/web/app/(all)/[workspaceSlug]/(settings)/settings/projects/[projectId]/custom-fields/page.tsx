/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: custom fields of a project's work items (project admins).
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { ArrowDown, ArrowUp, Trash2 } from "lucide-react";
import useSWR, { mutate } from "swr";
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
import { translate, useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { ICustomField, TCustomFieldType } from "@plane/types";
import { Input } from "@plane/ui";
// components
import { NotAuthorizedView } from "@/components/auth-screens/not-authorized-view";
import { PageHead } from "@/components/core/page-title";
import { SettingsContentWrapper } from "@/components/settings/content-wrapper";
import { SettingsHeading } from "@/components/settings/heading";
// hooks
import { useProject } from "@/hooks/store/use-project";
import { useUserPermissions } from "@/hooks/store/user";
// services
import { customFieldService } from "@/services/custom-field.service";
// local
import type { Route } from "./+types/page";
import { CustomFieldsProjectSettingsHeader } from "./header";

const TYPES: TCustomFieldType[] = ["text", "number", "date", "select", "checkbox"];
const fieldsKey = (projectId: string) => `GAM_CUSTOM_FIELDS_${projectId}`;
const showError = (error: any, fallback: string) =>
  setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? error?.name?.[0] ?? fallback });

function TypeSelect({ value, onChange }: { value: TCustomFieldType; onChange: (type: TCustomFieldType) => void }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as TCustomFieldType)}
      className="rounded-sm border border-subtle bg-surface-1 px-2 py-1.5 text-13"
      aria-label={translate("gam.cf.type")}
    >
      {TYPES.map((type) => (
        <option key={type} value={type}>
          {translate(`gam.cf.types.${type}`)}
        </option>
      ))}
    </select>
  );
}

function FieldRow({
  slug,
  projectId,
  field,
  index,
  fields,
}: {
  slug: string;
  projectId: string;
  field: ICustomField;
  index: number;
  fields: ICustomField[];
}) {
  const refresh = () => mutate(fieldsKey(projectId));
  const update = async (data: Partial<ICustomField>) => {
    try {
      await customFieldService.updateField(slug, projectId, field.id, data);
      refresh();
    } catch (error: any) {
      showError(error, translate("gam.error_generic"));
    }
  };
  const move = async (direction: -1 | 1) => {
    const neighbour = fields[index + direction];
    if (!neighbour) return;
    try {
      await Promise.all([
        customFieldService.updateField(slug, projectId, field.id, { sequence: neighbour.sequence }),
        customFieldService.updateField(slug, projectId, neighbour.id, { sequence: field.sequence }),
      ]);
      refresh();
    } catch (error: any) {
      showError(error, translate("gam.error_generic"));
    }
  };
  const remove = async () => {
    if (!window.confirm(translate("gam.cf.delete_confirm", { name: field.name }))) return;
    try {
      await customFieldService.deleteField(slug, projectId, field.id);
      refresh();
    } catch (error: any) {
      showError(error, translate("gam.error_generic"));
    }
  };

  return (
    <div className="flex flex-col gap-2 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          key={`${field.id}-${field.name}`}
          defaultValue={field.name}
          onBlur={(e) => {
            const name = e.target.value.trim();
            if (name && name !== field.name) update({ name });
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          }}
          className="min-w-40 flex-1"
          aria-label={translate("gam.cf.name")}
        />
        <TypeSelect value={field.field_type} onChange={(field_type) => update({ field_type })} />
        <button
          type="button"
          onClick={() => move(-1)}
          disabled={index === 0}
          className="text-tertiary hover:text-primary disabled:opacity-30"
          aria-label="Move up"
        >
          <ArrowUp className="size-4" />
        </button>
        <button
          type="button"
          onClick={() => move(1)}
          disabled={index === fields.length - 1}
          className="text-tertiary hover:text-primary disabled:opacity-30"
          aria-label="Move down"
        >
          <ArrowDown className="size-4" />
        </button>
        <button type="button" onClick={remove} className="text-tertiary hover:text-danger-primary" aria-label="Delete">
          <Trash2 className="size-4" />
        </button>
      </div>
      {field.field_type === "select" && (
        <Input
          key={`${field.id}-options-${field.options.join("|")}`}
          defaultValue={field.options.join(", ")}
          onBlur={(e) => {
            const options = e.target.value
              .split(",")
              .map((option) => option.trim())
              .filter(Boolean);
            if (options.join("|") !== field.options.join("|")) update({ options });
          }}
          placeholder={translate("gam.cf.options_placeholder")}
          className="w-full"
          aria-label={translate("gam.cf.options")}
        />
      )}
    </div>
  );
}

function CustomFieldsSettingsPage({ params }: Route.ComponentProps) {
  const { workspaceSlug: slug, projectId } = params;
  const { t } = useTranslation();
  const { currentProjectDetails } = useProject();
  const { workspaceUserInfo, allowPermissions } = useUserPermissions();
  const [name, setName] = useState("");
  const [fieldType, setFieldType] = useState<TCustomFieldType>("text");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isAdmin = allowPermissions([EUserPermissions.ADMIN], EUserPermissionsLevel.PROJECT);
  const { data: fields } = useSWR(isAdmin ? fieldsKey(projectId) : null, () =>
    customFieldService.fetchFields(slug, projectId)
  );

  if (workspaceUserInfo && !isAdmin) {
    return <NotAuthorizedView section="settings" isProjectView className="h-auto" />;
  }

  const handleCreate = async () => {
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await customFieldService.createField(slug, projectId, { name: name.trim(), field_type: fieldType });
      setName("");
      mutate(fieldsKey(projectId));
    } catch (error: any) {
      showError(error, translate("gam.error_generic"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SettingsContentWrapper header={<CustomFieldsProjectSettingsHeader />}>
      <PageHead title={currentProjectDetails?.name ? `${currentProjectDetails.name} - ${t("gam.cf.title")}` : undefined} />
      <div className="w-full">
        <SettingsHeading title={t("gam.cf.title")} description={t("gam.cf.description")} />
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
            }}
            placeholder={translate("gam.cf.name_placeholder")}
            className="w-full sm:w-72"
          />
          <TypeSelect value={fieldType} onChange={setFieldType} />
          <Button variant="primary" onClick={handleCreate} disabled={isSubmitting || !name.trim()}>
            {translate("gam.cf.add")}
          </Button>
        </div>
        <div className="mt-6 divide-y divide-subtle border-t border-subtle">
          {fields?.length ? (
            fields.map((field, index) => (
              <FieldRow key={field.id} slug={slug} projectId={projectId} field={field} index={index} fields={fields} />
            ))
          ) : (
            <p className="py-6 text-14 text-tertiary">{translate("gam.cf.none")}</p>
          )}
        </div>
      </div>
    </SettingsContentWrapper>
  );
}

export default observer(CustomFieldsSettingsPage);
