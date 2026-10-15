# stargate-vpn: isolated exit design

Status: reviewed design draft, not deployed or end-to-end validated. The public
[design manifest](design.example.json) defines intent; it is not consumed by a runtime installer.
No production addresses, keys, controller IDs or household inventory belong in this directory.

## Recommended structure

```text
Remote client -> Tailscale -> [namespace: stargate-vpn]
                               tailscale0 -> wg-vpn -> VPN internet
                                                |
                                encrypted WireGuard socket in host namespace
                                                |
                                         existing host WAN

Existing stargate exit -> existing host WAN          (unchanged)
Existing local VPN clients -> existing VPN tunnel   (unchanged)
```

Create a NEW WireGuard interface in the host namespace, then move that new interface into
`stargate-vpn`. Its encrypted UDP socket stays in the namespace where it was created. Inside the
new namespace, the VPN tunnel is the sole ordinary internet path. Tailscale's control traffic,
peer transport, DNS and forwarded exit traffic all use that tunnel. This trades some latency and
possibly more relay use for a simple isolation boundary. When the VPN fails, this Tailscale
identity may go offline; recovery remains possible from the existing host/admin path.

This revises the earlier shared-tunnel goal: use a separate provider configuration/key. Do not
move the existing working interface, reuse its identity, or change its addresses/routes. Check
provider limits for simultaneous connections. If a separate dual-stack configuration cannot be
provisioned, pause this design instead of silently modifying the working tunnel.

WireGuard documents its namespace/socket behavior in [Routing & Network Namespaces](https://www.wireguard.com/netns/).
The Tailscale exit integration remains an inference to validate, not a vendor-certified recipe.

## Proposed configuration ownership

| Component | Location / behavior |
| --- | --- |
| Namespace setup | New host service; creates only its own namespace and interface |
| Tunnel | New private key path; explicit addresses and dual-stack defaults inside namespace |
| DNS | Dedicated `/etc/netns/stargate-vpn/resolv.conf`; literal VPN resolver addresses |
| Firewall | Namespace-specific IPv4/IPv6 guards and NAT; installed before exit advertisement |
| Tailscale daemon | New service, persistent state `/var/lib/tailscale-vpn`, socket `/run/tailscale-vpn/tailscaled.sock` |
| Enrollment | Operator authenticates new identity; unique restricted tag, exit approval only |
| Public source | This design and reusable templates in home-config |
| Deployment | Private host values and installed-service ownership remain in dotsetup until explicitly migrated |

The namespace must include only loopback, wg-vpn and tailscale0. No veth, bridge, macvlan, physical
WAN, DHCP default or accepted subnet route is part of this design. Set IPv4/IPv6 forwarding
inside this namespace. Do not change host main defaults, existing policy tables or existing interfaces.
Install guards before Tailscale can add broad accept rules. Preserve required ICMP/ICMPv6 and
path-MTU discovery. Tune MTU for the nested tunnels using actual client transfer tests.

New forwarded internet traffic may leave only `tailscale0 -> wg-vpn`. Permit return traffic only
when established/related. NAT both families to the NEW tunnel's respective address. Block private,
link-local, multicast, tailnet and site-owned destinations on the forwarded internet path, with
narrow TCP/UDP 53 exceptions for configured VPN resolvers. These guards do not change a client's
separate direct tailnet connections or existing subnet-route permissions.

DNS acceptance is a separate gate: `accept-dns=false` on the new exit prevents importing the
existing household resolver into its OS resolver. That alone does NOT establish the remote
client's DNS behavior. Test Tailscale's exit DNS proxy, MagicDNS and the tailnet's global/split DNS
configuration; prove public queries use the intended VPN path. Do not change global tailnet DNS
or break private names merely to make this test pass. If selective DNS behavior needs more work,
leave the exit unadvertised to ordinary clients and report the limitation.

## Command shapes for review only

The following daemon command shows supported flags with isolated paths. It is not a complete
installation command: namespace, DNS mounts, keys, forwarding, firewall and service ordering
must exist first. Do not run it by hand on the host or against the default Tailscale socket.

```sh
ip netns exec stargate-vpn tailscaled \
  --tun=tailscale0 \
  --socket=/run/tailscale-vpn/tailscaled.sock \
  --statedir=/var/lib/tailscale-vpn
```

Use `ip netns exec` (or an equivalent reviewed mount arrangement) so the namespace-specific
resolver is mounted for the daemon. `NetworkNamespacePath=` alone does not select a separate
`resolv.conf`. Provision root-only state/runtime directories and service supervision before enrollment.
After private interactive enrollment, set the intended preferences ONLY on this new daemon:

```sh
ip netns exec stargate-vpn tailscale \
  --socket=/run/tailscale-vpn/tailscaled.sock set \
  --hostname=stargate-vpn \
  --accept-dns=false \
  --accept-routes=false \
  --advertise-routes= \
  --ssh=false \
  --webclient=false \
  --advertise-exit-node=false
```

Initial advertisement stays OFF. After namespace-only egress/DNS and firewall validation, the
approved test rollout enables advertisement on this socket and grants only the test identity
access. Avoid reusing an existing gateway tag with broader SSH/subnet auto-approval. Existing
broad policy grants must be evaluated; adding a narrow grant cannot override an existing broad one.

## Read-only review / validation commands

These are operator commands on the host AFTER deployment, not actions performed by this draft.
Some require the operator's sudo authorization. Never use `wg showconf` or print private keys.

```sh
sudo ip -n stargate-vpn -br link
sudo ip -n stargate-vpn -br address
sudo ip -n stargate-vpn -4 rule show
sudo ip -n stargate-vpn -6 rule show
sudo ip -n stargate-vpn -4 route show table all
sudo ip -n stargate-vpn -6 route show table all
sudo ip netns exec stargate-vpn wg show wg-vpn
sudo ip netns exec stargate-vpn iptables-save
sudo ip netns exec stargate-vpn ip6tables-save
sudo ip netns exec stargate-vpn tailscale --socket=/run/tailscale-vpn/tailscaled.sock status
```

Expected: no ordinary interface/fallback, new tunnel handshake, both tunnel addresses/defaults,
namespace guards before Tailscale accepts, and an independently registered `stargate-vpn` identity.
Review route/guard behavior after Tailscale startup; the namespace design does not remove the need
to validate Tailscale's own routing tables, packet marks and NAT interactions.

## Failure tests and rollback

Run only with explicit approval and only on the NEW tunnel/namespace. Lower wg-vpn, then test
new and already-established IPv4/IPv6 traffic and fresh DNS from the remote client. Delete each
namespace default route in turn and test again. Confirm no direct cellular/home fallback while
the exit remains selected. Check automatic-exit/managed policy settings on the client beforehand.
Deleting routes may require explicit replacement; do not assume reconfigure restores them.

Remote rollback is explicit: on the test client choose Tailscale -> Exit Node -> stargate (or None,
if direct internet is intentionally desired). Withdraw the NEW exit advertisement, stop the NEW
daemon, then remove its namespace/interface and only its service files. Retain state securely if
preserving identity; operator revokes/removes the identity if abandoning deployment. Never stop
existing tailscaled, remove its socket/state, flush host firewalls or delete the working local tunnel.
The exact setup/teardown commands will be generated from the reviewed private deployment inputs.
