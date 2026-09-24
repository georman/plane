/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { EAuthModes } from "@plane/constants";
import { translate, useTranslation } from "@plane/i18n";

interface TermsAndConditionsProps {
  authType?: EAuthModes;
}

// GAM: public pages served by the api (text edited in God mode > Legal)
const legalLink = (doc: "terms" | "privacy", language: string) =>
  `/legal/${doc}?lang=${language === "el" ? "el" : "en"}`;

// Plain <a>: these pages are outside the app, so they must load from the server
function LegalLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} className="text-secondary" target="_blank" rel="noopener noreferrer">
      <span className="text-13 font-medium underline hover:cursor-pointer">{children}</span>
    </a>
  );
}

export function TermsAndConditions({ authType = EAuthModes.SIGN_IN }: TermsAndConditionsProps) {
  const { currentLocale } = useTranslation();
  return (
    <div className="flex items-center justify-center">
      <p className="text-center text-13 whitespace-pre-line text-tertiary">
        {translate(authType === EAuthModes.SIGN_UP ? "gam.legal.by_signing_up" : "gam.legal.by_signing_in")}{" "}
        <LegalLink href={legalLink("terms", currentLocale)}>{translate("gam.legal.terms")}</LegalLink>{" "}
        {translate("gam.legal.and")}{" "}
        <LegalLink href={legalLink("privacy", currentLocale)}>{translate("gam.legal.privacy")}</LegalLink>.
      </p>
    </div>
  );
}
