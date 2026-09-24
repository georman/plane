/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 *
 * GAM addition: edit the Terms of Service / Privacy Policy (Markdown).
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IFormattedInstanceConfiguration, TInstanceLegalConfigurationKeys } from "@plane/types";
import { Input } from "@plane/ui";
// hooks
import { useInstance } from "@/hooks/store";

type TDoc = "terms" | "privacy";
type TLanguage = "el" | "en";
type TLegalDefaults = Record<TDoc, Record<TLanguage, string>>;

const DOCS: { key: TDoc; label: string }[] = [
  { key: "terms", label: "Terms of Service" },
  { key: "privacy", label: "Privacy Policy" },
];
const LANGUAGES: { key: TLanguage; label: string }[] = [
  { key: "el", label: "Ελληνικά" },
  { key: "en", label: "English" },
];
const textKey = (doc: TDoc, language: TLanguage) =>
  `GAM_LEGAL_${doc.toUpperCase()}_${language.toUpperCase()}` as TInstanceLegalConfigurationKeys;

const today = () => new Date().toLocaleDateString("el-GR", { day: "2-digit", month: "2-digit", year: "numeric" });

export const InstanceLegalForm = observer(function InstanceLegalForm(props: {
  config: IFormattedInstanceConfiguration;
  defaults: TLegalDefaults;
}) {
  const { config, defaults } = props;
  const { updateInstanceConfigurations } = useInstance();
  const [company, setCompany] = useState(config["GAM_LEGAL_COMPANY"] ?? "");
  const [address, setAddress] = useState(config["GAM_LEGAL_ADDRESS"] ?? "");
  // Empty = the standard text, shown so it can be edited
  const [texts, setTexts] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      DOCS.flatMap(({ key: doc }) =>
        LANGUAGES.map(({ key: language }) => [
          textKey(doc, language),
          config[textKey(doc, language)] || defaults[doc][language],
        ])
      )
    )
  );
  const [doc, setDoc] = useState<TDoc>("terms");
  const [language, setLanguage] = useState<TLanguage>("el");
  const [isSaving, setIsSaving] = useState(false);
  const currentKey = textKey(doc, language);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateInstanceConfigurations({
        GAM_LEGAL_COMPANY: company.trim(),
        GAM_LEGAL_ADDRESS: address.trim(),
        GAM_LEGAL_UPDATED: today(),
        ...(texts as Partial<Record<TInstanceLegalConfigurationKeys, string>>),
      });
      setToast({ type: TOAST_TYPE.SUCCESS, title: "Saved", message: "The public pages show the new text." });
    } catch (error: any) {
      setToast({ type: TOAST_TYPE.ERROR, title: "Not saved", message: error?.error ?? "Could not save." });
    } finally {
      setIsSaving(false);
    }
  };

  const tabClass = (active: boolean) =>
    `rounded-md px-3 py-1.5 text-13 ${active ? "bg-layer-1 font-medium text-primary" : "text-tertiary hover:text-primary"}`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-1">
          <span className="text-13 text-secondary">Company (legal name)</span>
          <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Company Ltd" />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-13 text-secondary">Registered address</span>
          <Input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="Street, city, postcode" />
        </label>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-1">
          {DOCS.map(({ key, label }) => (
            <button key={key} type="button" className={tabClass(doc === key)} onClick={() => setDoc(key)}>
              {label}
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          {LANGUAGES.map(({ key, label }) => (
            <button key={key} type="button" className={tabClass(language === key)} onClick={() => setLanguage(key)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <textarea
        value={texts[currentKey]}
        onChange={(e) => setTexts((prev) => ({ ...prev, [currentKey]: e.target.value }))}
        rows={24}
        className="w-full rounded-md border border-subtle bg-surface-1 p-3 font-mono text-13 leading-6"
        aria-label={`${doc} ${language}`}
      />
      <p className="text-12 text-tertiary">
        Markdown: <code>## Heading</code>, <code>**bold**</code>, <code>- list item</code>, tables. [company],
        [address], [brand], [domain] and [email] are filled in automatically (brand and email come from Branding).
        The standard text is a draft: have it checked by a lawyer.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <Button variant="primary" onClick={handleSave} loading={isSaving}>
          {isSaving ? "Saving" : "Save"}
        </Button>
        <Button
          variant="secondary"
          onClick={() => setTexts((prev) => ({ ...prev, [currentKey]: defaults[doc][language] }))}
        >
          Use standard text
        </Button>
        <a
          href={`/legal/${doc}?lang=${language}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-13 text-accent-primary hover:underline"
        >
          Open public page
        </a>
      </div>
    </div>
  );
});
