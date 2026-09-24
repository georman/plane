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
  // Other templates (from the Kan boards) and template names
  "Requested": "requested",
  "Planned": "planned",
  "Done": "done",
  "Under Review": "under_review",
  "Rejected": "rejected",
  "Ideas": "ideas",
  "Research": "research",
  "Planning": "planning",
  "Execution": "execution",
  "Review": "review",
  "Next Steps": "next_steps",
  "Complete": "complete",
  "Backlog": "backlog",
  "To Do": "to_do",
  "Todo": "to_do",
  "Code Review": "code_review",
  "Brainstorming": "brainstorming",
  "Writing": "writing",
  "Editing": "editing",
  "Design": "design",
  "Approval": "approval",
  "Publishing": "publishing",
  "New Ticket": "new_ticket",
  "Triaging": "triaging",
  "Awaiting Customer": "awaiting_customer",
  "Resolution": "resolution",
  "Started": "started",
  "Unfinished": "unfinished",
  "GAM pipeline": "tpl_gam_pipeline",
  "Simple": "tpl_simple",
  "Basic Roadmap": "tpl_basic_roadmap",
  "Extended Roadmap": "tpl_extended_roadmap",
  "Personal Project": "tpl_personal_project",
  "Software": "tpl_software",
  "Content Creation": "tpl_content_creation",
  "Customer Support": "tpl_customer_support",
  "In Progress": "in_progress",
};

export const stateDisplayName = (name: string): string => {
  const key = GAM_PIPELINE_STATE_KEYS[name];
  return key ? translateOr(`gam.pipeline_state.${key}`, name) : name;
};
