import type { Metadata } from "next";
import { LegalArticle } from "@/components/LegalArticle";
import { PRIVACY } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Privacy Policy — Aftertax",
  description: "Privacy Policy for Aftertax, operated by Aftertax LLC.",
};

export default function PrivacyPage() {
  return <LegalArticle document={PRIVACY} />;
}
