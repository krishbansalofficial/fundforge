# Sources and verification boundaries

Checked 6 October 2026 for this redesign. All campaign dollar amounts, horizons, rates, gates, margin coefficients, confidence effects and victory conditions are original fictional house rules. Source material motivates financial concepts; it does not certify this simulator as accurate legal compliance or a deployable investment service.

| Source | Narrow support | Boundary |
|---|---|---|
| [Investor.gov: Hedge Funds](https://www.investor.gov/introduction-investing/investing-basics/investment-products/private-investment-funds/hedge-funds) | Pooled capital, flexible strategies, leverage, fees and limited redemption rights | Does not prescribe this game's contracts or numerical defaults |
| [SEC: T+1 implementation announcement](https://www.sec.gov/newsroom/press-releases/2024-62) | Standard settlement change for most relevant broker-dealer transactions effective May 28, 2024 | Not every instrument, historical era, calendar or broker cash policy |
| [SEC: Key Points About Regulation SHO](https://www.sec.gov/investor/pubs/regsho.htm) | Locate and close-out concepts for short sales | Educational source includes older context; do not implement its historical timing examples as current universal rules |
| [OpenSEO upstream](https://github.com/every-app/open-seo) | SEO research scope and service dependency | Not a financial data engine or evidence of predictive alpha |
| [OpenSEO pinned license](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/LICENSE) | MIT source license, copyright2026 Ben Senescu | Provider data and third-party dependencies have separate terms |
| [OpenSEO pinned manifest](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/package.json) | Actual stack/dependencies at inspected snapshot | No assumption that those versions should be installed into FundForge |
| [OpenSEO provider core](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/lib/dataforseo/core.ts) | Bounded request/error/retry pattern and non-idempotent exception | Not a completed adapter, billing safety audit or free API entitlement |
| [OpenSEO domain tool](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/mcp/tools/get-domain-overview.ts) | Structured, scoped research output | Estimated digital activity must not be represented as company revenue |
| [OpenSEO keyword tool](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/mcp/tools/research-keywords.ts) | Market-scoped keyword research, missing/partial results | Current observations are not point-in-time historical evidence |
| [OpenSEO project authorization](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/mcp/project-auth.ts) | Resource membership gate pattern | FundForge must enforce its own fund/actor authority |
| [OpenSEO cache](https://github.com/every-app/open-seo/blob/ccd2077d47c3ff76fe8787280f2a16c61f1dc2a6/src/server/lib/r2-cache.ts) | Parameter keys, TTL and schema-validation concern | FundForge additionally needs immutable dataset and as-of boundaries |

Repository content was read using the GitHub connection, including the pinned files above and the provider client. Web references were used for public source verification. The afazhriel/openseo result identifies itself as a fork of every-app/open-seo; the upstream is the working interpretation of the user's repo name. A different intended repository remains an explicit assumption to resolve, not a claimed fact.

No source code has been copied in this revision. The proposed adaptation of research, cache, authorization and provider patterns is design work. Financial/game formulas and scenario narratives are original design choices.

Before implementing real market data, recheck provider entitlements, redistribution/retention rights, available-at history, corporate actions and calendars. Before adding a legal-rule teaching module, recheck current primary authority separately. Before implementing framework, SDK, Claude or agent commands, inspect installed versions and current official documentation. Prior package links about coding subscriptions and agent syntax are not treated as freshly verified facts in this revision.
