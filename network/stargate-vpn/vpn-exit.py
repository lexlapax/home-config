#!/usr/bin/env python3
"""Stage/manage only the isolated stargate-vpn namespace; never enroll or advertise."""
import argparse
import base64
import fcntl
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess

NS = 'stargate-vpn'
WG = 'wg-vpn'
MARKER = Path('/run/home-config-vpn-exit.owned')


def validate(data):
    expected = {'address4', 'address6', 'dns4', 'dns6', 'endpoint', 'peer_key', 'private_key_file', 'protected4', 'protected6', 'mtu'}
    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError('Unexpected runtime configuration fields')
    for family in (4, 6):
        if any(not isinstance(data[f'{key}{family}'], str) or '%' in data[f'{key}{family}'] for key in ('address', 'dns')):
            raise ValueError('Literal unscoped address strings required')
        address = ipaddress.ip_interface(data[f'address{family}'])
        dns = ipaddress.ip_address(data[f'dns{family}'])
        if address.version != family or dns.version != family or address.ip.is_unspecified or address.ip.is_multicast or address.ip.is_loopback or dns.is_unspecified or dns.is_multicast or dns.is_loopback:
            raise ValueError('Invalid tunnel or resolver address')
        prefixes = data[f'protected{family}']
        if not isinstance(prefixes, list) or not prefixes:
            raise ValueError('Site protected destination prefixes must be explicit')
        for prefix in prefixes:
            network = ipaddress.ip_network(prefix)
            if network.version != family or network.prefixlen == 0 or dns in network:
                raise ValueError('Invalid protected prefix or resolver overlap')
    endpoint = data['endpoint']
    match = re.fullmatch(r'(?:\[([0-9a-fA-F:]+)\]|([0-9.]+)):(\d+)', endpoint)
    if not match or not 1 <= int(match[3]) <= 65535:
        raise ValueError('Endpoint must be a literal IP and UDP port')
    endpoint_ip = ipaddress.ip_address(match[1] or match[2])
    if endpoint_ip.is_unspecified or endpoint_ip.is_loopback or endpoint_ip.is_multicast:
        raise ValueError('Invalid endpoint address')
    try:
        decoded = base64.b64decode(data['peer_key'], validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError('Invalid peer public key') from error
    if len(decoded) != 32:
        raise ValueError('Peer public key must be 32 bytes')
    keypath = data['private_key_file']
    if not isinstance(keypath, str) or not re.fullmatch(r'/etc/home-config/vpn-exit/[A-Za-z0-9_.-]+', keypath):
        raise ValueError('Private-key path must be within /etc/home-config/vpn-exit')
    if type(data['mtu']) is not int or not 1280 <= data['mtu'] <= 1420:
        raise ValueError('Choose an MTU from 1280 through 1420; validate nested tunnel behavior')
    return data


def firewall(data, family):
    private = ['0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8', '169.254.0.0/16', '172.16.0.0/12', '192.168.0.0/16', '224.0.0.0/4', '240.0.0.0/4'] if family == 4 else ['::/128', '::1/128', '::ffff:0:0/96', '64:ff9b::/96', 'fc00::/7', 'fe80::/10', 'ff00::/8']
    dns = data[f'dns{family}']
    client = '100.64.0.0/10' if family == 4 else 'fd7a:115c:a1e0::/48'
    lines = ['*mangle', ':hc-vpn-guard - [0:0]', '-A FORWARD -j hc-vpn-guard',
             '-A hc-vpn-guard -m conntrack --ctstate INVALID -j DROP',
             f'-A hc-vpn-guard -i tailscale0 ! -o {WG} -j DROP',
             f'-A hc-vpn-guard -i tailscale0 ! -s {client} -j DROP']
    for protocol in ('udp', 'tcp'):
        lines.append(f'-A hc-vpn-guard -i tailscale0 -o {WG} -d {dns} -p {protocol} --dport 53 -j RETURN')
    for prefix in private + data[f'protected{family}']:
        lines.append(f'-A hc-vpn-guard -i tailscale0 -d {prefix} -j DROP')
    lines += [f'-A hc-vpn-guard -i tailscale0 -o {WG} -j RETURN',
              f'-A hc-vpn-guard -i {WG} -o tailscale0 -d {client} -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN',
              '-A hc-vpn-guard -j DROP', 'COMMIT', '*filter',
              ':INPUT DROP [0:0]', ':FORWARD DROP [0:0]', ':OUTPUT ACCEPT [0:0]',
              '-A INPUT -i lo -j ACCEPT', '-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT',
              f'-A INPUT -i {WG} -p udp --dport 41642 -j ACCEPT',
              '-A INPUT -p icmp -j ACCEPT' if family == 4 else '-A INPUT -p ipv6-icmp -j ACCEPT',
              f'-A FORWARD -i tailscale0 -o {WG} -s {client} -j ACCEPT',
              f'-A FORWARD -i {WG} -o tailscale0 -d {client} -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT',
              'COMMIT', '*nat', ':POSTROUTING ACCEPT [0:0]',
              f'-A POSTROUTING -s {client} -o {WG} -j MASQUERADE', 'COMMIT', '']
    return '\n'.join(lines)


class Manager:
    def __init__(self, data, dry_run=False):
        self.data = validate(data)
        self.dry_run = dry_run

    def run(self, *args, input=None, capture=False):
        if self.dry_run:
            print(' '.join(args) + (' [generated rules on stdin]' if input else ''))
            return ''
        result = subprocess.run(args, input=input, text=True, check=True, capture_output=capture)
        return result.stdout if capture else ''

    def exists(self):
        return any(line.split()[0] == NS for line in self.run('ip', 'netns', 'list', capture=True).splitlines())

    def status(self):
        if not self.exists():
            raise ValueError('Owned namespace is not running')
        if not MARKER.exists():
            raise ValueError('Namespace exists without ownership marker; leave it untouched')
        names = self.run('ip', '-n', NS, '-o', 'link', 'show', capture=True)
        names = {line.split(': ', 2)[1].split('@')[0] for line in names.splitlines()}
        if not names <= {'lo', WG, 'tailscale0'} or WG not in names:
            raise ValueError('Unexpected namespace interfaces; stop and investigate')
        for family, tool in [(4, 'iptables'), (6, 'ip6tables')]:
            self.run('ip', 'netns', 'exec', NS, tool, '-t', 'mangle', '-C', 'FORWARD', '-j', 'hc-vpn-guard')
            routes = self.run('ip', '-n', NS, f'-{family}', 'route', 'show', 'default', capture=True)
            if f'dev {WG}' not in routes:
                raise ValueError('Missing VPN default; no repair performed while daemon may run')
        print('Owned namespace, expected interfaces, guard jumps and dual-stack defaults present. Client egress is not verified.')

    def start(self):
        if not self.dry_run and self.exists():
            self.status()  # Idempotent health check; never flush a running daemon's firewall.
            return
        if not self.dry_run:
            key = Path(self.data['private_key_file'])
            if key.is_symlink() or not key.is_file() or key.stat().st_uid != 0 or key.stat().st_mode & 0o077:
                raise ValueError('Private-key file must be root-owned, regular and mode 0600 or stricter')
            # Never read or print the key: WireGuard receives its path only.
            if MARKER.exists():
                raise ValueError('Stale ownership marker; inspect before recovery')
        created_ns = created_wg = moved = False
        try:
            self.run('ip', 'netns', 'add', NS)
            created_ns = True
            if not self.dry_run:
                MARKER.write_text('home-config stargate-vpn\n')
                MARKER.chmod(0o600)
            self.run('ip', 'link', 'add', WG, 'type', 'wireguard')
            created_wg = True
            self.run('ip', 'link', 'set', WG, 'netns', NS)
            moved = True
            self.run('ip', '-n', NS, 'link', 'set', 'lo', 'up')
            for family in (4, 6):
                self.run('ip', '-n', NS, f'-{family}', 'address', 'add', self.data[f'address{family}'], 'dev', WG)
            self.run('ip', 'netns', 'exec', NS, 'wg', 'set', WG, 'private-key', self.data['private_key_file'],
                     'peer', self.data['peer_key'], 'allowed-ips', '0.0.0.0/0,::/0', 'endpoint', self.data['endpoint'], 'persistent-keepalive', '25')
            self.run('ip', '-n', NS, 'link', 'set', WG, 'mtu', str(self.data['mtu']), 'up')
            self.run('ip', 'netns', 'exec', NS, 'sysctl', '-q', '-w', 'net.ipv4.ip_forward=1', 'net.ipv6.conf.all.forwarding=1')
            for family, tool in [(4, 'iptables-restore'), (6, 'ip6tables-restore')]:
                rules = firewall(self.data, family)
                self.run('ip', 'netns', 'exec', NS, tool, '--test', input=rules)
                self.run('ip', 'netns', 'exec', NS, tool, input=rules)
                self.run('ip', '-n', NS, f'-{family}', 'route', 'add', 'default', 'dev', WG)
        except BaseException:
            if created_wg and not moved:
                self.run('ip', 'link', 'delete', WG)
            if created_ns:
                self.run('ip', 'netns', 'delete', NS)
                if not self.dry_run:
                    MARKER.unlink(missing_ok=True)
            raise

    def stop(self):
        if not self.dry_run:
            if not self.exists():
                if MARKER.exists():
                    raise ValueError('Namespace absent but marker remains; inspect stale state')
                return
            if not MARKER.exists():
                raise ValueError('Refusing to delete an unowned namespace')
            names = self.run('ip', '-n', NS, '-o', 'link', 'show', capture=True)
            names = {line.split(': ', 2)[1].split('@')[0] for line in names.splitlines()}
            if not names <= {'lo', WG, 'tailscale0'}:
                raise ValueError('Unexpected interface; refusing namespace deletion')
            if self.run('ip', 'netns', 'pids', NS, capture=True).strip():
                raise ValueError('Stop the isolated Tailscale daemon first; namespace still has processes')
        self.run('ip', 'netns', 'delete', NS)
        if not self.dry_run:
            MARKER.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'stop', 'status'])
    parser.add_argument('--config', type=Path, default=Path('/etc/home-config/vpn-exit/runtime.json'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not args.dry_run and os.geteuid() != 0:
        parser.error('Runtime actions require explicit operator authorization and root; use --dry-run for review')
    try:
        manager = Manager(json.loads(args.config.read_text()), args.dry_run)
        if args.dry_run:
            if args.action == 'status':
                print('Read-only status would check namespace ownership, interfaces, guard jumps and defaults.')
            else:
                getattr(manager, args.action)()
        else:
            with open('/run/home-config-vpn-exit.lock', 'w') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                getattr(manager, args.action)()
    except (ValueError, TypeError, KeyError, OSError, subprocess.CalledProcessError):
        parser.exit(1, 'VPN exit operation failed. No configuration or secret contents printed; inspect the staged deployment and service status.\n')


if __name__ == '__main__':
    main()
