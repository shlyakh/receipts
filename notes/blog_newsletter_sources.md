# Blogs and newsletters as scan listings

Research pass on Nov 13, 2026. Question: which specialised blogs and newsletters on
time-series forecasting and on electricity load forecasting could be read by the scan
step as dated listings, next to arXiv, Hugging Face and Zenodo in `tools/feeds.py`.

How it was done: every feed or page below was fetched directly on Nov 13, 2026 with a
generic user agent and no personal details. "In window" means dated items between
2026-07-16 and 2026-11-13 (120 days, `scan.window_days`). No LinkedIn page was opened
and no LinkedIn snippet was used. No article text is stored here; only URLs, counts,
dates and short paraphrases. Nothing in the code, `spec.yaml` or `tools/feeds.py` was
changed. Facts I did not confirm by fetching are marked "not verified".

## 1. Summary

- About 70 feed and page URLs were probed. Roughly 25 are live, dated and usable; the
  rest are dead, have no feed, block automated readers, or are off topic.
- The sources that announce new models or benchmarks with checkable claims are not
  energy blogs. They are (a) research-lab blogs (Amazon Science, Google Research,
  Salesforce), (b) the change logs of the two public leaderboards (GIFT-Eval, fev-bench)
  and (c) a small number of practitioner newsletters that run their own backtests
  (AI Horizon Forecast is the clearest case).
- Energy-specific blogs (Grid Status, PJM Inside Lines, Yes Energy, EIA, Amperon) are
  market and operations commentary. They are useful as context for the benchmark (PJM
  load records, heat and cold events, large-load news) but almost never contain a
  forecasting method with a testable accuracy claim. Tao Hong's blog is the only
  energy-forecasting specialist blog found with a feed, and it posted once in the window.
- Most blog feeds carry only the last 10 to 25 items. Unlike the arXiv or Zenodo
  listings they are not complete for a 120-day window unless the reader runs regularly
  and keeps what it saw before. This matters for the design (section 4).
- Three access facts to decide on before building:
  1. `github.com/robots.txt` disallows `/*.atom$` and `/*/*/commits/` for all agents and
     points to the API. The release and commit feeds work, but the GitHub REST API is
     the route GitHub asks for (checked: 200, 60 requests an hour without a token).
  2. Substack and Medium `robots.txt` disallow named AI crawlers (ClaudeBot,
     anthropic-ai, GPTBot and others). Substack's general block also states
     `ai-input=yes, ai-train=no`. Reading an RSS feed with a generic reader is not what
     those named-crawler rules target, but it is a judgement call for the owner.
  3. `eia.gov/robots.txt` disallows `/rss`, which is where the Today in Energy feed
     lives. `rss.sciencedirect.com/robots.txt` disallows everything (that is the
     International Journal of Forecasting feed).
- The International Institute of Forecasters site returned 403 to every request
  (feed, home page feed link target, `robots.txt`, Foresight). Nothing about it could be
  verified, so it is not proposed.

## 2. Verified sources

Columns: feed = what the feed URL returned; in window = dated items in the last 120
days (a "+" means the feed is capped and the true count may be higher); signal = how
useful for finding claims the judge can check.

### General forecasting

