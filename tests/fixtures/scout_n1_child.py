"""Fixed harmless pipe producer. Never imports a provider or reads accounts."""
import hashlib
import os
import subprocess
import sys
import time


def write(fd, value):
    while value:
        n = os.write(fd, value)
        value = value[n:]


case = sys.argv[1]
if case == 'hold':
    time.sleep(.25)
    write(1, b'held-pipe-tail\xff')
    raise SystemExit(0)

payload = sys.stdin.buffer.read()
if case == 'bytes':
    write(1, b'\xffinvalid JSON\r\n\n{"unknown_native_event":true}\n' + hashlib.sha256(payload).hexdigest().encode() + b'\x00tail')
    write(2, b'\xfeSTDERR\r\npartial')
elif case == 'flood':
    # Alternating writes larger than pipe capacity deadlock a serial collector.
    for _ in range(128):
        write(2, b'E' * 16384)
        write(1, b'O' * 4096)
elif case == 'split':
    for byte in b'\xe2\x82\xac\xf0\x9f\x8c\x8d\xff\r\n{"a":':
        write(1, bytes([byte])); time.sleep(.01)
    write(2, b'split-stderr')
elif case == 'delayed':
    write(1, b'parent-exited\n')
    subprocess.Popen([sys.executable, '-I', __file__, 'hold'], stdin=subprocess.DEVNULL,
                     stdout=sys.stdout, stderr=sys.stderr, close_fds=True)
    os._exit(0)  # Deliberately leave the inherited pipes open in a local child.
elif case == 'trailing':
    write(1, b'{"type":"result","result":"not authoritative"}\n')
    time.sleep(.02)
    write(1, b'TRAILING\xff\x00NO_NEWLINE')
elif case == 'nonzero':
    write(1, b'partial-before-error')
    write(2, b'fixed fixture failure')
    raise SystemExit(7)
elif case == 'sleep':
    write(1, b'before-watchdog')
    time.sleep(20)
elif case == 'threshold':
    for _ in range(128):
        write(1, b'X' * 16384)
else:
    raise SystemExit('unknown fixed fixture')
