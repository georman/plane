/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: State templates settings page - ready-made sets of states
 * that a project can start from (project create) or have applied later
 * (project settings → States).
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { ArrowDown, ArrowUp, ChevronDown, ChevronRight, Star, Trash2 } from "lucide-react";
import useSWR, { mutate } from "swr";
// plane imports
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
import { stateDisplayName, translate, useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IStateTemplate, IStateTemplateItem, TStateTemplateGroup } from "@plane/types";
import { Input } from "@plane/ui";
// components
import { NotAuthorizedView } from "@/components/auth-screens/not-authorized-view";
import { PageHead } from "@/components/core/page-title";
import { SettingsContentWrapper } from "@/components/settings/content-wrapper";
import { SettingsHeading } from "@/components/settings/heading";
// hooks
import { useUserPermissions } from "@/hooks/store/user";
import { useWorkspace } from "@/hooks/store/use-workspace";
// services
import { stateTemplateService } from "@/services/state-template.service";
// local
import { StateTemplatesWorkspaceSettingsHeader } from "./header";

const STATE_TEMPLATES_SWR_KEY = (slug: string) => `GAM_STATE_TEMPLATES_${slug}`;

const GROUPS: TStateTemplateGroup[] = ["backlog", "unstarted", "started", "completed", "cancelled"];

const showError = (error: any, fallback: string) =>
  setToast({ type: TOAST_TYPE.ERROR, title: "Error", message: error?.error ?? fallback });

function GroupSelect({
  value,
  onChange,
  className = "",
}: {
  value: TStateTemplateGroup;
  onChange: (group: TStateTemplateGroup) => void;
  className?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as TStateTemplateGroup)}
      className={`rounded-sm border border-subtle bg-surface-1 px-2 py-1.5 text-13 ${className}`}
      aria-label={translate("gam.st.group")}
    >
      {GROUPS.map((group) => (
        <option key={group} value={group}>
          {translate(`gam.state_group.${group}`)}
        </option>
      ))}
    </select>
  );
}

