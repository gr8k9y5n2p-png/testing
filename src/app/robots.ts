import type { MetadataRoute } from "next";
import { AFTERTAX_ORIGIN } from "@/lib/data-api/config";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    host: AFTERTAX_ORIGIN,
  };
}
