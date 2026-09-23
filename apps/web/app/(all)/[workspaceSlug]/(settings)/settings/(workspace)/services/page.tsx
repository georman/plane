/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: Services settings page - add/rename/remove the types of
 * billable work GAM offers (Design, CTP, SEO, IG Posts, ...) and edit each
 * service's checklist. When a work item is linked to a service, its checklist
 * steps are created as sub-items. See plane_stack.md memory for the full
 * Customer/Service billing model.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { ArrowDown, ArrowUp, ChevronDown, ChevronRight, Trash2 } from "lucide-react";
import useSWR, { mutate } from "swr";
// plane imports
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IService, IServiceTemplateItem } from "@plane/types";
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
import { billingService } from "@/services/billing.service";
// local
import { ServicesWorkspaceSettingsHeader } from "./header";

const SERVICES_SWR_KEY = (slug: string) => `GAM_SERVICES_${slug}`;

const showError = (error: any, fallback: string) =>
  setToast({ type: TOAST_TYPE.ERROR, title: "Error", message: error?.error ?? fallback });

type TServiceRowProps = {
  slug: string;
  service: IService;
  onDelete: (serviceId: string) => void;
};

const ServiceRow = observer(function ServiceRow({ slug, service, onDelete }: TServiceRowProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState(service.name);
  const [newStep, setNewStep] = useState("");
  const steps = [...(service.template_items ?? [])].sort((a, b) => a.sequence - b.sequence);
  const refresh = () => mutate(SERVICES_SWR_KEY(slug));

  const handleRename = async () => {
    const trimmed = name.trim();
    if (!trimmed || trimmed === service.name) return setName(service.name);
    try {
      await billingService.updateService(slug, service.id, { name: trimmed });
      refresh();
    } catch (error: any) {
      setName(service.name);
      showError(error, "Could not rename service.");
    }
  };

  const handleAddStep = async () => {
    const trimmed = newStep.trim();
    if (!trimmed) return;
    try {
      await billingService.createServiceTemplateItem(slug, service.id, { name: trimmed });
      setNewStep("");
      refresh();
    } catch (error: any) {
      showError(error, "Could not add step.");
    }
  };

  const handleRenameStep = async (step: IServiceTemplateItem, value: string) => {
    const trimmed = value.trim();
    if (!trimmed || trimmed === step.name) return;
    try {
      await billingService.updateServiceTemplateItem(slug, service.id, step.id, { name: trimmed });
      refresh();
    } catch (error: any) {
      showError(error, "Could not rename step.");
    }
  };

  // Swap sequences with the neighbour to move a step up or down
  const handleMoveStep = async (index: number, direction: -1 | 1) => {
    const current = steps[index];
    const neighbour = steps[index + direction];
    if (!current || !neighbour) return;
    try {
      await Promise.all([
        billingService.updateServiceTemplateItem(slug, service.id, current.id, { sequence: neighbour.sequence }),
        billingService.updateServiceTemplateItem(slug, service.id, neighbour.id, { sequence: current.sequence }),
      ]);
      refresh();
    } catch (error: any) {
      showError(error, "Could not reorder steps.");
    }
  };

  const handleDeleteStep = async (stepId: string) => {
    try {
      await billingService.deleteServiceTemplateItem(slug, service.id, stepId);
      refresh();
    } catch (error: any) {
      showError(error, "Could not delete step.");
    }
  };

  return (
    <div className="py-3">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="text-tertiary hover:text-primary"
          aria-label={isOpen ? `Hide checklist for ${service.name}` : `Show checklist for ${service.name}`}
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
          aria-label="Service name"
        />
        <span className="shrink-0 text-12 text-tertiary">
          {steps.length} {steps.length === 1 ? "step" : "steps"}
        </span>
        <button
          type="button"
          onClick={() => onDelete(service.id)}
          className="text-tertiary hover:text-danger-primary"
          aria-label={`Delete ${service.name}`}
        >
          <Trash2 className="size-4" />
        </button>
      </div>
      {isOpen && (
        <div className="mt-3 ml-6 flex flex-col gap-2">
          <p className="text-12 text-tertiary">
            These steps are added as sub-items when a work item is set to this service.
          </p>
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center gap-2">
              <span className="w-5 shrink-0 text-right text-12 text-tertiary">{index + 1}.</span>
              <Input
                type="text"
                defaultValue={step.name}
                onBlur={(e) => handleRenameStep(step, e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                }}
                className="flex-1"
                aria-label={`Step ${index + 1}`}
              />
              <button
                type="button"
                onClick={() => handleMoveStep(index, -1)}
                disabled={index === 0}
                className="text-tertiary hover:text-primary disabled:opacity-30"
                aria-label="Move step up"
              >
                <ArrowUp className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => handleMoveStep(index, 1)}
                disabled={index === steps.length - 1}
                className="text-tertiary hover:text-primary disabled:opacity-30"
                aria-label="Move step down"
              >
                <ArrowDown className="size-4" />
              </button>
              <button
                type="button"
                onClick={() => handleDeleteStep(step.id)}
                className="text-tertiary hover:text-danger-primary"
                aria-label={`Delete step ${step.name}`}
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <span className="w-5 shrink-0" />
            <Input
              type="text"
              value={newStep}
              onChange={(e) => setNewStep(e.target.value)}
              placeholder="Add a step, e.g. Send proof to client"
              className="flex-1"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAddStep();
              }}
            />
            <Button variant="secondary" onClick={handleAddStep} disabled={!newStep.trim()}>
              Add step
            </Button>
          </div>
        </div>
      )}
    </div>
  );
});

