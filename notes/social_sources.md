# Feeds for forecasting news: LinkedIn, X and open alternatives

Research pass on Nov 13, 2026 (decision 25). Done by a research agent that opened no
LinkedIn post, profile, feed or search page. Items marked "unverified" were not confirmed
on a page it opened. API rules and prices change often; re-check before relying on them.

## LinkedIn

- No official API lets an individual read other members' posts. Self-serve permissions
  cover sign-in and posting as yourself; the rest needs approval or partner status.
  https://learn.microsoft.com/en-us/linkedin/shared/authentication/getting-access
- The data portability API has no feed. It does list saved items as a date and a URL,
  without post text. Its self-serve token is limited to members in the EEA or
  Switzerland.
  https://learn.microsoft.com/en-us/linkedin/dma/member-data-portability/shared/snapshot-domain
- The manual "download your data" export also has saved items (date and URL), works
  outside the EU and covers only your own data.
  https://www.linkedin.com/help/linkedin/answer/a1339364
- The User Agreement (effective 2025-11-03, section 8.2) bars scraping software,
  crawlers and browser plugins, bypassing access limits, and bots or other unauthorised
  automated access. https://www.linkedin.com/legal/user-agreement
- Unverified: whether newsletter editions are emailed to subscribers, whether any
  newsletter RSS exists, what notification digests contain.
- Conclusion: for an automated agent LinkedIn can only be a manually pasted lead. The
  workable routine is to save posts while reading, then paste the post URL, the primary
  source link and a one-line paraphrase into the pipeline. A periodic data export gives
  the list of saved URLs as a checklist. The agent only ever opens the primary source.

## X/Twitter

- Pay-per-use credits, no subscription: $0.005 per post read, $0.010 per user read, cap
  3 million post reads a month. https://docs.x.com/x-api/getting-started/pricing
- Rate limits per 15 minutes per app: recent search 450 requests, list posts 900.
  https://docs.x.com/x-api/fundamentals/rate-limits
- Following one list of about 50 accounts would read an estimated 500 to 2,000 posts a
  week, about $2.50 to $10 a week (the agent's estimate). Not confirmed in the console
  that list and search endpoints are enabled on pay-per-use.
- Developer policy: no circumventing limits, keep stored content in sync with deletions,
  redistribute IDs only. https://docs.x.com/developer-terms/agreement-and-policy
- Unverified: the terms of service page could not be opened.

## Open alternatives (tested the same day)

| Source | Access | Forecasting signal |
|---|---|---|
| arXiv RSS (`rss.arxiv.org/rss/stat.ML+cs.LG+eess.SP`) | free, documented | high but noisy: 685 items in a day, 37 mentioning "forecast" |
| Hugging Face Hub API (`/api/models?pipeline_tag=time-series-forecasting&sort=createdAt`, `/api/daily_papers`) | free, no auth | high for model releases: 8 new repositories in 4 days |
| GitHub release feeds (`/<org>/<repo>/releases.atom`) | free | high for known libraries, none for discovery |
| Zenodo API | free | low to medium: archives and datasets |
| Hacker News API / Algolia search | free | low: about 5 relevant stories in 10 weeks |
| Mastodon public tag timeline | free | low |
| Bluesky author feeds | free without auth; search needs auth; limits unverified | unverified |
| Reddit RSS | reachable; API terms unverified | unverified |

## Ranked options

1. arXiv RSS plus the Hugging Face Hub API, with a keyword filter before judging. Free.
2. GitHub release feeds for a watchlist of 20 to 40 repositories. Free.
3. Manual LinkedIn lead intake: URL, primary link, paraphrase. About 5 minutes a week;
   the only route to practitioner backtests that never reach arXiv.
4. An X list of about 50 accounts through the API: roughly $10 to $40 a month
   (estimate); confirm endpoint availability first.
5. Bluesky author feeds and Hacker News search as cheap secondary feeds.