| Source | Who | Focus | Feed (fetched) | Latest / in window | Signal | Access notes |
|---|---|---|---|---|---|---|
| Hyndsight, https://robjhyndman.com/hyndsight/ | Rob Hyndman | general forecasting, statistics | RSS `https://robjhyndman.com/hyndsight/index.xml`: 20 items, dates, full text in description, categories. The site-wide `https://robjhyndman.com/index.xml` (60 items) adds his papers and talks. | 2026-10-28 / 6 | Medium. Mostly commentary, but one post in the window is about how to evaluate foundation-model claims, and new papers appear in the site-wide feed. | No paywall. robots: allow all, crawl-delay 10. |
| AI Horizon Forecast, https://aihorizonforecast.substack.com/ | Nikos Kafritsas | foundation models, practitioner backtests | RSS `/feed`: 20 items, dates, one-line description, full body for free posts. | 2026-11-09 / 7 | High. Posts run named models against tuned baselines on stated data (two electricity-price posts in November). Closest thing found to the "practitioner backtest" the receipt is about. | 12 of 20 items look like truncated previews of paid posts (short body ending in a read-more link); not confirmed by opening the posts. Substack robots: see summary. |
| Amazon Science, time-series tag, https://www.amazon.science/tag/time-series | Amazon researchers | foundation models (Chronos, fev-bench), research | RSS `https://www.amazon.science/tag/time-series.rss`: 10 items, dates, abstract-length descriptions (about 1,400 characters). Items are publication pages. | 2026-11-12 / 10+ (oldest item 2026-07-20) | High. 9 of 10 titles are forecasting papers, each with a paper link. | No paywall. robots: crawl-delay 10. The all-site feed `https://www.amazon.science/index.rss` (25 items) is mostly off topic. Guessed tag feeds for "forecasting" returned 404. |
| Google Research blog, https://research.google/blog/ | Google Research | foundation models (TimesFM) | RSS `https://research.google/blog/rss/`: 100 items, dates, titles only (description is about 18 characters). | 2026-11-11 / 36 | Medium. One forecasting post in the window (TimesFM-3, 2026-08-31); needs a title keyword filter. | No paywall. robots: allow all. The old `blog.research.google` feed stops in March 2024. |
| Salesforce AI research blog category | Salesforce | foundation models (Moirai), GIFT-Eval | RSS `https://www.salesforce.com/blog/category/ai-research/feed/`: 10 items, dates, short description and full body. | 2026-11-09 / 10+ (oldest 2026-08-07) | Medium. One forecasting item in the window (a new contextual-forecasting benchmark, 2026-11-09); the rest is agent and business content. | No paywall. The older `blog.salesforceairesearch.com/rss/` is 404. |
| GIFT-Eval change log, https://github.com/SalesforceAIResearch/gift-eval | Salesforce + submitters | leaderboard | Atom `https://github.com/SalesforceAIResearch/gift-eval/commits/main.atom`: 20 items, dates, commit message. No releases. | 2026-11-13 / 20+ (oldest 2026-10-16) | High. Almost every commit is a new model's results being added, which is a dated, checkable claim. The Hugging Face space `Salesforce/GIFT-Eval` reports only a last-modified time (2026-11-13). | Free. GitHub robots: see summary; use the API. |
| fev / fev-bench change log, https://github.com/autogluon/fev | AutoGluon team + submitters | leaderboard | Atom `https://github.com/autogluon/fev/commits/main.atom`: 20 items since 2026-10-01. Releases feed: 1 in window. | 2026-11-11 / 20+ | High, same reason. Mixed with ordinary maintenance commits; filter on "results". | Free. Same GitHub note. |
| GitHub release feeds of model and library repos | maintainers | releases | Atom `/<org>/<repo>/releases.atom`: 10 items, dates, release notes as content. Fetched and live: `amazon-science/chronos-forecasting` (1 in window), `google-research/timesfm` (2, incl. 3.0 on 2026-08-28), `autogluon/autogluon` (4), `Nixtla/neuralforecast` (4), `Nixtla/nixtla` (5), `Nixtla/statsforecast` (1), `ibm-granite/granite-tsfm` (6), `PriorLabs/tabpfn-time-series` (2), `sktime/sktime` (4), `unit8co/darts` (5), `skforecast/skforecast` (4), `TimeCopilot/timecopilot` (10), `awslabs/gluonts` (2), `Nixtla/hierarchicalforecast` (2), `facebook/prophet` (3, now redirects to `meta/prophet`). | varies | Medium. Exact dates for known projects, no discovery. Release notes rarely state accuracy numbers. | Free. Same GitHub note. Zero in window: `DataDog/toto` (last 2026-06-04), `SalesforceAIResearch/uni2ts` (last 2025-11-04), `NX-AI/tirex`, `Nixtla/mlforecast`, `sktime/pytorch-forecasting`. No releases at all: `moment`, `lag-llama`, `microsoft/ProbTS`. |
| OpenForecast, https://openforecast.org/ | Ivan Svetunkov | classical methods, forecast evaluation | RSS `https://openforecast.org/feed/`: 10 items, dates, summary (about 800 characters) and full body. | 2026-11-09 / 10+ (oldest 2026-09-14, roughly weekly) | Low to medium. Teaching and method notes (exponential smoothing, intermittent demand); useful for baseline thinking, few benchmark claims. | No paywall. robots: allow all. |
| Nixtla blog, https://www.nixtla.io/blog | Nixtla | practitioner, TimeGPT | No feed (`/rss.xml`, `/feed.xml`, `/blog/rss.xml`, `/blog/feed` all 404; no feed link in the page). `https://www.nixtla.io/sitemap.xml` lists 30 blog URLs with a last-modified date. | 2026-10-13 / 5 by last-modified | Low to medium. Tutorials and product news; model announcements appear here first for TimeGPT. | No paywall. Dates are last-modified, not publication. |
| Medium author feeds | individual writers | practitioner | RSS `https://medium.com/feed/@<name>` or `https://<name>.medium.com/feed`: 10 items, dates; summary only for member posts. Fetched: `@nikoskafritsas` (3 in window, same posts as AI Horizon), `valeman.medium.com` (9, mixed topics, one large benchmark post), `@marcopeixeiro` (1). | varies | Medium for the first, low otherwise. | Member paywall on many posts. Medium robots: see summary. |
| Medium tag feeds | anyone | mixed | RSS `https://medium.com/feed/tag/time-series-forecasting`: 9 items covering 4 days. `.../tag/energy-forecasting`: 8 items, 2 in window (both small load-forecast backtests). `.../tag/load-forecasting`: 0 in window. | daily / high volume | Low. Mostly tutorials and stock-price posts; the energy tag is quiet but on topic. | As above. |
| Forecasting Impact podcast (IIF) | IIF volunteers | interviews | RSS `https://rss.buzzsprout.com/1641538.rss`: 52 items, dates, show notes (about 1,000 characters). | 2026-08-11 / 1 | Low. Interviews, no method claims. | Free. |
| Hugging Face blog | HF and community | all ML | RSS `https://huggingface.co/blog/feed.xml`: 907 items, dates, titles only. | 2026-11-13 / 82 | Low. No forecasting title in the window. The Hub model listing already used by `feeds.py` is the better Hugging Face source. | Free. robots: allow all. |
| Adjacent Substacks | various | tabular models, data science, quant | All RSS `/feed`, 20 items, dates, full body. `mindfulmodeler` (Christoph Molnar per search result, 2 in window, last 2026-07-22), `ramikrispin` (20, weekly link digest), `quantailab` (12, finance, partly paid). | varies | Low. Occasional forecasting items; mostly pointers to things the other listings already catch. | Substack note. |

