@echo off
setlocal DisableDelayedExpansion
"%SystemRoot%\System32\findstr.exe" /R "stop_hook_active.:true stop_hook_active.:.true" >nul
if not errorlevel 1 goto allow
echo {"decision":"block","reason":"Axiom: completion rests on evidence observed in this session, names what remains unresolved, and replies in the language of the request."}
exit /b 0
:allow
echo {}
exit /b 0
