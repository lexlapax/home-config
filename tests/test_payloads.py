import base64
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


radius = load('radius_policy', 'network/radius-pilot/compile-policy.py')
vpn = load('vpn_exit', 'network/stargate-vpn/vpn-exit.py')


def fixture():
    return {'address4': '192.0.2.2/32', 'address6': '2001:db8:1::2/128',
            'dns4': '192.0.2.1', 'dns6': '2001:db8:1::1', 'endpoint': '198.51.100.2:51820',
            'peer_key': base64.b64encode(bytes([1]) * 32).decode(),
            'private_key_file': '/etc/home-config/vpn-exit/test.key',
            'protected4': ['203.0.113.0/24'], 'protected6': ['2001:db8:2::/64'], 'mtu': 1280}


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'network/radius-pilot/policy.example.json').read_text())

    def test_enrollment_and_vlan_switch(self):
        first = radius.compile_policy(self.policy)
        self.policy['devices'][0]['target'] = 'vpn'
        second = radius.compile_policy(self.policy)
        self.assertIn('Tunnel-Private-Group-Id := "30"', first)
        self.assertIn('Tunnel-Private-Group-Id := "90"', second)
        self.assertEqual(first.replace('"30"', '"90"'), second)
        self.assertIn('DEFAULT Auth-Type := Reject', second)

    def test_reject_unsafe_policy(self):
        for change in [lambda d: d['devices'].append(copy.deepcopy(d['devices'][0])),
                       lambda d: d['devices'][0].update(target='admin'),
                       lambda d: d['devices'][0].update(mac='01:00:00:00:00:01'),
                       lambda d: d['devices'][0].update(mac='02:00:00:00:00:01\nDEFAULT Auth-Type := Accept'),
                       lambda d: d['vlans'].update(vpn=d['vlans']['home']),
                       lambda d: d['vlans'].update(vpn=True)]:
            data = copy.deepcopy(self.policy)
            change(data)
            with self.assertRaises(ValueError): radius.compile_policy(data)

    def test_private_atomic_output_and_symlink_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'users'
            radius.atomic_write(output, 'first')
            radius.atomic_write(output, 'second')
            self.assertEqual(output.read_text(), 'second')
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            alias = Path(directory) / 'link'
            alias.symlink_to(output)
            with self.assertRaises(ValueError): radius.atomic_write(alias, 'bad')
            self.assertEqual(output.read_text(), 'second')


class NamespaceTests(unittest.TestCase):
    def test_reject_wrong_family_endpoint_and_injected_paths(self):
        for key, value in [('address6', '192.0.2.2/32'), ('dns4', '127.0.0.1'),
                           ('endpoint', 'vpn.example:51820'), ('protected4', []),
                           ('protected6', ['::/0']), ('private_key_file', '/etc/../tmp/key'),
                           ('peer_key', 'bad'), ('mtu', 1279)]:
            data = fixture()
            data[key] = value
            with self.assertRaises(ValueError): vpn.validate(data)

    def test_namespace_only_dry_run_and_birthplace_order(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output): vpn.Manager(fixture(), True).start()
        commands = output.getvalue().splitlines()
        create = commands.index('ip link add wg-vpn type wireguard')
        move = commands.index('ip link set wg-vpn netns stargate-vpn')
        self.assertLess(create, move)
        self.assertFalse(any('veth' in line or 'wan0' in line or 'wg-proton' in line for line in commands))
        self.assertTrue(all('ip netns exec stargate-vpn' in line for line in commands if 'iptables' in line or 'sysctl' in line))
        self.assertTrue(all('ip -n stargate-vpn' in line for line in commands if 'route ' in line))
        self.assertNotIn('tailscale up', output.getvalue())
        self.assertNotIn('--advertise-exit-node', output.getvalue())

    def test_guards_deny_wrong_output_and_source_before_dns_exception(self):
        for family in (4, 6):
            rules = vpn.firewall(fixture(), family)
            self.assertLess(rules.index('! -o wg-vpn -j DROP'), rules.index('--dport 53 -j RETURN'))
            self.assertLess(rules.index('! -s '), rules.index('--dport 53 -j RETURN'))
            self.assertIn('--ctstate ESTABLISHED,RELATED', rules)
            self.assertIn(':FORWARD DROP', rules)
            self.assertIn('-o wg-vpn -j MASQUERADE', rules)
            self.assertIn('-A hc-vpn-guard -j DROP', rules)
            self.assertIn(':INPUT DROP', rules)

    def test_start_refuses_unowned_existing_namespace_without_mutating_it(self):
        manager = vpn.Manager(fixture())
        calls = []
        def fake(*args, **kwargs):
            calls.append(args)
            return 'stargate-vpn\n' if args == ('ip', 'netns', 'list') else ''
        manager.run = fake
        with tempfile.TemporaryDirectory() as directory, patch.object(vpn, 'MARKER', Path(directory) / 'absent'):
            with self.assertRaises(ValueError): manager.start()
        self.assertTrue(calls)
        self.assertTrue(all(args == ('ip', 'netns', 'list') for args in calls))

    def test_stop_refuses_live_processes_and_foreign_interfaces(self):
        for links, pids in [('1: lo: <UP>\n2: wg-vpn: <UP>\n', '42\n'),
                            ('1: lo: <UP>\n2: eth0: <UP>\n', '')]:
            manager = vpn.Manager(fixture())
            calls = []
            def fake(*args, **kwargs):
                calls.append(args)
                if args == ('ip', 'netns', 'list'): return 'stargate-vpn\n'
                if args[-2:] == ('link', 'show'): return links
                if args == ('ip', 'netns', 'pids', 'stargate-vpn'): return pids
                return ''
            manager.run = fake
            with tempfile.TemporaryDirectory() as directory:
                marker = Path(directory) / 'owned'
                marker.touch()
                with patch.object(vpn, 'MARKER', marker):
                    with self.assertRaises(ValueError): manager.stop()
                self.assertTrue(marker.exists())
            self.assertNotIn(('ip', 'netns', 'delete', 'stargate-vpn'), calls)

    def test_failure_removes_only_new_namespace_not_foreign_host_tunnel(self):
        manager = vpn.Manager(fixture(), True)
        calls = []
        def fake(*args, **kwargs):
            calls.append(args)
            if args == ('ip', 'link', 'add', 'wg-vpn', 'type', 'wireguard'):
                raise subprocess.CalledProcessError(2, args)
            return ''
        manager.run = fake
        with self.assertRaises(subprocess.CalledProcessError): manager.start()
        self.assertIn(('ip', 'netns', 'delete', 'stargate-vpn'), calls)
        self.assertFalse(any(args[:3] == ('ip', 'link', 'delete') for args in calls))


if __name__ == '__main__':
    unittest.main()
