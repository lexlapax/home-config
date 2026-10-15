# Device Networks implementation plan

## Outcome

Give the operator one understandable Home/VPN interface. Local Wi-Fi devices retain their SSID
and password. Remote Tailscale devices select either `stargate` (home internet) or `stargate-vpn`
(Netherlands VPN internet). Provider names stay out of operator controls.

The primary request is local client reassignment. Remote Tailscale VPN egress is the secondary
request. Both need separate proofs before live app controls are enabled.

## Feasibility and current evidence

The installed network controller exposes Virtual Network Override and Reconnect for an online
wireless client. Moving that client into a third-party-gateway VLAN has not been validated.
The existing VPN policy applies only to the local VPN client interface; it does not currently
route exit-node clients through the VPN.

Recommended remote design: a second Tailscale instance, isolated with its own persistent identity
and network namespace or container, advertising exit-node capability as `stargate-vpn`. Review
its transit routing, IPv4/IPv6 NAT, DNS, return paths, MTU and firewall ordering before deployment.
Use a new WireGuard tunnel as the namespace's only ordinary internet interface. Its encrypted
socket stays in the host namespace; Tailscale control/peer traffic and forwarded client internet
traffic all traverse the new VPN tunnel. This revises the shared-tunnel goal: a separate VPN
configuration/key avoids changing the working local tunnel. Preserve the existing exit node,
subnet router and DNS services. See [the isolated design](../network/stargate-vpn/README.md).

A central web service cannot generally choose the exit node on unmanaged phones. Version one
provides exact client instructions. Endpoint management could be evaluated separately later.
Selecting a VPN exit does not remove tailnet permissions. Local VPN isolation and remote access
policy must remain explicit and separately verified.

References: [UniFi VLAN assignment](https://help.ui.com/hc/en-us/articles/9761080275607-Creating-Virtual-Networks-VLANs),
[Tailscale exit nodes](https://tailscale.com/docs/features/exit-nodes),
[Tailscale containers](https://tailscale.com/docs/features/containers/docker).
These document building blocks, not a guarantee for this combined topology.

## Operator workflow

1. Find a device by friendly name. Show online/last-seen status and observed connection path.
2. Choose Home or VPN. Explain whether this changes local access as well as internet egress.
3. Review the device, previous assignment, intended effect and expected interruption.
4. For supported local moves, explicitly confirm, save rollback state, change only the client's
   assignment, reconnect once, then wait for fresh network/address observations.
5. Display separate states: requested, controller accepted, device reconnected, addressing
   observed, client egress verified. Never claim the last state from controller readback alone.
6. Offer explicit Undo of the exact prior assignment. If another admin changed it meanwhile,
   stop and show the conflict rather than overwriting their work.
7. For remote clients, show: Open Tailscale -> Exit Node -> stargate-vpn (or stargate for Home).
   If observation is unavailable, say unknown; do not infer selection merely from online status.

No automatic VPN-to-Home fallback. A failed VPN verification does not authorize ordinary-WAN
routing. Any timed rollback that changes internet exposure needs explicit approval in advance.
Do not move gateways, switches, APs, the app host or the operator's management device.
Stable per-SSID randomized MACs can be registered; changed identities require reconfirmation.
Offline devices and static-address clients are excluded from the initial move workflow.

## Delivery sequence

1. **Preview (implemented):** sample list, search, Home/VPN review and remote instructions.
   No real inventory, credentials or live writes.
2. **Local proof (blocked at target selection):** with authorization, test one named client Home -> VPN -> Home,
   retaining its SSID/password. Verify IPv4, IPv6, DNS, isolation and recovery. Keep separate
   administration access. If override cannot target the required VLAN, revise the design before
   promising same-SSID switching; do not move an entire SSID or shared port as a workaround.
3. **Remote proof (pending):** draft isolated stargate-vpn service and routing guards, review,
   provision identity privately, then deploy with authorization. Test cellular egress for both
   families, DNS, sustained traffic, tunnel/route loss, restart and reboot recovery. Verify existing
   exit/subnet access and local VPN clients still work. Avoid overlapping VPN apps on phones.
4. **Read-only integration:** dedicated controller authentication; narrow supported API adapter,
   selected fields only, no raw exports. Verify whether supported APIs expose required operations;
   isolate any version-dependent API behind tests and compatibility checks. No saved Chrome session
   dependency in the deployed service. Display data freshness and unknown states.
5. **Live workflow:** authenticated admin access, CSRF protection, destination allowlist, job
   persistence, per-device locking, read-before-write conflict checks, audit history and explicit Undo.
   Scope credentials to required operations where the controller supports it; never claim narrower
   privileges than the credentials actually provide.
6. **Deployment:** host privately on Stargate behind authenticated admin/tailnet access, no WAN
   exposure. Operator approves any access grants. Runtime state and credentials stay outside Git.
   Select application authentication and service packaging before opening a listener beyond loopback.

## Repository ownership

- `apps/network-admin/`: reusable application code, adapters and tests.
- `network/`: sanitized topology schemas and reusable network templates.
- `docs/`: operator procedures, implementation plans and verification criteria.
- `dotsetup`: machine installation, system services and private deployment references for now.

Do not duplicate executable configuration between repositories. If deployment templates later
move here, migrate ownership explicitly and update dotsetup references in the same rollout.
No household inventory or existing private repository files are published here.

## Immediate next action

Prepared: [local one-client procedure](local-client-test.md), [isolated exit design and configuration
manifest](../network/stargate-vpn/README.md), and [remote Samsung test](remote-exit-test.md).
No live changes have been performed; the manifest is review-only, not an installer.

Next: assistant researches a compatible dynamic-VLAN alternative. The current controller override
selector excludes the third-party VPN network; the draft was canceled and no move was performed.
After a replacement procedure is prepared, operator approves the named test and sequence.
Assistant then carries out controller steps through the existing Chrome session and requests only
the phone checks. Remote implementation can be prepared independently; enrollment, service
deployment and failure tests require a reviewed payload and operator authorization.
