/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";

import type { ISvgIcons } from "../type";

// GAM white label: the brand logo from the admin panel (God mode > Branding),
// served by /api/instances/brand-logo/ (falls back to the built-in logo).
export function PlaneLogo({ width = "auto", height = "auto", className }: ISvgIcons) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/api/instances/brand-logo/"
      alt="Logo"
      width={width}
      height={height}
      className={className}
      style={{ objectFit: "contain" }}
    />
  );
}
