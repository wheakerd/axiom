#!/bin/sh
# Axiom Stop check. Argument: claude or codex. Reads the host's Stop event JSON on stdin and prints JSON only.
# When the host reports stop_hook_active true, this turn was already continued once: print an empty object and let it end.
input=$(cat)
case "$input" in
  *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) printf '{}\n'; exit 0 ;;
esac
text='Axiom check before you end: Is the original request met against its own criteria? Does each completion claim rest on evidence observed in this session rather than recalled or summarized? Is anything unresolved, deferred, or risky that the user should hear? Is the final summary in the language of the request? If a claim rests on recalled facts, verify it first. Then end, or continue.'
case "$1" in
  claude) printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' "$text" ;;
  codex) printf '{"decision":"block","reason":"%s"}\n' "$text" ;;
  *) printf '{}\n' ;;
esac
