"""Bounded local byte spool. Native launch is deliberately unavailable in V001.

No decoding, event inference, usage meter, account inspection, or model command.
Cross-pipe sequence is collector receipt order, not provider emission order.
"""
import ctypes
import copy
import os
from pathlib import Path
import queue
import signal
import subprocess
import threading
import time

from .binding import require, validate
from .evidence import Capture, audit


class Containment:
    """Best-effort local tree containment, never evidence of remote cancellation.

    Windows assignment occurs after spawn: the pre-assignment interval is an
    explicit coverage gap. No claim of an OS sandbox or complete tree visibility.
    """
    def __init__(self, process):
        self.process, self.job = process, None
        self.creation = 'UNKNOWN'
        if os.name == 'nt':
            from ctypes import wintypes as W
            self.k = ctypes.WinDLL('kernel32', use_last_error=True)
            self.k.CreateJobObjectW.argtypes = [ctypes.c_void_p, W.LPCWSTR]
            self.k.CreateJobObjectW.restype = W.HANDLE
            self.k.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
            self.k.AssignProcessToJobObject.restype = W.BOOL
            self.k.TerminateJobObject.argtypes = [W.HANDLE, W.UINT]
            self.k.TerminateJobObject.restype = W.BOOL
            self.k.CloseHandle.argtypes = [W.HANDLE]
            self.k.GetProcessTimes.argtypes = [W.HANDLE] + [ctypes.POINTER(W.FILETIME)] * 4
            times = [W.FILETIME() for _ in range(4)]
            if self.k.GetProcessTimes(int(process._handle), *[ctypes.byref(t) for t in times]):
                self.creation = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
            job = self.k.CreateJobObjectW(None, None)
            if job and self.k.AssignProcessToJobObject(job, int(process._handle)):
                self.job = job
            elif job:
                self.k.CloseHandle(job)

    def cancel(self, force=False):
        record = {'force': force, 'target_pid': self.process.pid, 'remote_cancellation': 'UNKNOWN'}
        try:
            if force and os.name == 'nt' and self.job:
                if not self.k.TerminateJobObject(self.job, 1):
                    raise OSError(ctypes.get_last_error(), 'TerminateJobObject failed')
                record['method'] = 'WINDOWS_ASSIGNED_JOB_TERMINATE'
            elif force and os.name != 'nt':
                os.killpg(self.process.pid, signal.SIGKILL)
                record['method'] = 'POSIX_PROCESS_GROUP_KILL'
            else:
                self.process.terminate()
                record['method'] = 'ATTRIBUTED_PARENT_TERMINATE'
            record['os_call_returned'] = True
        except OSError as error:
            record.update(os_call_returned=False, error_type=type(error).__name__)
        return record

    def close(self):
        if self.job:
            self.k.CloseHandle(self.job)
            self.job = None


def collect_fixture(binding, approval, payload):
    """Only the checked-in harmless fixture is executable through this interface.

    Simulated fixture consent is not owner consent. No real native entry point or
    command-line runner exists. A future native launcher needs independent review.
    """
    return _collect_fixture(binding, approval, payload)


