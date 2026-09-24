/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { Image, BrainCog, Cog, FileText, Mail, Palette } from "lucide-react";
// plane imports
import { LockIcon, WorkspaceIcon } from "@plane/propel/icons";
// types
import type { TSidebarMenuItem } from "./types";
import { brandName } from "@plane/i18n"; // GAM addition: white label

export type TCoreSidebarMenuKey =
  | "general"
  | "branding"
  | "legal"
  | "email"
  | "workspace"
  | "authentication"
  | "ai"
  | "image";

export const coreSidebarMenuLinks: Record<TCoreSidebarMenuKey, TSidebarMenuItem> = {
  general: {
    Icon: Cog,
    name: "General",
    description: "Identify your instances and get key details.",
    href: `/general/`,
  },
  // GAM addition: white-label brand settings
  branding: {
    Icon: Palette,
    name: "Branding",
    description: "Name, support email, website and logo.",
    href: `/branding/`,
  },
  // GAM addition: public Terms of Service / Privacy Policy
  legal: {
    Icon: FileText,
    name: "Legal",
    description: "Terms of Service and Privacy Policy, in Greek and English.",
    href: `/legal/`,
  },
  email: {
    Icon: Mail,
    name: "Email",
    description: "Configure your SMTP controls.",
    href: `/email/`,
  },
  workspace: {
    Icon: WorkspaceIcon,
    name: "Workspaces",
    description: "Manage all workspaces on this instance.",
    href: `/workspace/`,
  },
  authentication: {
    Icon: LockIcon,
    name: "Authentication",
    description: "Configure authentication modes.",
    href: `/authentication/`,
  },
  ai: {
    Icon: BrainCog,
    name: "Artificial intelligence",
    description: "Configure your OpenAI creds.",
    href: `/ai/`,
  },
  image: {
    Icon: Image,
    name: `Images in ${brandName()}`,
    description: "Allow third-party image libraries.",
    href: `/image/`,
  },
};
