"""Host-only cleanup regression tests; no process, desktop or emulator launch."""
import ctypes
from types import SimpleNamespace
import unittest

from mgba_headless_gdb_capture import PrivateDesktopProcess


class PrivateDesktopCleanupTests(unittest.TestCase):
    def process(self, terminate_ok=True, wait_result=0, error=5):
        process=PrivateDesktopProcess.__new__(PrivateDesktopProcess)
        process.process=SimpleNamespace(hProcess=101,hThread=102,dwProcessId=55)
        process.desktop=103
        calls=[]
        def terminate(handle,code):
            calls.append(('terminate',handle,code))
            ctypes.set_last_error(error)
            return terminate_ok
        def wait(handle,milliseconds):
            calls.append(('wait',handle,milliseconds))
            ctypes.set_last_error(87)  # must not replace the termination error
            # The old zero-time poll would still report the process as running.
            return wait_result if milliseconds==5000 else 258
        process._terminate_process=terminate
        process._wait_process=wait
        process._close_handle=lambda h:calls.append(('close_handle',h))
        process._close_desktop=lambda h:calls.append(('close_desktop',h))
        return process,calls

    def test_already_exiting_access_denied_waits_then_cleans(self):
        process,calls=self.process(terminate_ok=False)
        process.close()
        self.assertEqual(calls,[('terminate',101,0),('wait',101,5000),
            ('close_handle',102),('close_handle',101),('close_desktop',103)])
        self.assertIsNone(process.process)
        self.assertIsNone(process.desktop)
        process.close()
        self.assertEqual(len(calls),5)

    def test_successful_termination_waits_once(self):
        process,calls=self.process()
        process.close()
        self.assertEqual(calls[1],('wait',101,5000))
        self.assertEqual(len(calls),5)

    def test_denial_timeout_preserves_original_error_and_handles(self):
        for error in (5,6):
            with self.subTest(error=error):
                process,calls=self.process(terminate_ok=False,wait_result=258,error=error)
                with self.assertRaises(OSError) as caught:
                    process.close()
                self.assertEqual(caught.exception.winerror,error)
                self.assertEqual(calls,[('terminate',101,0),('wait',101,5000)])
                self.assertEqual(process.process.hProcess,101)
                self.assertEqual(process.desktop,103)

    def test_failed_wait_after_denial_does_not_hide_termination_error(self):
        process,calls=self.process(terminate_ok=False,wait_result=0xFFFFFFFF)
        with self.assertRaises(OSError) as caught:
            process.close()
        self.assertEqual(caught.exception.winerror,5)
        self.assertEqual(len(calls),2)

    def test_successful_termination_but_no_signaled_exit_still_fails(self):
        for result in (258,0xFFFFFFFF,0x80):
            with self.subTest(wait_result=result):
                process,calls=self.process(wait_result=result)
                with self.assertRaisesRegex(RuntimeError,'PID 55 did not exit'):
                    process.close()
                self.assertEqual(len(calls),2)
                self.assertIsNotNone(process.process)

    def test_retry_after_timeout_can_finish(self):
        process,calls=self.process(terminate_ok=False,wait_result=258)
        with self.assertRaises(OSError):
            process.close()
        process._wait_process=lambda handle,milliseconds:0
        process.close()
        self.assertIsNone(process.process)
        self.assertEqual(calls[-3:],[('close_handle',102),('close_handle',101),('close_desktop',103)])

    def test_no_process_handle_closes_remaining_resources(self):
        process,calls=self.process()
        process.process.hProcess=None
        process.close()
        self.assertEqual(calls,[('close_handle',102),('close_desktop',103)])

    def test_context_manager_uses_same_cleanup(self):
        process,calls=self.process(terminate_ok=False)
        with process as current:
            self.assertIs(current,process)
        self.assertEqual(calls[1],('wait',101,5000))


if __name__=='__main__':
    unittest.main()