def _collect_fixture(binding, approval, payload, *, after_raw=None, popen=None):
    binding, approval = copy.deepcopy(binding), copy.deepcopy(approval)
    popen = subprocess.Popen if popen is None else popen
    require(binding.get('mode') == 'LOCAL_FIXTURE', 'native launch disabled pending separate review')
    validate(binding, approval, payload)
    capture = Capture(binding, approval)  # CONSUMED durable before any spawn.
    process, containment = None, None
    threads = []
    start = time.monotonic()
    limits = binding['limits']
    events = queue.Queue(maxsize=8)  # Bounded read-ahead, shared by both pipes.
    stop_readers = threading.Event()
    eof = {'stdout': False, 'stderr': False}
    discarded = {'stdout': 0, 'stderr': 0}
    reasons, cancellations = [], []
    stdin = {'completed': False, 'bytes_written': 0, 'error': None}
    total, triggered, escalated, exit_seen = 0, None, False, None
    read_errors, identity = [], None

    def enqueue(row):
        while not stop_readers.is_set():
            try:
                events.put(row, timeout=.05)
                return
            except queue.Full:
                continue

    def reader(channel, pipe):
        try:
            while True:
                data = os.read(pipe.fileno(), limits['maximum_read_chunk_bytes'])
                observed = time.monotonic_ns()
                enqueue(('DATA' if data else 'EOF', channel, data, observed))
                if stop_readers.is_set():
                    break
                if not data:
                    break
        except (OSError, ValueError) as error:
            enqueue(('READ_ERROR', channel, type(error).__name__, time.monotonic_ns()))
        finally:
            pipe.close()

    def feed():
        try:
            view = memoryview(payload)
            while view:
                n = process.stdin.write(view)
                if not n:
                    raise OSError('short stdin write')
                stdin['bytes_written'] += n
                view = view[n:]
            process.stdin.close()  # Exactly one payload, then EOF.
            stdin['completed'] = True
        except (OSError, ValueError) as error:
            stdin['error'] = type(error).__name__
            try:
                process.stdin.close()
            except (OSError, ValueError):
                pass

    def trigger(reason, now):
        nonlocal triggered
        if reason not in reasons:
            reasons.append(reason)
            capture.event('STOP_TRIGGER', {'reason': reason})
        if triggered is None:
            triggered = now
            cancellations.append(containment.cancel())
            capture.event('CANCEL', cancellations[-1])

    try:
        capture.event('LAUNCH_INTENT', {'parent_invocations_maximum': 1, 'stdin_sha256': binding['stdin_sha256']})
        # Recheck mutable executable/source/runtime bindings after durable intent.
        # Existing capture is now expected, so common validation is not rerun.
        from .binding import sha, implementation, proposal, FIXTURE
        require(sha(Path(binding['binary']).read_bytes()) == binding['binary_sha256'] and
                sha(FIXTURE.read_bytes()) == binding['fixture_sha256'] and
                implementation() == binding['implementation'] and proposal() == binding['proposal'] and
                sha(Path(binding['system_file']).read_bytes()) == binding['system_sha256'], 'prelaunch executable/source/package changed')
        try:
            process = popen(binding['argv'], executable=binding['binary'], cwd=binding['cwd'],
                            env=binding['environment'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
                            shell=False, close_fds=True, start_new_session=os.name != 'nt')
        except OSError as error:
            capture.event('SPAWN_FAILED', {'error_type': type(error).__name__, 'reservation_consumed': True})
            reasons.append('SPAWN_FAILED')
        if process is not None:
            containment = Containment(process)
            identity = {'pid': process.pid, 'collector_pid': os.getpid(), 'collector_parent_pid': os.getppid(),
                        'child_parent_basis': 'DIRECT_POPEN_CHILD', 'created_windows_filetime': containment.creation,
                        'observed_after_spawn_monotonic_ns': time.monotonic_ns(),
                        'tree_control': ('WINDOWS_JOB_POST_SPAWN_BEST_EFFORT' if containment.job else
                                         'POSIX_NEW_SESSION' if os.name != 'nt' else 'PARENT_ONLY_TREE_UNKNOWN'),
                        'pre_assignment_descendants': 'UNKNOWN'}
            capture.event('SPAWNED', identity)
            for channel in eof:
                t = threading.Thread(target=reader, args=(channel, getattr(process, channel)), daemon=True)
                t.start(); threads.append(t)
            writer = threading.Thread(target=feed, daemon=True)
            writer.start(); threads.append(writer)
            while True:
                now = time.monotonic()
                code = process.poll()
                if code is not None and exit_seen is None:
                    exit_seen = now
                    capture.event('OS_EXIT', {'returncode': code})
                if now - start >= limits['watchdog_seconds']:
                    trigger('WATCHDOG', now)
                if stdin['error'] or read_errors:
                    trigger('PIPE_FAILURE', now)
                if triggered is not None and not escalated and now - triggered >= limits['cancel_escalation_after_seconds']:
                    escalated = True
                    cancellations.append(containment.cancel(force=True))
                    capture.event('CANCEL', cancellations[-1])
                if all(eof.values()) and code is not None and not writer.is_alive():
                    break
                drain_start = triggered if triggered is not None else exit_seen
                if drain_start is not None and now - drain_start >= limits['drain_grace_maximum_seconds']:
                    trigger('DRAIN_INCOMPLETE', now)
                    if not escalated:
                        escalated = True
                        cancellations.append(containment.cancel(force=True))
                        capture.event('CANCEL', cancellations[-1])
                    break
                try:
                    kind, channel, value, received = events.get(timeout=.02)
                except queue.Empty:
                    continue
                if kind == 'DATA':
                    if 'RECORDING_IO_TRIGGER' in reasons:
                        discarded[channel] += len(value)  # Explicitly truncated, never a lossless PASS.
                    else:
                        capture.chunk(channel, value, received, after_raw)
                        total += len(value)
                        if total >= limits['combined_recording_io_trigger_bytes']:
                            trigger('RECORDING_IO_TRIGGER', time.monotonic())
                elif kind == 'EOF':
                    eof[channel] = True
                    capture.event('EOF', {'channel': channel, 'received_monotonic_ns': received})
                else:
                    read_errors.append({'channel': channel, 'error_type': value})
                    capture.event('READ_ERROR', read_errors[-1])
            if process.poll() is None:
                trigger('CHILD_EXIT_UNKNOWN', time.monotonic())
        stop_readers.set()
        for t in threads:
            t.join(timeout=.05)
        alive = any(t.is_alive() for t in threads)
        wall = time.monotonic() - start
        if wall > limits['watchdog_seconds'] and 'WATCHDOG' not in reasons:
            reasons.append('WATCHDOG')
        if alive and 'CLEANUP_INCOMPLETE' not in reasons:
            reasons.append('CLEANUP_INCOMPLETE')
        if process is not None and (not stdin['completed'] or stdin['bytes_written'] != len(payload)):
            reasons.append('STDIN_INCOMPLETE')
        raw = {c: (capture.root / (c + '.bin')).read_bytes() for c in eof}
        receipt = {'version': binding['version'], 'mode': 'LOCAL_FIXTURE_NOT_NATIVE',
                   'outcome': 'LOCAL_CAPTURE_COMPLETE' if not reasons and all(eof.values()) else 'STOP_EVIDENCE_RETAINED',
                   'stop_reasons': reasons, 'process': identity, 'returncode': process.poll() if process else None,
                   'spawn_attempts': 1, 'eof': eof, 'stdin': stdin, 'drain_complete': all(eof.values()) and not alive,
                   'recorded_bytes': {c: len(raw[c]) for c in raw}, 'raw_sha256': {c: sha(raw[c]) for c in raw},
                   'discarded_after_io_trigger_bytes': discarded, 'truncated': bool(any(discarded.values()) or not all(eof.values())),
                   'observed_wall_seconds_through_receipt': wall, 'cancellations': cancellations,
                   'read_errors': read_errors, 'native_terminal': 'UNKNOWN_NOT_PARSED',
                   'N1_acceptance': 'NOT_EVALUATED_NO_NATIVE_PROFILE',
                   'resource_compliance': 'UNKNOWN', 'content_validity': 'NOT_EVALUATED',
                   'visible_generations': 'UNKNOWN', 'provider_requests': 'UNKNOWN',
                   'provider_usage': 'UNKNOWN', 'actual_subscription_charge': 'UNKNOWN',
                   'remote_cancellation': 'UNKNOWN', 'historical_account_writer': 'UNKNOWN',
                   'native_compatibility': 'NOT_TESTED', 'scientific_slots_consumed': 0,
                   'directory_power_loss_durability': 'UNKNOWN' if os.name == 'nt' else 'DIRECTORY_FSYNC_REQUESTED'}
        capture.seal(receipt)
        return audit(capture.root)
    except BaseException as error:
        # Storage failures and KeyboardInterrupt never yield a successful receipt.
        # Leave claim/lock and any unindexed tail intact; no retry or repair path.
        stop_readers.set()
        cleanup_cancel = None
        if process is not None:
            if containment:
                cleanup_cancel = containment.cancel(force=True)
            elif process.poll() is None:
                try:
                    process.kill()
                    cleanup_cancel = {'method': 'PARENT_KILL_NO_TREE_IDENTITY', 'os_call_returned': True}
                except OSError as cancel_error:
                    cleanup_cancel = {'method': 'PARENT_KILL_NO_TREE_IDENTITY', 'os_call_returned': False,
                                      'error_type': type(cancel_error).__name__}
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        for t in threads:
            t.join(timeout=.1)
        try:
            if not capture.closed and not capture.ended and not capture.poisoned:
                capture.event('INTERRUPTED', {'launch': 'ATTEMPTED' if process else 'UNKNOWN',
                                        'error_type': type(error).__name__, 'local_cancel': cleanup_cancel,
                                        'local_returncode_after_cleanup': process.poll() if process else None,
                                        'threads_still_alive': any(t.is_alive() for t in threads),
                                        'observed_wall_seconds': time.monotonic() - start,
                                            'remote_cancellation': 'UNKNOWN', 'no_retry': True})
        finally:
            capture.abandon()
        raise
    finally:
        if containment:
            containment.close()
