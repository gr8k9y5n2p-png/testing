import type { MetadataRoute } from "next";
import { isStagingPublicOrigin, publicOrigin } from "@/lib/hosts";

export default function robots(): MetadataRoute.Robots {
  const origin = publicOrigin();
  if (isStagingPublicOrigin(origin)) {
    return {
      rules: { userAgent: "*", disallow: "/" },
    };
  }
  return {
    rules: { userAgent: "*", allow: "/" },
    host: origin,
  };
}
