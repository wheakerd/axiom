#!/bin/sh
# Axiom Stop check. Argument: claude or codex. Reads the host's Stop event JSON on stdin and prints JSON only.
# When the host reports stop_hook_active true, this turn was already continued once: print an empty object and let it end.
input=$(cat)
case "$input" in
  *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) printf '{}\n'; exit 0 ;;
esac
text='Axiom: completion rests on evidence observed in this session, names what remains unresolved, and replies in the language of the request.'
case "$1" in
  claude) printf '{"hookSpecificOutput":{"hookEventName":"Stop","additionalContext":"%s"}}\n' "$text" ;;
  codex) printf '{"decision":"block","reason":"%s"}\n' "$text" ;;
  *) printf '{}\n' ;;
esac