### Energy and load forecasting

| Source | Who | Focus | Feed (fetched) | Latest / in window | Signal | Access notes |
|---|---|---|---|---|---|---|
| Energy Forecasting, http://blog.drhongtao.com/ | Tao Hong | load forecasting research, competitions | Atom `https://blog.drhongtao.com/feeds/posts/default` (25 items, dates, full body); `?alt=rss` also works. | 2026-08-07 / 1 (2 posts in 2026) | Medium when it posts: competition and call-for-papers announcements, benchmark discussion. Very low volume. | Free. Blogger platform. |
| Grid Status blog, https://blog.gridstatus.io/ | Grid Status staff (several authors) | US power markets analysis | RSS `https://blog.gridstatus.io/rss/`: 15 items, dates, short description, full body, topic tags (ISO names). | 2026-10-27 / 5 | Context only. Long data-driven market pieces; one in the window is about load-forecast misses in the East, one covers PJM heat. No methods. | Free. robots allows the feed. |
| PJM Inside Lines, https://insidelines.pjm.com/ | PJM communications | PJM operations and policy news | RSS `https://insidelines.pjm.com/feed/`: 10 items, dates, summary and full body, categories. | 2026-11-10 / 10+ (oldest 2026-10-12, about 10 a month) | Context only, but it is our benchmark's operator: seasonal outlooks, alerts, record and large-load news that explain odd weeks in the JC and DOM series. | Free. robots allows the feed. No feed found on `pjm.com` itself. |
| Yes Energy blog | Yes Energy (vendor) | power market data, demand | RSS `https://www.yesenergy.com/blog/rss.xml` (the old `blog.yesenergy.com/yeblog/rss.xml` redirects here): 10 items, dates, summary, tags. | 2026-11-06 / 10+ (oldest 2026-09-09) | Low. Vendor explainers; a demand series in September, one PJM price-spike review. No reproducible claims. | Free. |
| EIA Today in Energy | US EIA | energy statistics | RSS `https://www.eia.gov/rss/todayinenergy.xml`: 27 items, dates, summary. | 2026-11-13 / 26+ (oldest 2026-09-01) | Context only. Three load items in the window (ISO peak records, ERCOT weekly load). | Free, public-domain source, but `robots.txt` disallows `/rss`. |
| ISO Newswire (ISO New England) | ISO-NE | operator news | RSS `https://isonewswire.com/feed/`: 10 items since 2026-10-30. | 2026-11-13 / 10+ | Context only, and not our region. | Free. |
| Open Climate Fix insights, https://www.openclimatefix.org/insights | Open Climate Fix | solar, wind and demand forecasting (open source) | No feed (`/blog` and `/rss.xml` are 404, no feed link). The page shows dated posts. The repo release feed `openclimatefix/open-source-quartz-solar-forecast/releases.atom` works (1 in window). | 2026-11-03 / about 7 on the page since 2026-09-30 | Low to medium. Solar-focused; some posts describe model changes. | Free. Would need page scraping. |
| Amperon, https://www.amperon.co/resources | Amperon (vendor) | load and renewable forecasting | No feed. `/blog` redirects to a resources page; `sitemap.xml` lists 182 blog URLs but many share one bulk last-modified date, so dates are unreliable. | page shows 2026-10-22 as newest dated item | Low. Vendor posts; accuracy claims are about a closed product (it offers a "back-test request" form, not public numbers). | Free to read. |
| dynamical.org updates | dynamical.org | open weather-forecast archives | Atom `https://dynamical.org/feed/feed.xml`: dates and titles. | 2026-10-08 / about 5 | Not forecasting methods. Relevant only to the weather-input side (archived forecast data). | Free. |
| Utility Dive, RTO Insider, Latitude Media | trade press | industry news | RSS feeds live: `utilitydive.com/feeds/news/` (10 items over 3 days), `rtoinsider.com/feed/` (10 items over 2 days), `latitudemedia.com/feed/` (10 items over 4 days). | daily | Low for our purpose, high volume. | RTO Insider paywall not verified. |

