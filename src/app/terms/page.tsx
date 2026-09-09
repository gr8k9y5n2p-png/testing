import type { Metadata } from "next";
import { LegalArticle } from "@/components/LegalArticle";
import { TERMS } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Terms of Use — Aftertax",
  description: "Terms of Use for Aftertax, operated by Aftertax LLC.",
};

export default function TermsPage() {
  return <LegalArticle document={TERMS} />;
}
