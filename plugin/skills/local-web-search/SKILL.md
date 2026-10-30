---
name: local-web-search
description: Use before web search or page access through the user's own browser, CLI, script, or HTTP client, or that the user says runs on their machine, including a fallback from cloud search to such a client. A host's built-in web tool, confirmed cloud search, and web app actions stay outside.
---

# Local Web Search

Keep local research requests relevant, avoid adding machine information, and
stop automated access when a site challenges or limits it. These constraints
cannot guarantee that Cloudflare or another service will not classify a
request as automated.

Defaults you may adapt, saying so: query wording and report layout. Every other rule here and in the references this skill loads binds.

## Select The Execution Boundary

Before the first request, identify where it will run from the tool's documentation, the host's context, and the user's words. Do not probe a website, enumerate machine identifiers, or inspect secrets to make this decision.

- The user's own browser, CLI, script, or HTTP client, or a tool the user says runs on their machine: read `references/local-browsing.md` before sending the request.
- A host's built-in web tool, or a confirmed cloud-hosted search or retrieval service: return to the host's normal workflow. Reassess if a later step uses a local client.

## Scope

Apply the reference throughout this research task's local searches, selected
result pages, and relevant follow-up links. A switch of tools does not erase a
site's blocked state.

This skill does not authorize new disclosures, account actions, installation,
or changes to browser or network settings. Keep any other applicable owner and
host restrictions. Do not load it merely because a task mentions browsers,
Cloudflare, or bot detection, or asks to edit this skill.

## Report

Report the useful research result and any access limitation. Describe only
observed outcomes; neither these instructions nor a successful page load prove
that future requests will avoid bot detection.
