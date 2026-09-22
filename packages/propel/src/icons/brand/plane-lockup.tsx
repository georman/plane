/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";

import type { ISvgIcons } from "../type";

// Replaced with GAM's own logo (GAM branding, not Plane's). The image is
// served from /assets/gam-logo.png via a separate docker-compose volume
// mount on the web container (see /dockerstor/stacks/plane/branding on
// docker01), not bundled into this build - keep that mount in sync if this
// path ever changes.
export function PlaneLockup({ width = "253", height = "53", className }: ISvgIcons) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/assets/gam-logo.png"
      alt="GAM"
      width={width}
      height={height}
      className={className}
      style={{ objectFit: "contain", width, height }}
    />
  );
}
