# Staged payload review and operator handoff

Status: implementation staged; not installed, enrolled or advertised. No current SSID, host routes,
VPN key or existing Tailscale service has changed. Native/parser CI results are recorded separately
from unit tests and live acceptance. The app remains a sample preview with no live mutation endpoint.

## What is implemented

| Payload | Behavior | Boundary |
| --- | --- | --- |
| [RADIUS compiler](../network/radius-pilot/compile-policy.py) | Validates one enrolled MAC and two distinct VLAN IDs; writes a mode-0600 users file atomically | No controller connection, service reload or credentials read |
| [RADIUS module](../network/radius-pilot/files.module) and [site](../network/radius-pilot/pilot.site.in) | Dedicated FreeRADIUS 3 MAC/PAP authorization and VLAN attributes; reject unknown/malformed identities | Separate pilot configuration tree required; listen placeholder must be filled privately |
| [VPN helper](../network/stargate-vpn/vpn-exit.py) | Own namespace/tunnel, dual-stack defaults, guarded forwarding/NAT, ownership checks and partial-start cleanup | Root only for runtime, dry-run supported, never modifies the existing local tunnel/main defaults |
| [Namespace unit](../network/stargate-vpn/homeconfig-vpn-netns.service) | Creates the isolated path before the new daemon; cleans up after daemon shutdown | Enable flag and private config required |
| [Tailscale unit](../network/stargate-vpn/homeconfig-vpn-tailscaled.service) | Independent socket/state, port and syspolicy file; supervised inside isolated namespace | Fresh identity; no automatic login or advertisement command |
| [CI workflow](../.github/workflows/check.yml) | Python/app tests, FreeRADIUS parser and packet tests, native Linux namespace checks | Fictional fixtures on disposable runners only; no household credentials |

The VPN helper uses Python 3, iproute2, WireGuard tools, iptables/ip6tables, util-linux ip-netns
support and the host TUN device. Linux-only runtime, independent from portable dotsetup CLI code.
A fresh namespace contains only loopback and the new tunnel before the daemon creates its TUN.
The new Tailscale UDP port is 41642 INSIDE that namespace; no matching ordinary host-WAN port
is opened. Its transport still passes through the new VPN tunnel.

The helper checks existing ownership and refuses foreign namespace interfaces or deletion while
processes remain. Healthy repeated start does not flush a running Tailscale firewall. Missing routes
cause a failed check; there is no automatic WAN repair/fallback. Status checks ownership, interfaces,
guard jumps and defaults, not full chain equivalence, tunnel handshake or remote egress.

## Safe review on the development computer (no sudo)

Working directory: `~/projects/lexlapax/homeconfig`.

