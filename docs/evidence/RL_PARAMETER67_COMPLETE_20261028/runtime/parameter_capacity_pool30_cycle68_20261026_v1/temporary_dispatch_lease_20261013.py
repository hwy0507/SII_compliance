"""Bounded, recoverable dispatch pause; independent in-flight workers continue."""
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

COORDINATOR = 'sii-fair-parallel-20261013-v4.service'
TARGET = 'sii-original-esn-old-office-20261013-v3.service'


def main():
    receipt = Path(sys.argv[1])
    target = sys.argv[2] if len(sys.argv) > 2 else TARGET
    state = dict(coordinator=COORDINATOR, target=target, timeout_s=1200,
        started_utc=datetime.now(timezone.utc).isoformat(), scope='Freeze coordinator cgroup only; workers are separate sibling service cgroups; no restart or simulation interruption')
    def save():
        receipt.write_text(json.dumps(state, indent=2) + '\n')
    save()
    try:
        subprocess.run(['systemctl', '--user', 'freeze', COORDINATOR], check=True, timeout=20)
        state['frozen'] = True; save()
        deadline = time.monotonic() + 1200
        while time.monotonic() < deadline:
            result = subprocess.run(['systemctl', '--user', 'is-active', target], text=True, capture_output=True, timeout=10)
            if result.stdout.strip() not in ('active', 'activating', 'deactivating'):
                state['target_final_state'] = result.stdout.strip()
                break
            time.sleep(3)
        else:
            state['lease_expired'] = True
    finally:
        result = subprocess.run(['systemctl', '--user', 'thaw', COORDINATOR], timeout=20)
        state['thawed'] = result.returncode == 0
        state['ended_utc'] = datetime.now(timezone.utc).isoformat(); save()
        if result.returncode:
            raise RuntimeError('Coordinator thaw failed')


if __name__ == '__main__':
    main()
