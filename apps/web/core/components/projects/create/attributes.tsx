/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useParams } from "next/navigation";
import { Controller, useFormContext } from "react-hook-form";
import useSWR from "swr";
// plane imports
import { NETWORK_CHOICES, ETabIndices } from "@plane/constants";
import { translate, useTranslation } from "@plane/i18n";
import type { IProject } from "@plane/types";
import { CustomSelect } from "@plane/ui";
import { getTabIndex } from "@plane/utils";
// components
import { MemberDropdown } from "@/components/dropdowns/member/dropdown";
import { ProjectNetworkIcon } from "@/components/project/project-network-icon";
import { stateTemplateService } from "@/services/state-template.service";

type Props = {
  isMobile?: boolean;
};

function ProjectAttributes(props: Props) {
  const { isMobile = false } = props;
  const { t } = useTranslation();
  const { control } = useFormContext<IProject>();
  const { getIndex } = getTabIndex(ETabIndices.PROJECT_CREATE, isMobile);
  // GAM: the project can start from a state template
  const { workspaceSlug } = useParams();
  const { data: stateTemplates } = useSWR(workspaceSlug ? `GAM_STATE_TEMPLATES_${workspaceSlug}` : null, () =>
    stateTemplateService.fetchTemplates(workspaceSlug as string)
  );
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Controller
        name="network"
        control={control}
        render={({ field: { onChange, value } }) => {
          const currentNetwork = NETWORK_CHOICES.find((n) => n.key === value);

          return (
            <div className="h-7 flex-shrink-0" tabIndex={getIndex("network")}>
              <CustomSelect
                value={value}
                onChange={onChange}
                label={
                  <div className="flex h-full items-center gap-1">
                    {currentNetwork ? (
                      <>
                        <ProjectNetworkIcon iconKey={currentNetwork.iconKey} />
                        {t(currentNetwork.i18n_label)}
                      </>
                    ) : (
                      <span className="text-placeholder">{t("select_network")}</span>
                    )}
                  </div>
                }
                placement="bottom-start"
                className="h-full"
                buttonClassName="h-full"
                noChevron
                tabIndex={getIndex("network")}
              >
                {NETWORK_CHOICES.map((network) => (
                  <CustomSelect.Option key={network.key} value={network.key}>
                    <div className="flex items-start gap-2">
                      <ProjectNetworkIcon iconKey={network.iconKey} className="h-3.5 w-3.5" />
                      <div className="-mt-1">
                        <p>{t(network.i18n_label)}</p>
                        <p className="text-11 text-placeholder">{t(network.description)}</p>
                      </div>
                    </div>
                  </CustomSelect.Option>
                ))}
              </CustomSelect>
            </div>
          );
        }}
      />
      <Controller
        name="project_lead"
        control={control}
        render={({ field: { value, onChange } }) => {
          if (value === undefined || value === null || typeof value === "string")
            return (
              <div className="h-7 flex-shrink-0" tabIndex={getIndex("lead")}>
                <MemberDropdown
                  value={value ?? null}
                  onChange={(lead) => onChange(lead === value ? null : lead)}
                  placeholder={t("lead")}
                  multiple={false}
                  buttonVariant="border-with-text"
                  tabIndex={getIndex("lead")}
                />
              </div>
            );
          else return <></>;
        }}
      />
      {!!stateTemplates?.length && (
        <Controller
          name={"state_template" as keyof IProject}
          control={control}
          render={({ field: { value, onChange } }) => (
            <select
              value={(value as string | undefined) ?? ""}
              onChange={(e) => onChange(e.target.value || undefined)}
              className="h-7 flex-shrink-0 rounded-sm border border-subtle bg-surface-1 px-2 text-12"
              aria-label={translate("gam.st.choose_template")}
              title={translate("gam.st.choose_template")}
            >
              <option value="">{translate("gam.st.default_pipeline")}</option>
              {stateTemplates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          )}
        />
      )}
    </div>
  );
}

export default ProjectAttributes;

export { ProjectAttributes };
