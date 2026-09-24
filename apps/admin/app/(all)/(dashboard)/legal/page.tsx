/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: public Terms of Service / Privacy Policy, in Greek and English.
 * Shown at /legal/terms and /legal/privacy and linked from the login page.
 */

import { observer } from "mobx-react";
import useSWR from "swr";
import { InstanceService } from "@plane/services";
import { Loader } from "@plane/ui";
// components
import { PageWrapper } from "@/components/common/page-wrapper";
// hooks
import { useInstance } from "@/hooks/store";
// types
import type { Route } from "./+types/page";
// local
import { InstanceLegalForm } from "./form";

const instanceService = new InstanceService();

const InstanceLegalPage = observer(function InstanceLegalPage(_props: Route.ComponentProps) {
  const { formattedConfig, fetchInstanceConfigurations } = useInstance();

  useSWR("INSTANCE_CONFIGURATIONS", () => fetchInstanceConfigurations());
  const { data: defaults } = useSWR("INSTANCE_LEGAL_DEFAULTS", () => instanceService.getLegalDefaults());

  return (
    <PageWrapper
      header={{
        title: "Legal",
        description:
          "Terms of Service and Privacy Policy, public at /legal/terms and /legal/privacy and linked from the login page.",
      }}
    >
      {formattedConfig && defaults ? (
        <InstanceLegalForm config={formattedConfig} defaults={defaults} />
      ) : (
        <Loader className="space-y-8">
          <Loader.Item height="50px" width="50%" />
          <Loader.Item height="300px" width="100%" />
        </Loader>
      )}
    </PageWrapper>
  );
});

export const meta: Route.MetaFunction = () => [{ title: "Legal Settings - God Mode" }];

export default InstanceLegalPage;
