/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: apply a state template to the project (project admins).
 */

import { useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
import { translate } from "@plane/i18n";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { useProjectState } from "@/hooks/store/use-project-state";
import { stateTemplateService } from "@/services/state-template.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
};

export const ApplyStateTemplate = observer(function ApplyStateTemplate({ workspaceSlug, projectId }: Props) {
  const { fetchProjectStates } = useProjectState();
  const [templateId, setTemplateId] = useState("");
  const [isApplying, setIsApplying] = useState(false);
  const { data: templates } = useSWR(`GAM_STATE_TEMPLATES_${workspaceSlug}`, () =>
    stateTemplateService.fetchTemplates(workspaceSlug)
  );

  if (!templates?.length) return null;

  const handleApply = async () => {
    if (!templateId || !window.confirm(translate("gam.st.apply_confirm"))) return;
    setIsApplying(true);
    try {
      const result = await stateTemplateService.applyToProject(workspaceSlug, projectId, templateId);
      await fetchProjectStates(workspaceSlug, projectId);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: translate("gam.st.apply"),
        message:
          translate("gam.st.applied", { added: result.added, updated: result.updated, removed: result.removed }) +
          (result.kept.length ? " " + translate("gam.st.kept", { names: result.kept.join(", ") }) : ""),
      });
      setTemplateId("");
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Error", message: error?.error ?? "Could not apply the template." });
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2">
      <select
        value={templateId}
        onChange={(e) => setTemplateId(e.target.value)}
        className="rounded-sm border border-subtle bg-surface-1 px-2 py-1.5 text-13"
        aria-label={translate("gam.st.choose_template")}
      >
        <option value="">{translate("gam.st.choose_template")}…</option>
        {templates.map((template) => (
          <option key={template.id} value={template.id}>
            {template.name}
          </option>
        ))}
      </select>
      <Button variant="secondary" size="sm" onClick={handleApply} disabled={!templateId} loading={isApplying}>
        {translate("gam.st.apply")}
      </Button>
    </div>
  );
});
