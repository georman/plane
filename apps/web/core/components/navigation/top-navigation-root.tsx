/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// components
import { observer } from "mobx-react";
import { useParams, usePathname } from "next/navigation";
import { Globe } from "lucide-react";
import { cn } from "@plane/utils";
import { brandName, SUPPORTED_LANGUAGES, useTranslation } from "@plane/i18n";
import { CustomSelect } from "@plane/ui";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { TopNavPowerK } from "@/components/navigation";
import { UserMenuRoot } from "@/components/workspace/sidebar/user-menu-root";
import { WorkspaceMenuRoot } from "@/components/workspace/sidebar/workspace-menu-root";
import { useAppRailPreferences } from "@/hooks/use-navigation-preferences";
import { Tooltip } from "@plane/propel/tooltip";
import { AppSidebarItem } from "@/components/sidebar/sidebar-item";
import { InboxIcon } from "@plane/propel/icons";
import useSWR from "swr";
import { useWorkspaceNotifications } from "@/hooks/store/notifications";
import { useUserProfile } from "@/hooks/store/user";
// GAM addition: admin "log in as member" feature
import { impersonationService } from "@/services/impersonation.service";
// local imports

function ImpersonationBanner() {
  const { data } = useSWR("GAM_IMPERSONATION_STATUS", () => impersonationService.getImpersonationStatus(), {
    refreshInterval: 0,
    revalidateOnFocus: false,
  });

  if (!data?.is_impersonating) return null;

  const handleReturn = async () => {
    try {
      await impersonationService.stopImpersonating();
    } finally {
      window.location.href = "/";
    }
  };

  return (
    <div className="flex w-full items-center justify-center gap-3 bg-amber-500 px-3 py-1.5 text-13 font-medium text-black">
      <span>
        Viewing as <strong>{data.target_user_display_name || data.target_user_email}</strong> ({data.target_user_email})
        - logged in by {data.impersonator_email}
      </span>
      <button
        type="button"
        onClick={handleReturn}
        className="rounded-md bg-black/10 px-2.5 py-0.5 font-semibold hover:bg-black/20"
      >
        Return to your account
      </button>
    </div>
  );
}

function HeaderLanguageSelector() {
  // Matches ProfileSettingsLanguageAndTimezonePreferencesList's own pattern
  // (settings/profile/content/pages/preferences/language-and-timezone-list.tsx):
  // updateUserProfile({ language }) alone is enough - profile.store.ts's
  // updateUserProfile action calls setLanguage() internally as soon as a
  // language field is present, which updates i18next + localStorage +
  // document.documentElement.lang. No need to call setLanguage ourselves here.
  const { currentLocale } = useTranslation();
  const { updateUserProfile } = useUserProfile();

  const handleChange = async (value: string) => {
    try {
      await updateUserProfile({ language: value });
    } catch (_error) {
      setToast({ title: "Error!", message: "Failed to save language preference", type: TOAST_TYPE.ERROR });
    }
  };

  return (
    <Tooltip tooltipContent="Language" position="bottom">
      <CustomSelect
        value={currentLocale}
        onChange={handleChange}
        placement="bottom-end"
        customButton={
          <div className="flex size-8 items-center justify-center rounded-md hover:bg-layer-1-hover">
            <Globe className="size-4 text-tertiary" />
          </div>
        }
        customButtonClassName="flex items-center"
      >
        {SUPPORTED_LANGUAGES.map((language) => (
          <CustomSelect.Option key={language.value} value={language.value}>
            {language.label}
            {currentLocale === language.value ? " ✓" : ""}
          </CustomSelect.Option>
        ))}
      </CustomSelect>
    </Tooltip>
  );
}

export const TopNavigationRoot = observer(function TopNavigationRoot() {
  // router
  const { workspaceSlug } = useParams();
  const pathname = usePathname();

  // store hooks
  const { unreadNotificationsCount, getUnreadNotificationsCount } = useWorkspaceNotifications();
  const { preferences } = useAppRailPreferences();

  const showLabel = preferences.displayMode === "icon_with_label";

  // Fetch notification count
  useSWR(
    workspaceSlug ? "WORKSPACE_UNREAD_NOTIFICATION_COUNT" : null,
    workspaceSlug ? () => getUnreadNotificationsCount(workspaceSlug.toString()) : null
  );

  // Calculate notification count
  const isMentionsEnabled = unreadNotificationsCount.mention_unread_notifications_count > 0;
  const totalNotifications = isMentionsEnabled
    ? unreadNotificationsCount.mention_unread_notifications_count
    : unreadNotificationsCount.total_unread_notifications_count;

  return (
    <>
      <ImpersonationBanner />
      <div
        className={cn("z-[27] flex min-h-10 w-full items-center bg-canvas px-3.5 transition-all duration-300", {
          "px-2": !showLabel,
        })}
      >
      {/* Workspace Menu */}
      {/* GAM: on phones the search bar shrinks so the right-hand icons stay on screen */}
      <div className="shrink-0 md:flex-1">
        <WorkspaceMenuRoot variant="top-navigation" />
      </div>
      {/* Power K Search */}
      <div className="mx-2 min-w-0 flex-1 md:mx-0 md:flex-none md:shrink-0">
        <TopNavPowerK />
      </div>
      {/* Additional Actions */}
      <div className="flex shrink-0 items-center justify-end gap-1 md:flex-1">
        <Tooltip tooltipContent="Inbox" position="bottom">
          <AppSidebarItem
            variant="link"
            item={{
              href: `/${workspaceSlug?.toString()}/notifications/`,
              icon: (
                <div className="relative">
                  <InboxIcon className="size-5" />
                  {totalNotifications > 0 && (
                    <span className="absolute top-0 right-0 size-2 rounded-full bg-danger-primary" />
                  )}
                </div>
              ),
              isActive: pathname?.includes("/notifications/"),
            }}
          />
        </Tooltip>
        {/* GAM: removed HelpMenuRoot (Plane docs/community links) and StarUsOnGitHubLink - not relevant for GAM's own instance */}
        <HeaderLanguageSelector />
        <div className="flex size-8 items-center justify-center rounded-md hover:bg-layer-1-hover">
          <UserMenuRoot />
        </div>
      </div>
      </div>
    </>
  );
});
