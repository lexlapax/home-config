#!/usr/bin/env python3
"""Root integration test ONLY on a disposable GitHub-hosted runner."""
import base64
import os
from pathlib import Path
import subprocess
import sys

if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('HOME_CONFIG_DISPOSABLE_TESTS') != '1' or os.geteuid() != 0:
    sys.exit('Refusing native namespace test outside explicitly enabled disposable GitHub runner')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_payloads import vpn, fixture

def run(*args):
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        result.check_returncode()
    return result.stdout
before4 = run('ip', '-4', 'route', 'show', 'table', 'main')
before6 = run('ip', '-6', 'route', 'show', 'table', 'main')
assert not vpn.MARKER.exists()
assert 'stargate-vpn' not in run('ip', 'netns', 'list')
key = Path('/etc/home-config/vpn-exit/test.key')
assert not key.exists()
key.parent.mkdir(parents=True, exist_ok=True)
key.write_text(base64.b64encode(bytes([2]) * 32).decode() + '\n')
key.chmod(0o600)
manager = vpn.Manager(fixture())
try:
    manager.start()
    manager.status()
    manager.start()  # Healthy repeated start must not reset firewall or namespace.
    run('ip', '-n', vpn.NS, 'link', 'add', 'tailscale0', 'type', 'dummy')
    run('ip', '-n', vpn.NS, 'link', 'set', 'tailscale0', 'up')
    run('ip', '-n', vpn.NS, '-4', 'address', 'add', '100.64.0.1/10', 'dev', 'tailscale0')
    run('ip', '-n', vpn.NS, '-6', 'address', 'add', 'fd7a:115c:a1e0::1/48', 'dev', 'tailscale0')
    for family, source, target in [(4, '100.64.0.10', '198.51.100.99'), (6, 'fd7a:115c:a1e0::10', '2001:db8:3::99')]:
        lookup = run('ip', '-n', vpn.NS, f'-{family}', 'route', 'get', target, 'from', source, 'iif', 'tailscale0')
        assert 'dev wg-vpn' in lookup
        run('ip', '-n', vpn.NS, f'-{family}', 'route', 'del', 'default', 'dev', vpn.WG)
        missing = subprocess.run(['ip', '-n', vpn.NS, f'-{family}', 'route', 'get', target, 'from', source, 'iif', 'tailscale0'], capture_output=True)
        assert missing.returncode != 0, 'Missing VPN default must not fall back'
        run('ip', '-n', vpn.NS, f'-{family}', 'route', 'add', 'default', 'dev', vpn.WG)
    manager.stop()
    manager.stop()  # Repeated stop is safe after complete cleanup.
finally:
    if manager.exists():
        manager.stop()
    key.unlink(missing_ok=True)
assert run('ip', '-4', 'route', 'show', 'table', 'main') == before4
assert run('ip', '-6', 'route', 'show', 'table', 'main') == before6
print('Native isolated namespace/rules tests pass; host main routes unchanged. No real VPN handshake or Tailscale client tested.')
