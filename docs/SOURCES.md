# Official sources and verification boundaries

Checked 6 October 2026. These sources support narrowly identified facts; the game's mandate, scoring, architecture, account policies and hypothetical fee terms are original proposed design choices. This is not a comprehensive legal review. Recheck changing APIs, entitlements, CLI syntax, installed Claude features and legal modules at implementation time.

| ID | Source | Used for |
|---|---|---|
| S1 | [SEC/Investor.gov: Investor Bulletin — Investment Clubs](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-33) | Active/passive membership and fact-specific regulatory questions; not an exemption guarantee |
| S2 | [SEC: Starting a Private Fund](https://www.sec.gov/about/starting-private-fund) | Real entity, document, adviser and offering considerations |
| S3 | [Investor.gov: New T+1 Settlement Cycle](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor-bulletin) | Modern applicable U.S. settlement; not historical-era or every broker account rules |
| S4 | [Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders) and [Order Types Bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-14) | Market/limit/stop distinctions and execution uncertainty |
| S5 | [SEC: Division of Trading and Markets Regulation SHO FAQ](https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions-8) | Short-sale requirements context; simulated borrowing is not full compliance |
| S6 | [Alpaca: Historical bars](https://docs.alpaca.markets/us/reference/stockbarsingle-1) | Feed/adjustment/as-of/pagination metadata; not data redistribution permission |
| S7 | [Anthropic: Use Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) | Shared subscription usage; distinct API billing; no weekly-fit promise |
| S8 | [Claude Code: Best practices](https://code.claude.com/docs/en/best-practices) | Scoped working context and verification workflow |
| S9 | [Claude Code: Create custom subagents](https://code.claude.com/docs/en/sub-agents) and [Manage costs](https://code.claude.com/docs/en/costs) | Agent configurations, usage/context considerations; verify installed support |
| S10 | [Claude Code: Agent teams](https://code.claude.com/docs/en/agent-teams) | Optional multi-session teamwork and its overhead; availability may vary |
| S11 | [GitHub CLI: gh repo create](https://cli.github.com/manual/gh_repo_create) | --private, --source, --remote and --push repository setup |
| S12 | [Vercel Labs: agent-skills](https://github.com/vercel-labs/agent-skills) | Official skill collection; actual locally installed names must be inspected |

The supplied resume was read directly from the attached PDF to ground the project's resume fit. It is not included in the repository; its existing claims were not independently audited. The package makes no new personal accomplishment claim.

## Checks to perform later

Provider data terms/entitlements; original exchange calendars and historical settlement eras; auth SDK and deployment versions; current Claude usage/model/agent interfaces; advanced short/margin/derivatives rule modules if added. A source check in this document does not freeze external facts forever.
