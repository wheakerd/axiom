@echo off
setlocal DisableDelayedExpansion
echo You have Axiom. Load this startup front door before deciding whether any Axiom skill applies:
echo(
type "%~dp0..\skills\using-axiom\SKILL.md"
