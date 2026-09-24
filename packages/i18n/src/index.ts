/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// Components
export { TranslationProvider } from "./provider";

// Hooks
export { useTranslation } from "./hooks/use-translation";
export type { TTranslationStore } from "./hooks/use-translation";

// Types
export type { TLanguage, ILanguageOption } from "./types";
export type { TTranslationKeys } from "./types";
export type { TNamespace } from "./constants/namespaces";

// Utilities
export { setLanguage } from "./core/set-language";

// Constants
export { FALLBACK_LANGUAGE, SUPPORTED_LANGUAGES, LANGUAGE_STORAGE_KEY } from "./constants/language";

// GAM addition: white-label brand
export {
  applyBrand,
  applyBrandToDocument,
  brandHelpUrl,
  brandLogoUrl,
  brandName,
  brandSupportEmail,
  DEFAULT_BRAND,
  getBrand,
  setBrand,
  subscribeToBrand,
} from "./brand";
export type { TBrand } from "./brand";

// GAM addition: translate outside React components (and in components without the hook)
export { translate, translateOr, stateDisplayName } from "./core/translate";