## 3. Recommended first set

Eleven entries. Feed URLs are exactly what was fetched. For the GitHub entries the
Atom URL is given because that is what was tested; section 4 explains why the API
should be used instead.

| # | Source | Feed URL | Why |
|---|---|---|---|
| 1 | AI Horizon Forecast | `https://aihorizonforecast.substack.com/feed` | Best source of practitioner backtests with named models, baselines and data. 7 posts in window, nearly all on topic. Decide the Substack robots question first. |
| 2 | Amazon Science, time-series tag | `https://www.amazon.science/tag/time-series.rss` | Chronos and fev-bench team output with abstracts and paper links. Only 10 items, so read it at least monthly. |
| 3 | Google Research blog | `https://research.google/blog/rss/` | Where TimesFM versions are announced. Titles only; filter on title. |
| 4 | Salesforce AI research | `https://www.salesforce.com/blog/category/ai-research/feed/` | Moirai and GIFT-Eval announcements. Only 10 items; read at least monthly. |
| 5 | GIFT-Eval change log | `https://github.com/SalesforceAIResearch/gift-eval/commits/main.atom` | Each new leaderboard entry is a dated, checkable claim, often for models that have no paper yet. |
| 6 | fev-bench change log | `https://github.com/autogluon/fev/commits/main.atom` | Same, second leaderboard. Filter commit messages on "results". |
| 7 | Release feeds, model repos | `https://github.com/<org>/<repo>/releases.atom` for `amazon-science/chronos-forecasting`, `google-research/timesfm`, `SalesforceAIResearch/uni2ts`, `DataDog/toto`, `ibm-granite/granite-tsfm`, `PriorLabs/tabpfn-time-series`, `NX-AI/tirex`, `Nixtla/nixtla`, `Nixtla/neuralforecast`, `autogluon/autogluon` | Exact release dates for the models on our leaderboard; feeds rule 13 (pinned weights and their dates). |
| 8 | Hyndsight | `https://robjhyndman.com/hyndsight/index.xml` | Low volume, high authority on evaluation practice; one directly relevant post in the window. Respect crawl-delay 10. |
| 9 | Tao Hong, Energy Forecasting | `https://blog.drhongtao.com/feeds/posts/default` | The one specialist load-forecasting blog with a feed. One or two posts a year, so it costs nothing and catches competition announcements. |
| 10 | PJM Inside Lines | `https://insidelines.pjm.com/feed/` | Context for our benchmark zones (alerts, outlooks, records). Label rows as context, not candidates. Only 10 items, about one month; read weekly. |
| 11 | Grid Status blog | `https://blog.gridstatus.io/rss/` | Best free data-driven commentary on US load and forecast misses. Context, not candidates. |

Second tier, add later if the first set proves too thin: OpenForecast
(`https://openforecast.org/feed/`), Medium energy tag
(`https://medium.com/feed/tag/energy-forecasting`), Yes Energy
(`https://www.yesenergy.com/blog/rss.xml`), EIA Today in Energy
(`https://www.eia.gov/rss/todayinenergy.xml`, robots question), the Nixtla sitemap
(`https://www.nixtla.io/sitemap.xml`), the site-wide Hyndman feed
(`https://robjhyndman.com/index.xml`).

