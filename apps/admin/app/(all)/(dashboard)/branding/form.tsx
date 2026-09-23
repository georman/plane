/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: white-label brand settings form.
 */

import { useRef, useState } from "react";
import { observer } from "mobx-react";
import { useForm } from "react-hook-form";
import { brandLogoUrl, getBrand } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { InstanceService } from "@plane/services";
import type { IFormattedInstanceConfiguration, TInstanceBrandConfigurationKeys } from "@plane/types";
// components
import { ControllerInput } from "@/components/common/controller-input";
// hooks
import { useInstance } from "@/hooks/store";

type TBrandingFormValues = Record<TInstanceBrandConfigurationKeys, string>;

const instanceService = new InstanceService();
const MAX_LOGO_BYTES = 2 * 1024 * 1024;

const errorMessage = (error: any, fallback: string) =>
  typeof error?.error === "string" ? error.error : fallback;

export const InstanceBrandingForm = observer(function InstanceBrandingForm(props: {
  config: IFormattedInstanceConfiguration;
}) {
  const { config } = props;
  const { updateInstanceConfigurations, fetchInstanceInfo } = useInstance();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [logoUrl, setLogoUrl] = useState(brandLogoUrl());
  const [hasCustomLogo, setHasCustomLogo] = useState(Boolean(getBrand().has_custom_logo));
  const [isUploading, setIsUploading] = useState(false);

  const {
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<TBrandingFormValues>({
    defaultValues: {
      GAM_BRAND_NAME: config["GAM_BRAND_NAME"],
      GAM_SUPPORT_EMAIL: config["GAM_SUPPORT_EMAIL"],
      GAM_BRAND_WEBSITE: config["GAM_BRAND_WEBSITE"],
    },
  });

  // Reload the public instance info so every open tab picks up the new brand
  const refreshBrand = async () => {
    await fetchInstanceInfo();
    const brand = getBrand();
    setLogoUrl(brand.logo_url);
    setHasCustomLogo(Boolean(brand.has_custom_logo));
  };

  const onSubmit = async (formData: TBrandingFormValues) => {
    try {
      await updateInstanceConfigurations({
        GAM_BRAND_NAME: formData.GAM_BRAND_NAME.trim(),
        GAM_SUPPORT_EMAIL: formData.GAM_SUPPORT_EMAIL.trim(),
        GAM_BRAND_WEBSITE: formData.GAM_BRAND_WEBSITE.trim(),
      });
      await refreshBrand();
      setToast({ type: TOAST_TYPE.SUCCESS, title: "Saved", message: "Branding updated. Open pages update on reload." });
    } catch (error) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Not saved", message: errorMessage(error, "Could not save branding.") });
    }
  };

  const handleLogoChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_LOGO_BYTES) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Logo too large", message: "Choose an image of 2 MB or smaller." });
      return;
    }
    setIsUploading(true);
    try {
      await instanceService.uploadBrandLogo(file);
      await refreshBrand();
      setToast({ type: TOAST_TYPE.SUCCESS, title: "Logo uploaded", message: "The new logo is now used everywhere." });
    } catch (error) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Upload failed", message: errorMessage(error, "Could not upload the logo.") });
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveLogo = async () => {
    setIsUploading(true);
    try {
      await instanceService.removeBrandLogo();
      await refreshBrand();
      setToast({ type: TOAST_TYPE.SUCCESS, title: "Logo removed", message: "The built-in logo is used again." });
    } catch (error) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Not removed", message: errorMessage(error, "Could not remove the logo.") });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-10">
      <div className="grid w-full grid-cols-1 gap-x-16 gap-y-8 lg:grid-cols-2">
        <ControllerInput
          control={control}
          type="text"
          name="GAM_BRAND_NAME"
          label="Brand name"
          description="Shown instead of the product name in every app, language, email and error page."
          placeholder="GAM"
          error={Boolean(errors.GAM_BRAND_NAME)}
          required
        />
        <ControllerInput
          control={control}
          type="text"
          name="GAM_SUPPORT_EMAIL"
          label="Support email"
          description="Used for every Contact support link and in error messages."
          placeholder="info@gam.gr"
          error={Boolean(errors.GAM_SUPPORT_EMAIL)}
          required
        />
        <ControllerInput
          control={control}
          type="text"
          name="GAM_BRAND_WEBSITE"
          label="Website (optional)"
          description="Help, docs and contact links open this. When empty they open an email to support."
          placeholder="https://www.gam.gr"
          error={Boolean(errors.GAM_BRAND_WEBSITE)}
          required={false}
        />
      </div>
      <div>
        <Button variant="primary" size="lg" onClick={handleSubmit(onSubmit)} loading={isSubmitting}>
          {isSubmitting ? "Saving" : "Save changes"}
        </Button>
      </div>

      <div className="space-y-3 border-t border-subtle pt-8">
        <h4 className="text-13 text-tertiary">Logo</h4>
        <p className="text-12 text-tertiary">
          Used on the sign-in pages, as the browser tab icon and in emails. PNG, JPG, SVG, WebP or GIF, up to 2 MB. A
          square image works best.
        </p>
        <div className="flex flex-wrap items-center gap-4">
          <img
            src={logoUrl}
            alt="Current logo"
            className="size-20 rounded-md border border-subtle bg-surface-1 object-contain p-1"
          />
          <input
            ref={fileInputRef}
            id="brand-logo-input"
            type="file"
            accept="image/png,image/jpeg,image/svg+xml,image/webp,image/gif"
            className="hidden"
            onChange={handleLogoChange}
          />
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()} loading={isUploading}>
            Upload new logo
          </Button>
          {hasCustomLogo && (
            <Button variant="link-danger" onClick={handleRemoveLogo} disabled={isUploading}>
              Use built-in logo
            </Button>
          )}
        </div>
      </div>
    </div>
  );
});
