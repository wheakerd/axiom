# Local Browsing Conduct

Apply this reference before a local research request, or provisionally when
the execution location cannot be established from available tool information.

## Minimize Agent-Added Disclosure

- Use only the search terms and destination information needed for the user's
  question. Do not automatically append hostnames, device IDs, installation
  IDs, usernames, local paths, environment details, or other machine-specific
  information to search terms, URLs, query parameters, request headers, or
  request bodies.
- When using a local error, log, or file as research context, extract the
  relevant generic technical terms. Remove machine-specific values before
  sending the excerpt; do not upload the raw local context as a shortcut.
- Do not collect identifiers to enrich a search or add diagnostic or tracking
  headers. Treat identifiers embedded in copied URLs as potential disclosure,
  too. Use a known public destination or omit unnecessary parameters; do not
  damage a required URL and repeatedly try variants.
- Keep the browser's normal protocol behavior, existing session state, and
  host-managed automation disclosures. This rule limits agent-added data; it
  does not promise anonymity or hide the network address and browser signals
  inherent in a normal request. An existing user authorization must cover any
  task-required disclosure; this skill supplies none.

## Browse In Sequence

- Search only when needed to answer the current question. Read the returned
  results, select a relevant page, inspect it, and then decide whether another
  search or click is necessary.
- Send one agent-initiated search, navigation, or retrieval at a time. Wait for
  its result before the next step. Normal subresource loading within a browser
  page does not count as agent-initiated batch retrieval.
- Do not batch-fetch result pages, crawl links, enumerate pagination, fan out
  across tabs or workers, or run high-frequency refreshes. Do not schedule
  background retries, polling loops, or automatic retry-on-block behavior.
- Use the supported browsing tools as provided. Do not add parallel fetch
  workers or retry services. Do not run repeated access tests just to measure
  bot detection.

## Stop At A Challenge Or Limit

On a Cloudflare challenge, CAPTCHA, HTTP 429, or another explicit access or
rate-limit response:

1. Stop this task's automated requests to the affected site immediately. Cancel
   any pending task-owned retries or refreshes and retain the blocked state in
   the current task context, including across compaction or tool changes.
2. Do not solve or submit the challenge, reload it, click through it, or retry
   after a timer. A `Retry-After` value does not authorize automatic resumption.
3. Do not switch browsers, clients, IP addresses, proxies, accounts, URL
   variants, or cloud backends to reach the same blocked content. Other
   independently accessible sources may still be used within the task's scope.
4. Tell the user which site stopped access and what was observed, without
   exposing machine-specific URL parameters or local diagnostic data. If that
   site is necessary, hand control to the user for manual handling.
5. During handoff, preserve the current page. Do not create, close, replace,
   navigate, refresh, fill, or submit the handoff page while waiting for the
   user's explicit readiness. Readiness is not inferred from elapsed time.
6. After readiness, first inspect and preserve the user-opened page without
   navigating or submitting. Resume only when the block is visibly resolved
   and the next action is within the existing task authorization. If it is
   unresolved, stop again; do not enter a retry loop. If no page is available
   to inspect, keep that site's automated access stopped.

## Preserve Browser Identity

Do not impersonate a person, trusted crawler, or different client. Do not
spoof identity headers, alter browser fingerprints, hide automation flags,
inject stealth patches, rotate identities, or simulate human behavior to evade
detection. Use the real browser and its default identity behavior. Do not
remove required automation disclosures or modify browser security settings to
make a request appear human.

## Evidence Boundary

Report only successful reads and observed restrictions. Never claim that a
site accepted a request as human, that Cloudflare will not flag this browser,
or that this workflow guarantees unblocked access. A blocked source remains a
limitation of the research result, not a reason to bypass its controls.