## 4. Sketch: extending `tools/feeds.py`

Not implemented; this is the proposed shape.

**One generic reader.** A function `rss(cfg, start, end)` that fetches one URL, parses
it with `xml.etree` as the arXiv reader already does, and accepts both RSS (`item`) and
Atom (`entry`). Field mapping seen in the fetched feeds:

- date: `pubDate` (RSS), `published` then `updated` (Atom), `dc:date`. If none parses,
  write `published_at: "unknown"` and keep the row (same convention as Zenodo).
- link: text of `link` (RSS) or its `href` attribute (Atom). Strip tracking query
  strings such as Medium's `?source=rss...`.
- author: `dc:creator`, `author/name`, else the feed's configured owner.
- text: `description` or `summary`, else `content:encoded` or `content`, tags removed.

**Config block in `spec.yaml`** under `scan.feeds`, one entry per source:

```yaml
    blogs:
      any_of: [forecast, time series, foundation model, zero-shot, load, demand, benchmark]
      sources:
        - {name: amazon_science_ts, url: "https://www.amazon.science/tag/time-series.rss", filter: none}
        - {name: google_research,   url: "https://research.google/blog/rss/", filter: title}
        - {name: pjm_inside_lines,  url: "https://insidelines.pjm.com/feed/", filter: title_and_text, role: context}
        - {name: gift_eval_log,     kind: github_commits, repo: SalesforceAIResearch/gift-eval, any_of: [results, submission]}
        - {name: chronos_releases,  kind: github_releases, repo: amazon-science/chronos-forecasting, filter: none}
        - {name: nixtla_blog,       kind: sitemap, url: "https://www.nixtla.io/sitemap.xml", path_prefix: /blog/}
```

- `filter: none` for feeds that are already on topic; `title` for feeds without
  summaries (Google Research, Hugging Face blog); `title_and_text` otherwise. Matching
  works like the arXiv `any_of` list and the matched words go in the `matched` column.
- `role: context` marks operator and market feeds so `/scan` does not turn them into
  candidates.
- `kind: github_releases` and `github_commits` call `api.github.com/repos/<repo>/releases`
  and `/commits` instead of the Atom URLs, because GitHub's robots file disallows the
  Atom paths and names the API as the alternative. The releases endpoint was tested
  (200, limit 60 an hour unauthenticated). The commits endpoint was not tested. With
  about 12 repositories a run uses about 12 requests; a token is not needed.
- `kind: sitemap` reads `loc` and `lastmod`; rows are labelled as last-modified dates.

**Committed vs git-ignored.** Same split as today. `candidates/feeds/feeds_<date>.jsonl`
(committed): `source, url, title, published_at, authors_or_owner, matched`, plus `role`
if added. `data/feeds/abstracts_<date>.jsonl` (git-ignored): the summary or body text,
cut to 3,000 characters as for Zenodo, read locally with `--show`. Several feeds carry
the full article (Hyndsight, Grid Status, Substack free posts), so the cut matters for
rule 9: other people's text never reaches a commit.

