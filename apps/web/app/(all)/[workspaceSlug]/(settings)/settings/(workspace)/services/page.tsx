/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: Services settings page - add/remove the types of billable
 * work GAM offers (Design, CTP, SEO, IG Posts, ...). See plane_stack.md
 * memory for the full Customer/Service billing model.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { Trash2 } from "lucide-react";
import useSWR, { mutate } from "swr";
// plane imports
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
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
      setToast({ type: TOAST_TYPE.ERROR, title: "Error", message: error?.error ?? "Could not create service." });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (serviceId: string) => {
    try {
      await billingService.deleteService(slug, serviceId);
      mutate(SERVICES_SWR_KEY(slug));
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Error", message: error?.error ?? "Could not delete service." });
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
              <div key={service.id} className="flex items-center justify-between py-3">
                <span className="text-14 text-primary">{service.name}</span>
                <button
                  type="button"
                  onClick={() => handleDelete(service.id)}
                  className="text-tertiary hover:text-danger-primary"
                  aria-label={`Delete ${service.name}`}
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
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
