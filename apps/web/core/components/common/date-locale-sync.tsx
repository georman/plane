/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: dates and relative times ("2 days ago") follow the interface
 * language. date-fns reads its default locale from here everywhere in the app.
 * The shared priority and state-group lists (English in @plane/constants) are
 * relabelled here too, so every dropdown, filter and group header follows.
 */

import { useEffect } from "react";
import { setDefaultOptions } from "date-fns";
import { el, enUS } from "date-fns/locale";
import { ISSUE_PRIORITIES, ROLE, STATE_GROUPS } from "@plane/constants";
import { EUserWorkspaceRoles } from "@plane/types";
import { translate, useTranslation } from "@plane/i18n";

const DATE_LOCALES = { el, en: enUS } as const;

export function DateLocaleSync() {
  const { currentLocale } = useTranslation();
  useEffect(() => {
    setDefaultOptions({ locale: DATE_LOCALES[currentLocale as keyof typeof DATE_LOCALES] ?? enUS });
    ISSUE_PRIORITIES.forEach((priority) => {
      priority.title = translate(priority.key);
    });
    ROLE[EUserWorkspaceRoles.ADMIN] = translate("role_details.admin.title");
    ROLE[EUserWorkspaceRoles.MEMBER] = translate("common.member");
    ROLE[EUserWorkspaceRoles.GUEST] = translate("role_details.guest.title");
    Object.entries(STATE_GROUPS).forEach(([key, group]) => {
      group.label = translate(`gam.state_group.${key}`);
    });
  }, [currentLocale]);
  return null;
}
