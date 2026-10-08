import type { MetadataRoute } from "next";

const site = process.env.SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  // Seat links carry private game rooms; only the landing page is public.
  return { rules: { userAgent: "*", allow: "/", disallow: ["/room/", "/api/"] }, sitemap: `${site}/sitemap.xml` };
}
