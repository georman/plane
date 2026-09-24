/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
// plane imports
import { PROFILE_SETTINGS_TABS } from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import type { TProfileSettingsTabs } from "@plane/types";
// components
import { LogoSpinner } from "@/components/common/logo-spinner";
import { PageHead } from "@/components/core/page-title";
import { ProfileSettingsContent } from "@/components/settings/profile/content";
import { ProfileSettingsSidebarRoot } from "@/components/settings/profile/sidebar";
// hooks
import { useUser } from "@/hooks/store/user";
import { useAppRouter } from "@/hooks/use-app-router";
// local imports
import type { Route } from "../+types/layout";

function ProfileSettingsPage(props: Route.ComponentProps) {
  const { profileTabId } = props.params;
  // router
  const router = useAppRouter();
  // store hooks
  const { data: currentUser } = useUser();
  // translation
  const { t } = useTranslation();
  // derived values
  const isAValidTab = PROFILE_SETTINGS_TABS.includes(profileTabId as TProfileSettingsTabs);

  if (!currentUser || !isAValidTab)
    return (
      <div className="grid size-full place-items-center px-4">
        <LogoSpinner />
      </div>
    );

  return (
    <>
      <PageHead title={`${t("profile.label")} - ${t("general_settings")}`} />
      <div className="relative size-full">
        {/* GAM: on phones the settings menu sits above the form as a short scrollable strip */}
        <div className="flex size-full flex-col overflow-y-auto md:flex-row md:overflow-visible">
          <ProfileSettingsSidebarRoot
            activeTab={profileTabId as TProfileSettingsTabs}
            className="max-h-[35vh] w-full shrink-0 overflow-y-auto border-r-0 border-b border-subtle md:max-h-none md:w-[250px] md:border-r md:border-b-0"
            updateActiveTab={(tab) => router.push(`/settings/profile/${tab}`)}
          />
          <ProfileSettingsContent
            activeTab={profileTabId as TProfileSettingsTabs}
            className="mx-auto w-full max-w-225 grow px-4 py-6 md:w-fit md:px-page-x md:py-20"
          />
        </div>
      </div>
    </>
  );
}

export default observer(ProfileSettingsPage);
