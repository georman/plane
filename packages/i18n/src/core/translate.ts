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

/**
 * GAM: the job pipeline states are stored with Greek names (older projects may
 * still have the English ones). They are shown in the viewer's language;
 * states people add themselves are shown as typed.
 */
const GAM_PIPELINE_STATE_KEYS: Record<string, string> = {
  "Νέο αίτημα": "new_request",
  Προσφορά: "quotation",
  Εγκρίθηκε: "approved",
  "Σε εξέλιξη": "in_progress",
  "Εσωτερικός έλεγχος": "internal_review",
  "Έγκριση πελάτη": "client_approval",
  Διορθώσεις: "corrections",
  "Έτοιμο για παράδοση": "ready_for_delivery",
  Παραδόθηκε: "delivered",
  Τιμολογήθηκε: "invoiced",
  Ακυρώθηκε: "cancelled",
  "New request": "new_request",
  Quotation: "quotation",
  Approved: "approved",
  "In progress": "in_progress",
  "Internal review": "internal_review",
  "Client approval": "client_approval",
  Corrections: "corrections",
  "Ready for delivery": "ready_for_delivery",
  Delivered: "delivered",
  Invoiced: "invoiced",
  Cancelled: "cancelled",
};

export const stateDisplayName = (name: string): string => {
  const key = GAM_PIPELINE_STATE_KEYS[name];
  return key ? translateOr(`gam.pipeline_state.${key}`, name) : name;
};
