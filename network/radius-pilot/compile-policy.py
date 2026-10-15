#!/usr/bin/env python3
"""Compile an explicitly enrolled pilot inventory into a FreeRADIUS 3 users file."""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile


def compile_policy(data):
    if not isinstance(data, dict) or set(data) != {'vlans', 'devices'}:
        raise ValueError('Expected only vlans and devices')
    vlans = data['vlans']
    if not isinstance(vlans, dict) or set(vlans) != {'home', 'vpn'} or any(type(v) is not int or not 1 <= v <= 4094 for v in vlans.values()):
        raise ValueError('Home and VPN need valid VLAN IDs')
    if vlans['home'] == vlans['vpn']:
        raise ValueError('Home and VPN must use different VLANs')
    if not isinstance(data['devices'], list) or len(data['devices']) != 1:
        raise ValueError('Pilot must enroll exactly one device')
    lines = ['# Pilot policy: unlisted identities are rejected; no default accept.']
    for device in data['devices']:
        if not isinstance(device, dict) or set(device) != {'mac', 'target'} or not isinstance(device['target'], str) or device['target'] not in vlans:
            raise ValueError('Device needs only mac and an approved target')
        mac = device['mac']
        if not isinstance(mac, str) or not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', mac):
            raise ValueError('MAC must use six colon-separated octets')
        raw = bytes.fromhex(mac.replace(':', ''))
        if raw[0] & 1 or raw == bytes(6):
            raise ValueError('MAC must identify a unicast device')
        identity = mac.replace(':', '').upper()
        vlan = vlans[device['target']]
        lines += [f'{identity} Cleartext-Password := "{identity}"',
                  '    Tunnel-Type := VLAN,', '    Tunnel-Medium-Type := IEEE-802,',
                  f'    Tunnel-Private-Group-Id := "{vlan}"', '']
    lines += ['DEFAULT Auth-Type := Reject', '']
    return '\n'.join(lines)


def atomic_write(path, content):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refusing symlink output')
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.pilot-', delete=False) as stream:
        temp = Path(stream.name)
        try:
            os.chmod(temp, 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        result = compile_policy(json.loads(args.inventory.read_text()))
        if args.dry_run:
            print('Valid one-device pilot policy; no files written or identities printed.')
        elif not args.output:
            parser.error('--output is required unless --dry-run is used')
        else:
            atomic_write(args.output, result)
            print('Policy written privately; run the FreeRADIUS parser before deployment.')
    except (ValueError, TypeError, KeyError, OSError):
        parser.exit(1, 'Invalid policy or output path; no policy contents printed.\n')