1. Run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`.
   Expected: validation, authorization-boundary, ownership and cleanup tests pass.
2. Run `python3 network/radius-pilot/compile-policy.py network/radius-pilot/policy.example.json --dry-run`.
   Expected: one-device policy validates; no file or identity is printed. Example VLANs/MAC are fictional.
3. Run `npm test --prefix apps/network-admin`.
   Expected: the preview tests pass and no live apply endpoint exists.
4. Inspect the public runtime example. It deliberately contains invalid placeholders and must
   be rejected if supplied to the VPN helper. Do not replace them with real values in Git.
5. Check GitHub Actions -> Staged payload checks for this commit. Expected: unit, radius-parser
   and namespace jobs all pass. Do not infer live AP/VPN behavior from these sandbox passes.

Do not run `tests/namespace-disposable.py` locally, with sudo, or on Stargate. It refuses to run
unless explicitly enabled on a GitHub Actions runner and uses fictional credentials. The RADIUS
container test likewise requires a disposable container and publishes no host ports.

## Private preparation: assistant-owned, before deployment approval

1. Prepare private deployment metadata from approved host/controller records: selected AP,
   approved phone identity, Home/VPN VLAN IDs, RADIUS source allowlist, package/runtime versions,
   listen address and protected destination prefixes. Keep them out of this public repository.
2. Stage a SEPARATE FreeRADIUS configuration directory using the chosen installed version's
   stock dictionaries/modules. Enable only `pap`, the dedicated files module and dedicated site
   for the pilot. Do not overwrite an existing global RADIUS server/configuration. The users file
   belongs under that tree's `homeconfig/pilot-users`; set service-readable ownership/mode after
   privileged installation while retaining restrictive access.
3. Require Message-Authenticator in the pilot client definitions and a privately provisioned shared
   secret. Permit only approved source addresses/UDP auth port through the host firewall. Verify
   actual NAS source and integrity compatibility before creating a live SSID. Do not use CI's dummy
   secret in production. CI's pinned FreeRADIUS 3.2.9 image is a parser compatibility fixture, not a
   statement that this version is the current approved production security baseline.
4. Prepare a NEW independent provider configuration. Save its key privately; never read or print
   it through the assistant. Prepare `/etc/home-config/vpn-exit/runtime.json` from the invalid public
   example, filling metadata privately. Its key path must remain within `/etc/home-config/vpn-exit/`.
   Runtime accepts only literal endpoint IPs, matching address families and explicit site-protected
   prefixes. Validate provider connection limits and whether a separate dual-stack key is available.
5. Stage the new namespace resolver file at `/etc/netns/stargate-vpn/resolv.conf` containing only
   the intended VPN resolver addresses. Stage a dedicated `/etc/home-config/vpn-exit/syspolicy.json`
   with `{}` initially, so the new instance does not inherit host-wide automatic exit policies.
6. Prepare a private diff of the host deployment changes. Public helper ownership stays here;
   dotsetup should install a reviewed pinned version rather than maintaining a divergent copy.
   No deployment mechanism or package installation is included in this commit. Resolve that
   integration in the private host configuration before presenting installation commands.

## Deployment gates and expected outcomes

The operator reviews the actual private diff before any package/service/firewall/controller change.
Private credential provisioning is an operator task. Do not request secret contents in chat.

Remote setup order, once specifically approved:

1. Install prerequisites and the reviewed helper/unit files through the host deployment mechanism.
   Expected destinations: helper `/usr/local/libexec/home-config/vpn-exit.py`; the two new units
   under `/etc/systemd/system/`. Do not enable the existing/default Tailscale unit again or change it.
2. Install reviewed root-owned private metadata, namespace resolver and separate syspolicy;
   provision the new key as root-owned regular mode 0600. Keep the new instance's state/runtime
   directories separate; never copy the existing Tailscale state into them.
3. Validate metadata with the helper's `start --config <private-runtime-json> --dry-run` as the
   operator. It prints non-secret configuration/commands; keep that output private. Expected:
   only the new namespace/tunnel, namespace routes and namespace firewalls appear.
4. Create the enable flag ONLY after review, reload units and start ONLY the new namespace unit.
   Expected: namespace status and non-secret handshake check pass before starting the new daemon.
5. Start the new Tailscale unit WITHOUT exit advertisement. Operator performs enrollment against
   `/run/tailscale-vpn/tailscaled.sock`, with hostname `stargate-vpn`, DNS/route acceptance disabled,
   SSH/web management disabled, no subnet advertisements and exit advertisement initially OFF.
   Validate the current `tailscale up/set` flags during installation; never use the default socket.
6. Review effective tailnet policy and approve only the intended test access/exit advertisement.
   Narrow added grants do not override existing broad grants. Follow the [remote phone test](remote-exit-test.md).
7. Stop on any unexpected fallback, DNS path, route/interface, lost authorized access or regression.
   Test new-tunnel loss, restart and reboot before allowing general use. Namespace checks alone
   do not establish actual provider egress or client kill-switch behavior.

Local setup is independently approved: install only the dedicated RADIUS pilot service/profile,
verify its parser and local authentication before the one-AP pilot SSID. Follow the
[replacement pilot procedure](same-ssid-alternatives.md), not the blocked override procedure.
Pilot enrollment can require two connection attempts because the randomized MAC is SSID-specific.
Production Home authentication remains unchanged until a separate all-client rollout is approved.

## Recovery and rollback

Remote: the operator explicitly returns the test client's Exit Node to its recorded previous choice.
Withdraw the NEW exit advertisement if reachable. Stop the NEW Tailscale unit first, then the NEW
namespace unit. The helper refuses cleanup with surviving processes or foreign interfaces. Preserve
private identity state securely or revoke it as an explicit operator decision. Do not delete existing
Tailscale state, disable the existing gateway service, flush host firewalls or move the existing tunnel.

Local: reconnect the phone to its original household SSID before disabling the pilot. Remove only
pilot-owned profile/SSID/mapping/service changes. If another admin changed a mapping meanwhile,
stop and review that conflict. Do not restore Home automatically when VPN verification fails.

No automatic deployment, phone change, credential provisioning or live failure test has been performed.
