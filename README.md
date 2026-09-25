# wolffcatskyy.dev

Source for [wolffcatskyy.dev](https://wolffcatskyy.dev), a static page on Cloudflare Pages.

Star counts, the project count and the threat-feed count are **generated at build time**
from the GitHub API. Don't hand-edit numbers in `src/`; use the tokens.

## Layout

- `src/` - templates with `{{...}}` tokens (`index.html`, `llms.txt`)
- `public/` - static files copied as-is (`og-image.webp`, `robots.txt`, `sitemap.xml`, `.well-known/`)
- `build.py` - fills the tokens and writes `dist/`. Python standard library only.

| Token | Source |
| --- | --- |
| `{{STARS:<repo>}}` | `stargazers_count` of `wolffcatskyy/<repo>` |
| `{{TOTAL_STARS}}` | sum of the repos on the page |
| `{{PROJECT_COUNT}}` | number of repos on the page |
| `{{FEED_COUNT}}` | length of `BLOCKLIST_SOURCES` in crowdsec-blocklist-import's latest release |

If any API call fails the build fails, so wrong numbers never ship; the previous deploy stays up.

## Build locally

```sh
GITHUB_TOKEN=... python3 build.py   # token optional; avoids the anonymous rate limit
open dist/index.html
```

## Deploy

`.github/workflows/deploy.yml` builds and deploys on push to `main` and once a day. It is
off until the repo has a `CLOUDFLARE_PAGES_PROJECT` variable plus `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID` secrets. PRs run a build check only.

## Notes

- `pip install` points at the GitHub repo until the first PyPI release of
  crowdsec-blocklist-import; switch it back to `pip install crowdsec-blocklist-import` after that.
- "120k+ IPs Blocked" and the sample terminal output are still static text.
