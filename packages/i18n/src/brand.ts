/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: white-label brand. The name, support email, website and logo
 * come from the admin panel (God mode > Branding) via /api/instances/ and are
 * remembered in the browser, so even the "can't reach the server" pages show
 * the right brand. Every translated string passes through applyBrand().
 */

export type TBrand = {
  name: string;
  support_email: string;
  website: string;
  logo_url: string;
  has_custom_logo?: boolean;
};

const STORAGE_KEY = "gam_brand";
export const DEFAULT_BRAND: TBrand = {
  name: "GAM",
  support_email: "info@gam.gr",
  website: "",
  logo_url: "/assets/gam-logo.png",
};

const readStoredBrand = (): TBrand => {
  if (typeof window === "undefined") return DEFAULT_BRAND;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored ? { ...DEFAULT_BRAND, ...(JSON.parse(stored) as Partial<TBrand>) } : DEFAULT_BRAND;
  } catch {
    return DEFAULT_BRAND;
  }
};

let currentBrand: TBrand = readStoredBrand();
const listeners = new Set<(brand: TBrand) => void>();

export const getBrand = (): TBrand => currentBrand;
export const brandName = (): string => currentBrand.name || DEFAULT_BRAND.name;
export const brandSupportEmail = (): string => currentBrand.support_email || DEFAULT_BRAND.support_email;
export const brandLogoUrl = (): string => currentBrand.logo_url || DEFAULT_BRAND.logo_url;

/** Where "help", "docs", "contact" and similar links go: the brand website, or an email to support. */
export const brandHelpUrl = (): string => currentBrand.website || `mailto:${brandSupportEmail()}`;

/**
 * Replace the upstream product name with the brand name in any text:
 * "Plane" / "plane" as a word become the brand, and example domains or
 * addresses (plane.so, plane.town, help@plane.so) become company.com ones.
 */
export const applyBrand = (text: string): string => {
  if (typeof text !== "string" || !/plane/i.test(text)) return text;
  return text
    .replace(/\bplane\.(so|town)\b/gi, "company.com")
    .replace(/\b(glab|gh)\.company\.com\b/g, "$1.company.com")
    .replace(/(?<![\w.@/-])Plane(?!\w)/g, brandName())
    .replace(/(?<![\w.@/-])plane-/g, `${brandName().toLowerCase().replace(/\s+/g, "-")}-`)
    .replace(/(?<![\w.@/-])plane(?![\w.-])/g, brandName());
};

/** Called with the "brand" block of /api/instances/ config once it loads. */
export const setBrand = (brand?: Partial<TBrand> | null): void => {
  if (!brand) return;
  const next: TBrand = {
    ...DEFAULT_BRAND,
    ...Object.fromEntries(Object.entries(brand).filter(([, value]) => value !== null && value !== undefined && value !== "")),
  };
  const changed = JSON.stringify(next) !== JSON.stringify(currentBrand);
  currentBrand = next;
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // storage unavailable (private mode) - the brand still applies for this visit
    }
    applyBrandToDocument();
  }
  if (changed) listeners.forEach((listener) => listener(next));
};

export const subscribeToBrand = (listener: (brand: TBrand) => void): (() => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

/** Tab title and favicon follow the brand too. */
export const applyBrandToDocument = (): void => {
  if (typeof document === "undefined") return;
  const branded = applyBrand(document.title);
  if (branded !== document.title) document.title = branded;
  if (currentBrand.has_custom_logo) {
    document.querySelectorAll<HTMLLinkElement>('link[rel~="icon"], link[rel="apple-touch-icon"]').forEach((link) => {
      if (link.href !== currentBrand.logo_url) link.href = currentBrand.logo_url;
    });
  }
};
