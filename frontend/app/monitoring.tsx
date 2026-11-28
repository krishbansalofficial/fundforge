"use client";

import { useEffect } from "react";

/** Browser error reporting to Sentry's free tier, only when NEXT_PUBLIC_SENTRY_DSN is set. Loaded after the
 *  page is interactive, so it adds nothing to first-load JS. No session replay, no tracing, no tracking:
 *  errors only, with the URL fragment (where seat tokens and sign-in links live) removed. */
export function Monitoring() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (!dsn) return;
    void import("@sentry/browser").then((Sentry) =>
      Sentry.init({
        dsn,
        sendDefaultPii: false,
        // uncaught errors and rejections only: no breadcrumbs of clicks, console or network requests
        defaultIntegrations: false,
        integrations: [Sentry.globalHandlersIntegration(), Sentry.linkedErrorsIntegration(), Sentry.dedupeIntegration()],
        beforeSend(event) {
          if (event.request?.url) event.request.url = event.request.url.split("#")[0];
          delete event.request?.headers;
          return event;
        },
      }));
  }, []);
  return null;
}