const TemplateRow = observer(function TemplateRow({
  slug,
  template,
  onDelete,
}: {
  slug: string;
  template: IStateTemplate;
  onDelete: (templateId: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState(template.name);
  const [newItemName, setNewItemName] = useState("");
  const [newItemGroup, setNewItemGroup] = useState<TStateTemplateGroup>("started");
  const items = [...template.items].sort((a, b) => a.sequence - b.sequence);
  const refresh = () => mutate(STATE_TEMPLATES_SWR_KEY(slug));

  const handleRename = async () => {
    const trimmed = name.trim();
    if (!trimmed || trimmed === template.name) return setName(template.name);
    try {
      await stateTemplateService.updateTemplate(slug, template.id, { name: trimmed });
      refresh();
    } catch (error: any) {
      setName(template.name);
      showError(error, "Could not rename the template.");
    }
  };

  const updateItem = async (item: IStateTemplateItem, data: Partial<IStateTemplateItem>) => {
    try {
      await stateTemplateService.updateItem(slug, template.id, item.id, data);
      refresh();
    } catch (error: any) {
      showError(error, "Could not update the state.");
    }
  };

  const handleMove = async (index: number, direction: -1 | 1) => {
    const current = items[index];
    const neighbour = items[index + direction];
    if (!current || !neighbour) return;
    try {
      await Promise.all([
        stateTemplateService.updateItem(slug, template.id, current.id, { sequence: neighbour.sequence }),
        stateTemplateService.updateItem(slug, template.id, neighbour.id, { sequence: current.sequence }),
      ]);
      refresh();
    } catch (error: any) {
      showError(error, "Could not reorder the states.");
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    try {
      await stateTemplateService.deleteItem(slug, template.id, itemId);
      refresh();
    } catch (error: any) {
      showError(error, "Could not delete the state.");
    }
  };

  const handleAddItem = async () => {
    const trimmed = newItemName.trim();
    if (!trimmed) return;
    try {
      await stateTemplateService.createItem(slug, template.id, {
        name: trimmed,
        group: newItemGroup,
        default: items.length === 0,
      });
      setNewItemName("");
      refresh();
    } catch (error: any) {
      showError(error, "Could not add the state.");
    }
  };

  return (
    <div className="py-3">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-tertiary hover:text-primary"
          aria-label={isOpen ? `Hide ${template.name}` : `Show ${template.name}`}
          aria-expanded={isOpen}
        >
          {isOpen ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
        </button>
        <Input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={handleRename}
          onKeyDown={(e) => {
            if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          }}
          className="flex-1 border-transparent hover:border-subtle"
          aria-label={translate("gam.st.template_name")}
        />
        <span className="shrink-0 text-12 text-tertiary">{translate("gam.st.states", { count: items.length })}</span>
        <button
          type="button"
          onClick={() => onDelete(template.id)}
          className="text-tertiary hover:text-danger-primary"
          aria-label={`Delete ${template.name}`}
        >
          <Trash2 className="size-4" />
        </button>
      </div>
      {isOpen && (
        <div className="mt-3 ml-6 flex flex-col gap-2">
          <p className="text-12 text-tertiary">{translate("gam.st.items_hint")}</p>
          {items.map((item, index) => (
            <div key={item.id} className="flex flex-wrap items-center gap-2">
              <input
                type="color"
                defaultValue={item.color}
                onBlur={(e) => {
                  if (e.target.value !== item.color) updateItem(item, { color: e.target.value });
                }}
                className="size-7 shrink-0 cursor-pointer rounded-sm border border-subtle bg-transparent"
                aria-label={translate("gam.st.color")}
              />
              <Input
                type="text"
                defaultValue={item.name}
                onBlur={(e) => {
                  const trimmed = e.target.value.trim();
                  if (trimmed && trimmed !== item.name) updateItem(item, { name: trimmed });
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                }}
                className="min-w-40 flex-1"
                aria-label={translate("gam.st.state_name")}
                title={stateDisplayName(item.name)}
              />
              <GroupSelect value={item.group} onChange={(group) => updateItem(item, { group })} />
              <button
                type="button"
                onClick={() => !item.default && updateItem(item, { default: true })}
                className={item.default ? "text-accent-primary" : "text-tertiary hover:text-primary"}
                aria-label={translate("gam.st.default")}
                title={translate("gam.st.default")}
              >
                <Star className="size-4" fill={item.default ? "currentColor" : "none"} />
              </button>
              <button
                type="button"
                onClick={() => handleMove(index, -1)}
                disabled={index === 0}
                className="text-tertiary hover:text-primary disabled:opacity-30"
                aria-label="Move up"
              >
                <ArrowUp className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => handleMove(index, 1)}
                disabled={index === items.length - 1}
                className="text-tertiary hover:text-primary disabled:opacity-30"
                aria-label="Move down"
              >
                <ArrowDown className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => handleDeleteItem(item.id)}
                className="text-tertiary hover:text-danger-primary"
                aria-label={`Delete ${item.name}`}
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          ))}
          <div className="flex flex-wrap items-center gap-2">
            <Input
              type="text"
              value={newItemName}
              onChange={(e) => setNewItemName(e.target.value)}
              placeholder={translate("gam.st.new_state")}
              className="min-w-40 flex-1"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAddItem();
              }}
            />
            <GroupSelect value={newItemGroup} onChange={setNewItemGroup} />
            <Button variant="secondary" onClick={handleAddItem} disabled={!newItemName.trim()}>
              {translate("gam.st.add_state")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
});

function StateTemplatesSettingsPage() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug as string;
  const { t } = useTranslation();
  const { allowPermissions } = useUserPermissions();
  const { currentWorkspace } = useWorkspace();
  const [newName, setNewName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canPerformWorkspaceAdminActions = allowPermissions([EUserPermissions.ADMIN], EUserPermissionsLevel.WORKSPACE);

  const { data: templates } = useSWR(
    canPerformWorkspaceAdminActions ? STATE_TEMPLATES_SWR_KEY(slug) : null,
    canPerformWorkspaceAdminActions ? () => stateTemplateService.fetchTemplates(slug) : null
  );

  const pageTitle = currentWorkspace?.name
    ? `${currentWorkspace.name} - ${t("workspace_settings.settings.state_templates.title")}`
    : undefined;

  if (!canPerformWorkspaceAdminActions) {
    return <NotAuthorizedView section="settings" className="h-auto" />;
  }

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setIsSubmitting(true);
    try {
      await stateTemplateService.createTemplate(slug, { name });
      setNewName("");
      mutate(STATE_TEMPLATES_SWR_KEY(slug));
    } catch (error: any) {
      showError(error, "Could not create the template.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (templateId: string) => {
    if (!window.confirm(translate("gam.st.delete_confirm"))) return;
    try {
      await stateTemplateService.deleteTemplate(slug, templateId);
      mutate(STATE_TEMPLATES_SWR_KEY(slug));
    } catch (error: any) {
      showError(error, "Could not delete the template.");
    }
  };

  return (
    <SettingsContentWrapper header={<StateTemplatesWorkspaceSettingsHeader />}>
      <PageHead title={pageTitle} />
      <div className="w-full">
        <SettingsHeading
          title={t("workspace_settings.settings.state_templates.title")}
          description={t("workspace_settings.settings.state_templates.description")}
        />
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder={translate("gam.st.template_name")}
            className="w-full sm:w-80"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
            }}
          />
          <Button variant="primary" onClick={handleCreate} disabled={isSubmitting || !newName.trim()}>
            {translate("gam.st.add_template")}
          </Button>
        </div>
        <div className="mt-6 divide-y divide-subtle border-t border-subtle">
          {templates?.length ? (
            templates.map((template) => (
              <TemplateRow key={template.id} slug={slug} template={template} onDelete={handleDelete} />
            ))
          ) : (
            <p className="py-6 text-14 text-tertiary">{translate("gam.st.none")}</p>
          )}
        </div>
      </div>
    </SettingsContentWrapper>
  );
}

export default observer(StateTemplatesSettingsPage);
