# Private-desktop cleanup race

The completed120000-frame original observation wrote its bounded-completion
marker, final captures and module summaries, but its host launcher subsequently
raised during `PrivateDesktopProcess.close()`. Root reported termination error5
and no remaining EmuHawk process. Root owns recovery of that run's postchecks;
this fix does not rerun the observation or reinterpret it as Shoot success.

The previous helper called `TerminateProcess`, then performed only a zero-time
wait on failure. A process still finishing exit could therefore fail cleanup
before the existing five-second wait was reached. It also fetched last-error
after the wait, allowing the wait to overwrite the termination failure.

The minimal change saves the termination error immediately and performs exactly
one5000ms wait in either termination-result branch. Only `WAIT_OBJECT_0` permits
resource cleanup. A termination failure followed by timeout or wait failure
raises the saved WinError; successful termination followed by non-signaled wait
retains the existing runtime error. Handles remain available after failure,
and successful cleanup remains idempotent.

Microsoft documents that external
[TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
is asynchronous and calls against a terminated process can return access
denied. Its
[WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject)
contract distinguishes a signaled process from timeout/failure and specifies
that a zero timeout returns immediately. The fix uses that completion signal;
it does not assume error5 always means harmless exit.

Before editing, all36 matching active-tree context-manager callsites were
inspected: five tools and31 ignored launchers/fixtures. None calls close or the
private wait directly or depends on immediate failure. Historical checkout
copies contain their own helper and remain untouched. Caller APIs are unchanged.

`tools/test_private_desktop_cleanup.py` bypasses construction and supplies fake
Win32 functions. Eight tests pass, including delayed exit after denial,
successful termination, preserved errors5/6 across a changed last-error value,
timeout/wait-failure, retry, missing process handle, idempotence and context
manager cleanup. The frozen old method fails the delayed-exit regression control
and reports the mock wait's error87 instead of the original5. No process or
desktop is created and no emulator is launched by these tests.

Changed helper SHA256:
`A3DE346280D736D7B1590D9450DFC901854F11F53EC2615432D594FBDEEAB60E`.
Test SHA256:
`D7B8BFEE2FB78557AA0B8CC8E15CD1A541E967666675CD751E39FCD5250F66EE`.
Run with `python -m unittest discover -s tools -p test_private_desktop_cleanup.py -v`.
Only the shared host helper, new test and this record were changed by this task;
frozen Lua, ROM/main, save and runtime artifacts remain untouched.
