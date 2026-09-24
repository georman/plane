/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: Customers settings page - add/remove GAM's clients, set
 * their billing type (retainer flat-fee vs per-job), and their agreed
 * price per service (their "rate card"). See plane_stack.md memory for
 * the full Customer/Service billing model.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";
import useSWR, { mutate } from "swr";
// plane imports
import { EUserPermissions, EUserPermissionsLevel } from "@plane/constants";
import { translate, useTranslation } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { Input } from "@plane/ui";
import type { ICustomerServiceRate, TCustomerLanguage } from "@plane/types";
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
import { CustomersWorkspaceSettingsHeader } from "./header";

const CUSTOMERS_SWR_KEY = (slug: string) => `GAM_CUSTOMERS_${slug}`;
const SERVICES_SWR_KEY = (slug: string) => `GAM_SERVICES_${slug}`;

function RateCard({
  slug,
  customerId,
  rates,
  services,
}: {
  slug: string;
  customerId: string;
  rates: ICustomerServiceRate[];
  services: { id: string; name: string }[] | undefined;
}) {
  const [serviceId, setServiceId] = useState("");
  const [price, setPrice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const availableServices = (services ?? []).filter((s) => !rates.some((r) => r.service === s.id));

  const handleAddRate = async () => {
    if (!serviceId || !price) return;
    setIsSubmitting(true);
    try {
      await billingService.createCustomerRate(slug, customerId, { service: serviceId, price });
      setServiceId("");
      setPrice("");
      mutate(CUSTOMERS_SWR_KEY(slug));
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateRate = async (rateId: string, newPrice: string) => {
    try {
      await billingService.updateCustomerRate(slug, customerId, rateId, { price: newPrice });
      mutate(CUSTOMERS_SWR_KEY(slug));
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    }
  };

  const handleDeleteRate = async (rateId: string) => {
    try {
      await billingService.deleteCustomerRate(slug, customerId, rateId);
      mutate(CUSTOMERS_SWR_KEY(slug));
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    }
  };

  return (
    <div className="bg-layer-1 px-4 py-3">
      {rates.length > 0 && (
        <div className="mb-3 space-y-2">
          {rates.map((rate) => (
            <div key={rate.id} className="flex items-center gap-3">
              <span className="w-40 text-13 text-secondary">{rate.service_name}</span>
              <Input
                type="number"
                step="0.01"
                defaultValue={rate.price}
                className="w-28"
                onBlur={(e) => {
                  if (e.target.value !== rate.price) handleUpdateRate(rate.id, e.target.value);
                }}
              />
              <span className="text-13 text-tertiary">
                EUR {rate.service_billing_type === "monthly" ? translate("gam.per_month") : translate("gam.per_job")}
              </span>
              <button
                type="button"
                onClick={() => handleDeleteRate(rate.id)}
                className="text-tertiary hover:text-danger-primary"
                aria-label={`Remove ${rate.service_name} rate`}
              >
                <Trash2 className="size-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
      {availableServices.length > 0 ? (
        <div className="flex items-center gap-2">
          <select
            value={serviceId}
            onChange={(e) => setServiceId(e.target.value)}
            className="w-40 rounded-sm border border-subtle bg-surface-1 px-2 py-1.5 text-13"
          >
            <option value="">{translate("gam.choose_service")}</option>
            {availableServices.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <Input
            type="number"
            step="0.01"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder={translate("gam.price")}
            className="w-28"
          />
          <Button variant="secondary" size="sm" onClick={handleAddRate} disabled={isSubmitting || !serviceId || !price}>
            {translate("gam.add_rate")}
          </Button>
        </div>
      ) : (
        <p className="text-13 text-tertiary">{translate("gam.all_services_priced")}</p>
      )}
    </div>
  );
}

// GAM: edit a customer's details (name, contact email)
function CustomerDetailsForm({
  slug,
  customer,
}: {
  slug: string;
  customer: { id: string; name: string; contact_email: string };
}) {
  const [name, setName] = useState(customer.name);
  const [contactEmail, setContactEmail] = useState(customer.contact_email ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isChanged = name.trim() !== customer.name || contactEmail.trim() !== (customer.contact_email ?? "");

  const handleSave = async () => {
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await billingService.updateCustomer(slug, customer.id, {
        name: name.trim(),
        contact_email: contactEmail.trim(),
      });
      mutate(CUSTOMERS_SWR_KEY(slug));
      setToast({ type: TOAST_TYPE.SUCCESS, title: translate("gam.saved"), message: name.trim() });
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 bg-layer-1 px-4 pt-3">
      <Input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder={translate("gam.customer_name")}
        className="w-full sm:w-52"
      />
      <Input
        type="email"
        value={contactEmail}
        onChange={(e) => setContactEmail(e.target.value)}
        placeholder={translate("gam.contact_email_optional")}
        className="w-full sm:w-56"
      />
      <Button variant="primary" size="sm" onClick={handleSave} disabled={isSubmitting || !isChanged || !name.trim()}>
        {translate("gam.save")}
      </Button>
    </div>
  );
}

// GAM: the customer's personal client portal link
function CustomerPortalLink({ slug, customerId, hasEmail }: { slug: string; customerId: string; hasEmail: boolean }) {
  const [isBusy, setIsBusy] = useState(false);
  const run = async (action: "copy" | "email" | "renew") => {
    if (action === "renew" && !window.confirm(translate("gam.portal.renew_confirm"))) return;
    setIsBusy(true);
    try {
      const result = await billingService.customerPortalLink(slug, customerId, action === "copy" ? undefined : action);
      if (action === "email") {
        setToast({
          type: TOAST_TYPE.SUCCESS,
          title: translate("gam.portal.emailed"),
          message: result.sent_to ?? translate("gam.portal.not_sent"),
        });
        return;
      }
      await navigator.clipboard.writeText(result.url);
      setToast({ type: TOAST_TYPE.SUCCESS, title: translate("gam.portal.copied"), message: result.url });
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    } finally {
      setIsBusy(false);
    }
  };
  return (
    <div className="flex flex-wrap items-center gap-2 bg-layer-1 px-4 pt-3">
      <span className="text-13 text-secondary">{translate("gam.portal.title")}:</span>
      <Button variant="secondary" size="sm" disabled={isBusy} onClick={() => run("copy")}>
        {translate("gam.portal.copy")}
      </Button>
      <Button variant="secondary" size="sm" disabled={isBusy || !hasEmail} onClick={() => run("email")}>
        {translate("gam.portal.email")}
      </Button>
      <Button variant="tertiary" size="sm" disabled={isBusy} onClick={() => run("renew")}>
        {translate("gam.portal.renew")}
      </Button>
    </div>
  );
}

function CustomersSettingsPage() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug as string;
  const { t } = useTranslation();
  const { allowPermissions } = useUserPermissions();
  const { currentWorkspace } = useWorkspace();

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [language, setLanguage] = useState<TCustomerLanguage>("el");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canPerformWorkspaceAdminActions = allowPermissions([EUserPermissions.ADMIN], EUserPermissionsLevel.WORKSPACE);

  const { data: customers } = useSWR(
    canPerformWorkspaceAdminActions ? CUSTOMERS_SWR_KEY(slug) : null,
    canPerformWorkspaceAdminActions ? () => billingService.fetchCustomers(slug) : null
  );
  const { data: services } = useSWR(
    canPerformWorkspaceAdminActions ? SERVICES_SWR_KEY(slug) : null,
    canPerformWorkspaceAdminActions ? () => billingService.fetchServices(slug) : null
  );

  const pageTitle = currentWorkspace?.name
    ? `${currentWorkspace.name} - ${t("workspace_settings.settings.customers.title")}`
    : undefined;

  if (!canPerformWorkspaceAdminActions) {
    return <NotAuthorizedView section="settings" className="h-auto" />;
  }

  const handleCreate = async () => {
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      await billingService.createCustomer(slug, {
        name: name.trim(),
        contact_email: contactEmail.trim(),
        language,
      });
      setName("");
      setContactEmail("");
      setLanguage("el");
      mutate(CUSTOMERS_SWR_KEY(slug));
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    } finally {
      setIsSubmitting(false);
    }
  };

  // GAM: the language this client receives emails, approval pages and billing PDFs in
  const handleLanguageChange = async (customerId: string, newLanguage: TCustomerLanguage) => {
    try {
      await billingService.updateCustomer(slug, customerId, { language: newLanguage });
      mutate(CUSTOMERS_SWR_KEY(slug));
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    }
  };

  const handleDelete = async (customerId: string) => {
    try {
      await billingService.deleteCustomer(slug, customerId);
      mutate(CUSTOMERS_SWR_KEY(slug));
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: translate("gam.error"), message: error?.error ?? translate("gam.error_generic") });
    }
  };

  return (
    <SettingsContentWrapper header={<CustomersWorkspaceSettingsHeader />}>
      <PageHead title={pageTitle} />
      <div className="w-full">
        <SettingsHeading
          title={t("workspace_settings.settings.customers.title")}
          description={t("workspace_settings.settings.customers.description")}
        />
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={translate("gam.customer_name")}
            className="w-full sm:w-52"
          />
          <Input
            type="email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            placeholder={translate("gam.contact_email_optional")}
            className="w-full sm:w-56"
          />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as TCustomerLanguage)}
            className="rounded-sm border border-subtle bg-surface-1 px-2 py-1.5 text-13"
            aria-label="Language the customer receives emails in"
          >
            <option value="el">Ελληνικά</option>
            <option value="en">English</option>
          </select>
          <Button variant="primary" onClick={handleCreate} disabled={isSubmitting || !name.trim()}>
            {translate("gam.add_customer")}
          </Button>
        </div>

        <div className="mt-6 divide-y divide-subtle border-t border-subtle">
          {customers?.length ? (
            customers.map((customer) => {
              const isExpanded = expandedId === customer.id;
              return (
                <div key={customer.id}>
                  <div className="flex flex-wrap items-center justify-between gap-y-2 py-3">
                    <button
                      type="button"
                      className="flex min-w-0 flex-1 flex-wrap items-center gap-2 text-left"
                      onClick={() => setExpandedId(isExpanded ? null : customer.id)}
                    >
                      {isExpanded ? (
                        <ChevronDown className="size-4 text-tertiary" />
                      ) : (
                        <ChevronRight className="size-4 text-tertiary" />
                      )}
                      <span className="text-14 text-primary">{customer.name}</span>
                      {customer.contact_email && (
                        <span className="text-12 text-tertiary">{customer.contact_email}</span>
                      )}
                      <span className="text-12 text-tertiary">
                        {translate("gam.rates_set", { count: customer.rates.length })}
                      </span>
                    </button>
                    <select
                      value={customer.language ?? "el"}
                      onChange={(e) => handleLanguageChange(customer.id, e.target.value as TCustomerLanguage)}
                      className="mr-3 rounded-sm border border-subtle bg-surface-1 px-2 py-1 text-12"
                      aria-label={`Language for ${customer.name}`}
                      title="Language of emails, approval pages and billing PDFs"
                    >
                      <option value="el">Ελληνικά</option>
                      <option value="en">English</option>
                    </select>
                    <button
                      type="button"
                      onClick={() => handleDelete(customer.id)}
                      className="text-tertiary hover:text-danger-primary"
                      aria-label={`Delete ${customer.name}`}
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                  {isExpanded && (
                    <>
                      <CustomerDetailsForm slug={slug} customer={customer} />
                      <CustomerPortalLink slug={slug} customerId={customer.id} hasEmail={!!customer.contact_email} />
                      <RateCard slug={slug} customerId={customer.id} rates={customer.rates} services={services} />
                    </>
                  )}
                </div>
              );
            })
          ) : (
            <p className="py-6 text-14 text-tertiary">{translate("gam.no_customers")}</p>
          )}
        </div>
      </div>
    </SettingsContentWrapper>
  );
}

export default observer(CustomersSettingsPage);
