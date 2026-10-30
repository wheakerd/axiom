---
name: local-web-search
description: Use before web search or page access through the user's own browser, CLI, script, or HTTP client, or that the user says runs on their machine, including a fallback from cloud search to such a client. A host's built-in web tool, confirmed cloud search, and web app actions stay outside.
---

# Local Web Search

Keep research that runs through the user's own client relevant, free of agent-added machine details, and stopped at the first access challenge. No instruction can guarantee that a site will not classify a request as automated.

## Invariants

These invariants bind in every phase, including the references that phase loads. Everything else in this skill is a default you may adapt, saying so when you depart.

1. **Boundary before the first request.** Decide where the request will run from the tool's documentation, the host's context, and the user's words; never probe a site, enumerate machine identifiers, or inspect secrets to decide.
2. **No agent-added disclosure.** Send only the terms and destination the question needs; add no hostnames, device or installation IDs, usernames, local paths, environment details, or tracking headers, and strip machine-specific values from local context before sending it.
3. **One request at a time.** Send one agent-initiated search, navigation, or retrieval, read its result, then decide the next; no batch fetching, crawling, fan-out, polling, or scheduled retries.
4. **A challenge is a stop.** On a Cloudflare challenge, CAPTCHA, HTTP 429, or another explicit access or rate limit, stop this task's automated requests to that site. Never solve, reload, or retry the challenge, and never switch client, identity, proxy, account, or URL variant to reach the same content.
5. **Real identity.** Use the real client and its default identity; never spoof headers, alter fingerprints, hide automation flags, or simulate a human.
6. **No new authority.** This skill authorizes no disclosure, account action, installation, or change to browser or network settings.

## Select The Execution Boundary

- The user's own browser, CLI, script, or HTTP client, or a tool the user says runs on their machine: read `references/local-browsing.md` before the first request.
- A host's built-in web tool, or a confirmed cloud-hosted search or retrieval service: return to the host's normal workflow. Reassess when a later step uses a local client.

## Scope

Apply the reference throughout this task's local searches, selected result pages, and relevant follow-up links. A switch of tools does not erase a site's blocked state. Do not load this skill merely because a task mentions browsers, Cloudflare, or bot detection, or asks to edit this skill.

## Report

Report the useful research result and any access limitation. Describe only observed outcomes; neither these instructions nor a successful page load proves that later requests will avoid detection.