**Capped feeds.** arXiv, Hugging Face and Zenodo return everything in the window. Most
blog feeds return the last 10 to 25 items, which for PJM Inside Lines is one month and
for the Datadog blog under three months. Two consequences: (a) the reader should merge
with rows from earlier runs instead of overwriting, and (b) it should print, per feed,
the oldest item date so a gap between that date and the window start is visible
("pjm_inside_lines: 10 items, oldest 2026-10-12, window starts 2026-07-16: not
complete").

**Politeness and failure.** Keep the existing "report, do not hide" behaviour per
feed. Wait between requests to the same host (10 seconds for `robjhyndman.com` and
`amazon.science`, which state a crawl-delay). Keep the current generic user agent.
Refuse any configured URL on `linkedin.com` (rule 10).

**What a blog row is.** A pointer, not evidence. The judge should follow it to the
primary source (paper, repository, model card) and cite that, as it does for a web
search hit.

## 5. Not verified, and rejected

### Could not verify

- **International Institute of Forecasters** (`forecasters.org`: site feed, Foresight,
  Oracle newsletter): HTTP 403 on every URL including `robots.txt`, with two generic
  user agents. The home page HTML (fetched once, 200) advertises a feed at
  `/feed/`, but that URL returns 403. Not retried with a disguised browser agent.
- **IEEE PES Working Group on Energy Forecasting and Analytics**: `site.ieee.org`
  returned 403. A search result says the page exists under the PSOPE committee; chair
  and activity not verified. No feed found.
- **NREL news**: `www.nrel.gov` did not resolve. `www.nlr.gov/news` loads (title "News |
  NLR") and offers only an email sign-up page; no feed link, guessed `/news/rss.xml` is
  404. Whether another feed exists was not established.
- **AI Horizon Forecast paywall share**: inferred from short bodies in the feed, not
  from opening posts.
- **RTO Insider paywall, Reddit API terms, Substack and Medium terms of service pages**:
  not read. Only `robots.txt` was checked.
- **GitHub API commits endpoint**: only the releases endpoint was called.
- Authors: taken from the feed's author field for AI Horizon Forecast, OpenForecast,
  Grid Status, PJM. Hyndsight's feed has no author field; the attribution to Rob Hyndman
  is from the site name. "Christoph Molnar" for Mindful Modeler is from a search
  result only.

### Rejected

| Source | Reason |
|---|---|
| Datadog blog (`datadoghq.com/blog/index.xml`, `/blog/ai/index.xml`) | Live, but 97 items in under 3 months are product posts; the AI sub-feed had no forecasting item in the window. Follow `DataDog/toto` releases instead. |
| Unit8 (`unit8.com/resources/feed/`) | Live, 2 items in window, both consulting topics. Darts news is in the GitHub releases. |
| sktime, skforecast, Darts websites | No feed on the sites; releases are on GitHub. |
| Forecasting: Principles and Practice (`otexts.com/fpp3`) | No feed or news page; book news appears on Hyndsight. |
| M-competitions | `m6competition.com/feed/` is a valid but empty feed; the University of Nicosia page is static with no feed and shows nothing newer than M6. `mofc.unic.ac.cy` redirects to a 404. |
| Papers with Code | `paperswithcode.com/task/time-series-forecasting` now redirects to Hugging Face trending papers. Hugging Face `api/daily_papers` works but is a general list. |
| International Journal of Forecasting RSS (`rss.sciencedirect.com/publication/science/01692070`) | Live, 73 items, but no date field (the date is a phrase inside the description), mostly macro and finance, and the host's `robots.txt` disallows everything. |
| Hugging Face blog feed | Titles only, no forecasting title in the window. |
| Medium tag `time-series-forecasting`, Towards Data Science, KDnuggets, Machine Learning Mastery feeds | Live, but high volume and tutorial or off-topic content; the category feeds of the last two return general posts. |
| Electricity Maps | No feed; `/blog` redirects to a publications page; carbon-accounting focus. |
| Modo Energy | No feed (`/rss.xml` 404); research page contains paywall and log-in markers; storage-market focus. |
| Enertel | Feed `enertel.ai/blog-feed.xml` is live but the last post is 2025-12-18, and the blog page title now carries another company's name. |
| Ascend Analytics | No feed (`/blog`, `/blog/rss.xml` 404); category pages are mostly webinars and case studies. |
| Energy-Charts | Data application; no news page or feed found. |
| Relae blog | Active (5 posts in the first half of November), no feed, vendor content. Found by search, not on the original list. |
| Open-Meteo Substack | 1 post in window; weather API news. |
| Reddit `r/forecasting` | Feed reachable; last item 2026-04-27, off topic. A search feed on `r/MachineLearning` returned 403. |
| Cross Validated `forecasting` tag feed | Questions and answers, not announcements. |
| "Awesome" paper lists (`ddz16/TSFpaper`, `qingsongedu/Awesome-TimeSeries-SpatioTemporal-LM-LLM`, `thuml/Time-Series-Library`, `thuml/OpenLTM`) | Commit feeds live but stale: 2, 0, 0 and 0 commits in the window. |
| `timeseries.substack.com`, `epforecasting.blogspot.com`, `microprediction.com/blog`, Itron forecasting blog, ERCOT, CAISO, MISO and NYISO guessed feed paths | Dead, empty or 404 at the URLs tried. |
| ECMWF news, IBM Research blog, Lokad blog, Kaggle competitions | Pages load but no feed found; not forecasting-method sources for this benchmark. |

### LinkedIn-only, excluded

None identified by name in this pass. No LinkedIn page was opened to look for any.
Several of the writers above also post on LinkedIn; only their blog or newsletter feed
is proposed.
