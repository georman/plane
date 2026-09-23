/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";

import type { ISvgIcons } from "../type";

// GAM white label: the brand logo from the admin panel (God mode > Branding).
// /api/instances/brand-logo/ serves the uploaded logo, or redirects to the
// built-in /assets/gam-logo.png (a docker-compose volume mount on the web
// container, see /dockerstor/stacks/plane/branding) when none is uploaded.
export function PlaneLockup({ width = "253", height = "53", className }: ISvgIcons) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/api/instances/brand-logo/"
      alt="Logo"
      width={width}
      height={height}
      className={className}
      style={{ objectFit: "contain", width, height }}
    />
  );
}
