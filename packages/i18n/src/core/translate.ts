/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: translate a key in the current UI language without the React hook.
 */

import { i18nInstance } from "./instance";

export const translate = (key: string, params?: Record<string, unknown>): string => {
  const value = params === undefined ? i18nInstance.t(key) : i18nInstance.t(key, params);
  return typeof value === "string" ? value : key;
};

/** Like translate(), but returns the fallback when there is no translation for the key. */
export const translateOr = (key: string, fallback: string): string =>
  i18nInstance.exists(key) ? translate(key) : fallback;
