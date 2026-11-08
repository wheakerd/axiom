@echo off
setlocal DisableDelayedExpansion
"%SystemRoot%\System32\findstr.exe" /R "stop_hook_active.:true stop_hook_active.:.true" >nul
if not errorlevel 1 goto allow
echo {"decision":"block","reason":"Axiom check before you end: Is the original request met against its own criteria? Does each completion claim rest on evidence observed in this session rather than recalled or summarized? Is anything unresolved, deferred, or risky that the user should hear? Is the final summary in the language of the request? If a claim rests on recalled facts, verify it first. Then end, or continue."}
exit /b 0
:allow
echo {}
exit /b 0
