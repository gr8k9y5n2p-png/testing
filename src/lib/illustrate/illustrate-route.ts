import { NextResponse } from "next/server";
import {
  allowDemoEngine,
  getLiveIllustrateUrl,
  proxyLiveDataApiPost,
} from "@/lib/data-api/config";
import { stripMockChromeFromPayload } from "@/lib/illustrate/user-facing-notes";

function asJsonText(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

function tryParseJson(text: string): unknown {
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

/** Live Data API JSON, or localhost demo. Production never runs seed math. */
export async function proxyLiveOrDemo<T>(options: {
  path: string;
  body: unknown;
  mock: () => T;
  unavailableDetail: string;
}): Promise<Response> {
  const live = getLiveIllustrateUrl(options.path);
  if (live) {
    try {
      const upstream = await proxyLiveDataApiPost(live, options.body);
      const text = await upstream.text();
      const parsed = tryParseJson(text);
      const body =
        parsed == null ? text : asJsonText(stripMockChromeFromPayload(parsed));
      return new NextResponse(body, {
        status: upstream.status,
        headers: { "Content-Type": "application/json" },
      });
    } catch {
      return NextResponse.json(
        { detail: options.unavailableDetail },
        { status: 503 },
      );
    }
  }

  if (!allowDemoEngine()) {
    return NextResponse.json(
      { detail: options.unavailableDetail },
      { status: 503 },
    );
  }

  return NextResponse.json(stripMockChromeFromPayload(options.mock()));
}