function ServicesSettingsPage() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug as string;
  const { t } = useTranslation();
  const { allowPermissions } = useUserPermissions();
  const { currentWorkspace } = useWorkspace();
  const [newServiceName, setNewServiceName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canPerformWorkspaceAdminActions = allowPermissions([EUserPermissions.ADMIN], EUserPermissionsLevel.WORKSPACE);

  const { data: services } = useSWR(
    canPerformWorkspaceAdminActions ? SERVICES_SWR_KEY(slug) : null,
    canPerformWorkspaceAdminActions ? () => billingService.fetchServices(slug) : null
  );

  const pageTitle = currentWorkspace?.name
    ? `${currentWorkspace.name} - ${t("workspace_settings.settings.services.title")}`
    : undefined;

  if (!canPerformWorkspaceAdminActions) {
    return <NotAuthorizedView section="settings" className="h-auto" />;
  }

  const handleCreate = async () => {
    const name = newServiceName.trim();
    if (!name) return;
    setIsSubmitting(true);
    try {
      await billingService.createService(slug, { name });
      setNewServiceName("");
      mutate(SERVICES_SWR_KEY(slug));
    } catch (error: any) {
      showError(error, "Could not create service.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (serviceId: string) => {
    try {
      await billingService.deleteService(slug, serviceId);
      mutate(SERVICES_SWR_KEY(slug));
    } catch (error: any) {
      showError(error, "Could not delete service.");
    }
  };

  return (
    <SettingsContentWrapper header={<ServicesWorkspaceSettingsHeader />}>
      <PageHead title={pageTitle} />
      <div className="w-full">
        <SettingsHeading
          title={t("workspace_settings.settings.services.title")}
          description={t("workspace_settings.settings.services.description")}
        />
        <div className="mt-4 flex items-center gap-2">
          <Input
            type="text"
            value={newServiceName}
            onChange={(e) => setNewServiceName(e.target.value)}
            placeholder="e.g. Design, CTP, SEO, IG Posts"
            className="w-80"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
            }}
          />
          <Button variant="primary" onClick={handleCreate} disabled={isSubmitting || !newServiceName.trim()}>
            Add service
          </Button>
        </div>
        <div className="mt-6 divide-y divide-subtle border-t border-subtle">
          {services?.length ? (
            services.map((service) => (
              <ServiceRow key={service.id} slug={slug} service={service} onDelete={handleDelete} />
            ))
          ) : (
            <p className="py-6 text-14 text-tertiary">No services yet - add one above.</p>
          )}
        </div>
      </div>
    </SettingsContentWrapper>
  );
}

export default observer(ServicesSettingsPage);
