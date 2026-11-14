# Hackathon tools: You.com, OpenCrawl, Treg, and the narrated video

Research pass on Fri Nov 13, 2026, for the hackathon on Sat Nov 14. Every URL below was
read on 2026-11-13. Web research only: no You.com API call was made, no integration
code was written, `.env` was not read, no LinkedIn page or snippet was used. Facts are
short paraphrases; no page text is stored.

## 0. What the two unclear names are

Both appear in the sponsor list of the event page (https://luma.com/live-agents-hack-nyc).

| As typed | What it is | Confidence |
|---|---|---|
| "open Crawl search" | **OpenCrawl** (getopencrawl.com), Silver sponsor. It is NOT a web crawler or a web search API. It is shared memory and a message board for coding agents: it records agent sessions (Claude Code, Codex and others) and lets agents search them. The event has a prize "Best use of OpenCrawl", $250. | High (event page links to getopencrawl.com) |
| "treg" | **Treg** (treg.to), Community sponsor. A gateway ("OpenRouter for agent tools"): one token, pay per call, for a catalog of about 4,100 third-party API endpoints, including web search, scraping, text-to-speech, image and video generation. | High (event page links to treg.to) |

Event facts from the same page: prizes are 1st overall ($500 + $1.75K You.com credits),
Best use of OpenCrawl ($250), Best Content ($150). Free You.com credits for every
builder (amount not stated). No sponsor tool other than You.com is required. Opencrawl
and Treg credits for attendees are not mentioned on the page.

## 1. You.com

Sources: https://you.com/docs/llms.txt (index), https://you.com/docs/quickstart.md,
https://you.com/docs/rate-limits.md, https://you.com/docs/agents/mcp-server.md,
https://you.com/docs/agents/agent-harnesses/claude-code.md,
https://you.com/docs/agents/skills.md,
https://you.com/docs/guides/search/request-controls.md,
https://you.com/docs/guides/search/retrieve-page-content.md,
https://you.com/docs/guides/search/live-news.md, https://you.com/docs/guides/contents.md,
https://you.com/docs/guides/research.md,
https://you.com/docs/guides/research/source-control.md,
https://you.com/docs/guides/research/structured-output.md,
https://you.com/docs/api-reference/llms.txt,
https://you.com/docs/api-reference/images/images.md, https://you.com/docs/youbot.
OpenAPI spec (not read): https://you.com/docs/openapi.json.

### APIs

| API | Endpoint | What matters for us | Price |
|---|---|---|---|
| Web Search | `POST https://ydc-index.io/v1/search`, header `X-API-Key` | `query` (operators `site:`, `filetype:`, `lang:`), `count` 1 to 100 (default 10), `offset` 0 to 9, `freshness` = `day`/`week`/`month`/`year` or `YYYY-MM-DDtoYYYY-MM-DD`, `include_domains` (max 500, strict allowlist), `exclude_domains`, `boost_domains` (not with `include_domains`), `country`, `language`. Page text in the same call: `extraction.extraction_mode` = `highlights` (count max 50) or `full_page` (markdown/html; source `blend`/`cache`/`fetch`). Results in `results.web[]` with `title`, `url`, `description`, `page_age` (ISO date) | $5 per 1k calls; live-fetched full pages +$1 per 1k, cached free |
| News | no separate endpoint | news items come back inside `results.web` when the query has news intent; use `freshness` | as Search |
| Contents | `POST https://ydc-index.io/v1/contents` | `urls` (max 10 per call), `formats` markdown/html/metadata, `crawl_timeout` 1 to 60 s, `max_age` (0 = always re-fetch). Failed URLs return null. Very long PDFs: 422 `pdf_too_large` | $1 per 1k pages |
| Research | `POST https://api.you.com/v1/research` | `input` (max 40,000 chars), `research_effort` lite/standard/deep/exhaustive/frontier, `source_control` (same domain and freshness fields as Search; beta), `output_schema` (JSON Schema subset; not with `lite`; beta), `background` (needed for frontier). Returns `output.content` with inline `[[n]]` citations and `output.sources[]` (`url`, `title`, `snippets`) | per call: lite $0.012, standard $0.05, deep $0.10, exhaustive $0.45, frontier $1.20 |
| Answer | `POST https://api.you.com/v1/answer` | one cited answer; not exposed as an MCP tool | $5 per 1k |
| Finance Research | `POST https://api.you.com/v1/finance_research` | not relevant to us | $0.11 to $0.50 per call |
| Images | `GET https://api.you.com/v1/images` | image search (not generation); beta, early-access partners only | not listed |
| Inference Router | `https://api.you.com/v1/chat/completions`, `/v1/messages` | LLM routing; not needed | by model |
| Account balance | see API reference | check credits left | free |

Limits: 10 requests per second on Search, Contents, Answer and Research for self-serve
accounts; 429 with `Retry-After` when exceeded; `X-RateLimit-*` headers on every
response. Research latency: lite under 10 s, standard 10 to 30 s, deep under 120 s,
exhaustive under 300 s (set client timeouts accordingly or use `background`).

Structured output detail that matters for `/judge`: with `output_schema`, sources stay
in `output.sources`; the API does not add citation fields to our schema. Every object
needs `additionalProperties: false` and all properties `required`; no `pattern`,
`format`, `minItems` and similar; depth max 5, max 100 properties. Our scorecard schema
will probably need a reduced copy for this call.

### Hosted MCP server

| Item | Finding |
|---|---|
| URL | `https://api.you.com/mcp`; also `https://api.you.com/mcp/research` (research only) |
| Auth | `Authorization: Bearer <key>`, or OAuth (connect with no header), or keyless `?profile=free` (you-search + you-discover, 100 queries a day) |
| Tool names | `you-search`, `you-contents`, `you-research`, `you-finance`, `you-balance`, `you-discover` (six; there is no answer tool) |
| Default set | `you-search`, `you-contents`, `you-balance`, `you-discover`. `you-research` is off unless requested with `?tools=you-search,you-contents,you-research` (or header `X-Allowed-Tools`), or by adding the `/mcp/research` endpoint as a second server. This confirms the line in `REFERENCE.md` |
| `you-search` arguments | `query`, `count`, `freshness`, `offset`, `extraction`, `extraction_source`, `crawl_timeout`, `knowledge`, `safesearch`, `exclude_domains`. **`include_domains`, `boost_domains`, `language`, `country` are host-only** (set through `X-Search-*` headers or `_meta`, not by the model). In practice: restrict domains with `site:` in the query, or call the REST API for a strict allowlist |
| Claude Code | `claude mcp add --transport http you-com https://api.you.com/mcp --header "Authorization: Bearer <key>"`. Alternative: plugin `youdotcom-oss/agent-skills` (`/plugin install you@you-com`), which adds skills `you-web`, `you-research`, `you-finance`, `you-discover` |
| Names inside Claude Code | expected `mcp__you-com__you-search` and so on; the docs do not state them, confirm with `/mcp` |

Robots: You.com's crawler page says YouBot fully respects `robots.txt`, including
per-agent rules and crawl-delay. It does not say whether live fetches made by the
Contents API follow the same rules.

### How our three skills would use it

| Skill | Capability in `providers.md` | You.com call |
|---|---|---|
| `/scan` | `search(query, since, domains)` | `you-search` with `freshness` set to the exact window (`2026-07-17to2026-11-14`), `count` 50 to 100, one query per source using `site:arxiv.org`, `site:huggingface.co`, `site:github.com`, `site:zenodo.org`; keep `page_age` as the provisional date and let `tools/feeds.py` supply exact dates. About 10 to 20 calls, under $0.10 |
| `/judge` | `fetch(url)` then `research(question)` | `you-contents` on the primary URL (the Zenodo record, the paper, the model card), then `you-research` at `standard` for "what primary sources support this claim", with `freshness` and `exclude_domains: ["linkedin.com"]`. Every returned source goes to the ledger; the judge still reasons only from the ledger |
| `/run-candidate` | `fetch(url)` | `you-contents` on the model card and repository README to fill the harness config (model id, licence, context length, covariate support). No search needed. Only registered adapters run |

Always pass `exclude_domains: ["linkedin.com"]` (decision 21). It is a model-settable
argument on `you-search` and a `source_control` field on Research.

### Additional demo ideas, feasible in a day

1. **Provider agreement table.** Same 11 evaluation items through `claude` and `youcom`;
   show sources found by both, by one only, and whether the verdict changed. It is
   already planned and is the strongest "ground truth" point.
2. **Counter-evidence pass.** For each judged claim, one `you-research` call asking for
   independent replications or contradicting results, restricted by `freshness`. The
   scorecard gains a "disputed by" line with citations. Fits the Receipts track.
3. **Live Wire angle.** A `freshness: day` scan run on stage: "what was claimed in the
   last 24 hours", then judge the top hit. Cheap, and it shows the agent is live.
4. **Cost and latency line on the receipt.** Research effort tiers have fixed prices;
   print "this receipt cost $0.06 of search" next to each scorecard.

## 2. OpenCrawl ("open Crawl search")

Sources: https://getopencrawl.com, https://github.com/getopencrawl/opencrawl-core
(README), https://github.com/getopencrawl/opencrawl-core/blob/main/docs/mcp.md.

| Item | Finding |
|---|---|
| What it is | Shared memory for coding agents: captures full session transcripts (prompts, tool calls, results, memory files) from Claude Code, Codex and others; agents search them; a message board where agents post updates and subscribe to topics |
| What it is not | Not a web crawler, not web search, no feeds, no structured extraction of web pages. `robots.txt` does not apply to it: it reads our own agent sessions and connected workspaces (GitHub, Slack, Notion, Linear and others), not the public web |
| Search | lexical (BM25), returns excerpts with provenance, not generated answers |
| MCP | cloud `https://app.getopencrawl.com/mcp`; self-hosted `http://localhost:8092/mcp`. Tools: `opencrawl`, `test_connection`, `search`, `fetch`, `board_topics`, `board_sync`, `board_fetch`, `board_search` (parameters not documented) |
| Install | CLI `npm i -g @getopencrawl/cli@next`, then `opencrawl login`, `opencrawl collect install`, `opencrawl collect backfill`; `claude mcp add --transport http opencrawl <mcp url>` |
| Price | cloud: 100M session tokens a month free, then $0.50 per 1M. Self-host: free, Docker, needs 4 CPUs, 8 GB RAM, 20 GB disk |
| Licence | Apache-2.0 (plugins MIT); pre-1.0 preview |

What it adds that You.com does not: nothing for the web. It adds memory across agents
and sessions. Uses that fit this project:

1. **Scan, judge and run as agents that coordinate on the board.** `/scan` posts each
   new candidate to a topic; a `/judge` session subscribed to it picks the candidate
   up; `/run-candidate` posts the receipt. This is a credible entry for the OpenCrawl
   prize and matches the "How it works" tab.
2. **Audit trail.** The judge's whole session (every search and fetch) is stored word
   for word and searchable. "Show me where this citation came from" becomes a search
   over the session, next to the evidence ledger.
3. **"Have we judged this before?"** Before judging, search past sessions for the
   candidate's primary URL, to avoid duplicate work across teammates.
4. **Team memory** if teammates join at kickoff: their agents can search this repo's
   earlier sessions instead of asking.

Cautions before installing:

- `collect install` uploads complete session transcripts to their cloud unless
  self-hosted. Sessions of this repo include file contents and tool output. Use the
  project exclusions, do not backfill other projects, and keep rule 8 in mind (a
  secret printed in a session would be captured).
- `backfill` would also upload past sessions; decide deliberately.
- It does not help with reading the blogs and newsletters in
  `notes/blog_newsletter_sources.md`. That question stays as decided there: RSS feeds
  read by `tools/feeds.py`, no crawling of Substack, Medium, `eia.gov/rss` or GitHub
  Atom paths where `robots.txt` discourages it. No tool found today changes that.

If a real crawler is wanted (whole site, structured extraction), the candidates are
inside Treg's catalog (Firecrawl, Crawl4AI, Apify, Spider). Their `robots.txt`
behaviour was not checked, so they must not be pointed at the sources above.

## 3. Treg

Sources: https://treg.to/, https://treg.to/llms.txt, https://treg.to/skill.md,
https://treg.to/catalog, https://treg.to/tools/fishaudio, https://treg.to/tools/you,
https://github.com/superdesigndev/treg/blob/main/README.md.

| Item | Finding |
|---|---|
| What it is | One token for a catalog of third-party APIs, billed per call at the provider's rate; credentials are held on Treg's side |
| Setup | `curl -fsSL https://treg.to/install.sh \| sh`, `treg login` (or `--token <token>`). Claude Code plugin: `/plugin marketplace add superdesigndev/treg`, `/plugin install treg@treg`. MCP: `https://treg.to/mcp/` |
| Calling | `treg catalog search "<task>"`, `treg catalog get <id>` (parameters, price), `treg call <id> --data '{...}'`. HTTP: `https://treg.to/call/<id>` with header `X-Treg-Token` |
| MCP tools | `catalog_search`, `catalog_get`, `call`, `call_media` (audio), `resources_list`, `balance`, `my_tools`, and a few feedback tools |
| Price | per call, shown before the call; $1.00 free credit once per verified account; HTTP 402 when the balance is empty; own provider keys are not metered |
| Relevant catalog | Web: Brave, Exa, Firecrawl, Tavily, Serper, Perplexity, Parallel, **You.com** (search, contents, research at You.com's own prices), Crawl4AI, Apify. Academic: Valyu, Crawl4AI. Voice: **Fish Audio**, Google AI (Gemini), MiniMax. Image and video generation: Replicate, MiniMax, PiAPI and others. No avatar-video provider (HeyGen and similar are not listed), no ElevenLabs, no OpenAI |
| Licence | Apache-2.0 with extra terms (no competing hosted registry); calling the hosted API from our project is allowed |
| Data | requests and responses pass through Treg's proxy; calls are logged; the CLI sends anonymous usage data unless `TREG_TELEMETRY=0` |

What Yuri can do with it in this project:

1. **Narration for the video** (section 4). This is the clear use.
2. **A third search provider for the comparison.** Exa or Tavily through Treg as a
   `treg` column next to `claude` and `youcom` in `providers.md`, with no new accounts.
   Only if time remains; the hackathon is judged on You.com use.
3. **Backup route to You.com.** `you.web.search`, `you.web.contents`, `you.web.research`
   exist in the catalog. Useful only if the You.com key fails; the free $1 is about
   200 searches.
4. **Academic search** (Valyu) as an extra listing for `/scan`. Not checked in detail.

Do not use: Treg's LinkedIn data sources (decision 21), people and email enrichment
(irrelevant), and any scraper against the sites whose `robots.txt` discourages it.

## 4. The video with a computer voice

**Can the Treg key be used? Yes for the voice, no for an avatar.** Treg's catalog has
text-to-speech (`fishaudio.tts.s2-1-pro`, $15 per 1M bytes of input text, so a
3-minute script of about 2,700 characters costs about $0.04 and fits in the free $1).
It has no talking-avatar provider. Its video-generation models make short generated
clips ($0.28 to $0.56 each), which this video does not need: the picture is the
recorded dashboard tour.

Local state checked: `ffmpeg` (with libx264 and aac) and `say` are installed;
`dashboard/tour.webm` is 54.3 s, 1280x800, 12 fps, video only, 9 steps. Each step has
a caption and a duration (`ms`) in `dashboard/index.html`. At a normal speaking rate
(about 2.5 words a second) several captions are longer than their step, so narration
needs either longer steps or a slowed picture.

| Option | Quality | Cost | Licence note |
|---|---|---|---|
| Fish Audio through Treg | natural | about $0.04 for 3 minutes | Fish Audio's terms for publishing output not checked; choose a voice with `licensed=true` in `fishaudio.voices.discover` |
| macOS `say` | robotic to fair (Samantha, Daniel; better with a downloaded Premium voice) | free, offline | Apple's macOS licence allows system voices for personal, non-commercial content only. A hackathon demo is probably within that; a public post for the Best Content prize is less clear |
| OpenAI text-to-speech | natural | about $0.015 a minute (third-party estimate) | needs its own key; current models are reported to shut down Jan 6, 2027 (third-party) |

### Recommended pipeline

1. Write the talking points as one file per tour step: `video/01.txt` ... `video/09.txt`
   (one or two sentences each; they can differ from the on-screen captions).
2. Make one audio file per step.
   - Treg: `treg call fishaudio.tts.s2-1-pro --method POST --data '{"text":"...","format":"mp3"}' > video/01.mp3`
     (audio is binary on stdout; add `"reference_id":"<voice id>"` to pick a voice).
   - Fallback, offline: `say -v Samantha -r 170 -f video/01.txt -o video/01.aiff`.
3. Measure each clip: `ffprobe -v error -show_entries format=duration -of csv=p=0 video/01.mp3`.
4. Fit picture to voice. Simplest reliable way: set each step's `ms` in the tour to its
   clip length plus about 600 ms, re-record with `node tools/record_tour.mjs <work dir> video/tour_long.webm`.
   (Quick alternative with no re-recording: slow the whole video,
   `ffmpeg -i dashboard/tour.webm -vf "setpts=1.6*PTS" ...`, less exact.)
5. Join the clips with the same gaps:
   `ffmpeg -f concat -safe 0 -i video/list.txt -c:a aac video/narration.m4a`
   (the list alternates clips and a 0.6 s silence made with `ffmpeg -f lavfi -i anullsrc -t 0.6`).
6. Lay the narration over the tour and export MP4 (plays everywhere, unlike webm):
   `ffmpeg -i video/tour_long.webm -i video/narration.m4a -c:v libx264 -pix_fmt yuv420p -r 24 -c:a aac -shortest video/receipts_demo.mp4`
7. Say in the video or its description that the voice is synthetic.

Step 4 changes `dashboard/index.html` timing, so it is a code change to decide on
tomorrow, not done here. The `say` fallback gives a complete backup video tonight
without any key.

## What to do tomorrow, in order

1. At kickoff: get the You.com key and ask the four questions in `HACKATHON.md`, plus:
   how many credits, is the Research API included, is there a Treg or OpenCrawl
   credit or key for attendees, and what "Best use of OpenCrawl" is judged on.
2. Add the You.com MCP with research enabled
   (`https://api.you.com/mcp?tools=you-search,you-contents,you-research`), confirm the
   tool names with `/mcp`, check the balance with `you-balance`.
3. Smoke test: `you-contents` on the Zenodo record URL, then `you-search` for it with a
   date-range `freshness`. This settles the open item in `REFERENCE.md`.
4. Build `/judge` on You.com first (contents + research at `standard`,
   `exclude_domains` LinkedIn), then `/run-candidate`, as in `HACKATHON.md`.
5. `/scan` with `site:` queries and exact-range `freshness`; then the provider
   agreement table.
6. If going for the OpenCrawl prize: connect the cloud MCP for this project only (no
   backfill), and have scan, judge and run post to one board topic. About 30 to 45
   minutes; skip if the main path is behind.
7. Install Treg, check `treg` balance, generate the nine narration clips, build the
   video (section 4). Keep the `say` version as the backup.
8. Optional, last: a third provider column through Treg (Exa or Tavily); the
   counter-evidence pass.

## Not verified

- The amount of You.com credits per builder, and whether Research is included.
- Whether Yuri's Treg access is a pre-funded hackathon key or a normal account with
  the $1 free credit. The event page mentions neither.
- Fish Audio through Treg: maximum text length per call, WAV output, voice ids, and
  Fish Audio's terms for publishing generated speech. The HTTP body shape is inferred
  from the CLI example. No call was made.
- Whether You.com's Contents API live fetches obey `robots.txt` (the YouBot page
  covers the crawler only).
- `robots.txt` behaviour of the scrapers in Treg's catalog (Firecrawl, Crawl4AI, Apify).
- Exact MCP tool names as Claude Code shows them (`mcp__you-com__...`), and whether
  `count` and date-range `freshness` behave through MCP as in the REST docs.
- `page_age` is documented for news results; whether every web result carries it.
- You.com `count` default and maximum come from the quickstart, not the OpenAPI spec
  (not read). The Images endpoint is early access; assume it is unavailable.
- OpenCrawl: MCP tool parameters; whether the cloud service supports per-project
  capture limits as the self-hosted README describes; what the prize criteria are.
- Treg's catalog size differs between sources (2,600 to 4,100 endpoints); its own site
  says about 4,100 across 127 providers.
- OpenAI text-to-speech price and shutdown date come from third-party pages.
- Apple's licence wording was read from a search summary of the macOS licence PDFs
  (https://www.apple.com/legal/sla/), not from the PDF for the installed version (14.5).
- Sources disagree on the venue (New York vs. Brooklyn); the address is shown only
  after registration.
