/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: white-label brand settings (name, support email, website,
 * logo). The name replaces the upstream product name everywhere: all apps,
 * all languages, emails and error pages.
 */

import { observer } from "mobx-react";
import useSWR from "swr";
import { Loader } from "@plane/ui";
// components
import { PageWrapper } from "@/components/common/page-wrapper";
// hooks
import { useInstance } from "@/hooks/store";
// types
import type { Route } from "./+types/page";
// local
import { InstanceBrandingForm } from "./form";

const InstanceBrandingPage = observer(function InstanceBrandingPage(_props: Route.ComponentProps) {
  const { formattedConfig, fetchInstanceConfigurations } = useInstance();

  useSWR("INSTANCE_CONFIGURATIONS", () => fetchInstanceConfigurations());

  return (
    <PageWrapper
      header={{
        title: "Branding",
        description: "Your name, support email, website and logo. They are shown everywhere in the apps and emails.",
      }}
    >
      {formattedConfig ? (
        <InstanceBrandingForm config={formattedConfig} />
      ) : (
        <Loader className="space-y-8">
          <Loader.Item height="50px" width="50%" />
          <Loader.Item height="50px" width="30%" />
        </Loader>
      )}
    </PageWrapper>
  );
});

export const meta: Route.MetaFunction = () => [{ title: "Branding Settings - God Mode" }];

export default InstanceBrandingPage;
