# Same-SSID assignment: researched replacement plan

Status: candidate selected; no live settings changed, no new SSID or RADIUS server created.
The previous controller override form could not select the third-party-gateway VPN network.
Opening and canceling that form did not move the test client.

## Findings

| Method | Same SSID/password during moves | 6 GHz | Assessment |
| --- | --- | --- | --- |
| Current client Virtual Network Override | Yes for offered targets | Not the observed blocker | VPN target absent; do not force an undocumented value |
| Private pre-shared keys (PPSK) | Same SSID; password determines VLAN | Unsupported under documented WPA2-only PPSK | Does not meet this household's combined requirement |
| MAC-based RADIUS VLAN assignment | Candidate: keep personal Wi-Fi password and change AP authorization | UI exposes the option with current bands/security; not proven | Recommended isolated pilot |
| Enterprise RADIUS / certificates | Same SSID after enrollment | WPA3 Enterprise is a potential path | Requires client onboarding/security-mode migration; more disruptive |
| Per-client internet routing only | Can preserve existing Wi-Fi association | Independent of Wi-Fi band | Changes egress, not VLAN membership or local-layer isolation; separate fallback proposal |

Ubiquiti documents [MAC-based RADIUS authentication and optional VLAN assignment](https://help.ui.com/hc/en-us/articles/115004589707-MAC-Based-VLAN-Assignment-Using-802-1x-in-UniFi-Network).
It specifies a separator-free MAC identity, VLAN ID, Tunnel Type 13 and Tunnel Medium Type 6.
The installed Home SSID form exposes an enabled RADIUS MAC Authentication control while its
personal WPA2/WPA3 security and 6 GHz are enabled. This is availability evidence, not a successful
WPA3/6 GHz dynamic-VLAN test. No RADIUS checkbox was enabled during inspection.

The [PPSK documentation](https://help.ui.com/hc/en-us/articles/29887064407319-Using-PPSK-RADIUS-for-Multiple-VLANs-On-an-SSID-in-UniFi-Network)
says PPSK is WPA2-only and excludes 6 GHz. The [Wi-Fi settings overview](https://help.ui.com/hc/en-us/articles/32065480092951-UniFi-WiFi-SSID-and-AP-Settings-Overview)
describes RADIUS MAC Authentication as centralized admission with dynamic VLAN/policy support.
None of these sources guarantees this exact AP/firmware/security combination; testing remains required.

## Recommended pilot

Use a temporary `network-pilot` SSID on ONE approved healthy Wi-Fi 7 AP. It copies the relevant
security/band behavior of the existing Home SSID but uses a new operator-entered password and
its own RADIUS profile. Existing household SSIDs remain unchanged. This requires the test phone
to join the temporary SSID once; subsequent Home -> VPN -> Home moves keep that pilot SSID.
Do not present this initial pilot connection as achieving the final no-SSID-change rollout.

The RADIUS server runs on Stargate's trusted management side, separately from the isolated
remote VPN-exit namespace. Use an established RADIUS implementation such as FreeRADIUS;
do not invent an authentication protocol inside the web app. The app eventually manages a
restricted assignment store and requests a reconnect through the controller.

Pilot policy:

- Accept only the explicitly enrolled test MAC on the pilot. Reject unknown identities; no broad
  default Access-Accept or VLAN fallback is part of the first test.
- Keep the Wi-Fi personal authentication/password in place. MAC lookup chooses authorization
  and VLAN; a MAC is spoofable and must not be treated as proof of a person's identity.
- Resolve Home and VPN to numeric VLAN IDs through private deployment configuration. Do not
  depend on the controller's per-client override target list for AP-level VLAN selection.
- Advertise the configured VLAN using the documented tunnel attributes. Require wireless
  RADIUS VLAN support in the selected profile if the installed UI exposes that setting.
- Allow RADIUS access only from approved AP/controller source addresses as actually observed;
  protect transport with strong privately provisioned shared secrets and supported integrity checks.
  Validate each component's Message-Authenticator behavior and current security guidance.
- Restrict client reconnect requests to the enrolled test device. Do not rely on Change of
  Authorization (CoA) support before proving it; a controller reconnect is sufficient for the pilot.

## Concrete preparation sequence (assistant)

1. Inspect the chosen AP's firmware and available SSID capacity, plus controller RADIUS profile
   fields, without changing them. Record private values outside this public repository.
2. Prepare a version-pinned RADIUS configuration and service in the host deployment repository.
   Build a narrow policy store for the enrolled test MAC and two allowed VLANs; stage and test it
   without connecting production APs. No server installation is authorized by this research step.
3. Prepare the exact controller profile and pilot SSID changes for review. Name the selected AP,
   target VLANs, security mode, PMF, bands, server address/ports and allowed sources privately.
   Confirm that personal authentication plus RADIUS MAC authorization can be selected together
   without downgrading 6 GHz, security or password behavior. Stop if the UI requires a downgrade.
4. Present the staged payload and exact affected devices before requesting deployment approval.
   Operator privately enters credentials/shared secrets; they are not pasted into chat or Git.
5. Once authorized, install the RADIUS service with firewall restrictions, verify daemon/config
   health, create only the new pilot profile/SSID, and read back selected non-secret settings.

## Phone sequence after pilot deployment (operator)

These steps are conditional on the assistant completing and verifying the approved pilot setup.
Do not perform them while the pilot is absent.

1. On Samsung, note the current Wi-Fi, Mobile data, Private DNS and VPN settings so they can be
   restored. Turn Mobile data OFF and disconnect Tailscale/other VPNs. Leave Wi-Fi ON.
2. Open Settings -> Connections -> Wi-Fi and join `network-pilot` using the privately chosen
   pilot password. The assistant must explain the first-enrollment behavior before this step:
   unknown MACs are rejected until enrolled, and the pilot SSID can have a different randomized MAC.
3. Open the gear beside `network-pilot`; report its displayed MAC privately. Do not change MAC
   type. The assistant enrolls ONLY this identity after confirming the physical test phone.
4. Reconnect to `network-pilot`. Expected: Home assignment and working baseline internet.
   Assistant verifies RADIUS reply VLAN, actual AP/client network, gateway and DHCP observations.
5. Remain on `network-pilot` while the assistant changes ONLY this MAC's mapping to VPN and
   reconnects the client once. If instructed, toggle Wi-Fi OFF, wait five seconds, then ON.
6. Open https://ip.me, https://test-ipv6.com and https://dnsleaktest.com. Expected: VPN egress
   for both families, working IPv6 and intended resolver observations. Disable alternate DNS
   only through an agreed temporary test; restore the noted settings afterward.
7. Test the supplied private admin URLs. Expected: local VPN isolation. Test sustained video.
   Assistant verifies actual 6 GHz association; falling back to 5 GHz is not a 6 GHz pass.
8. Assistant restores the exact original Home mapping and reconnects once. Repeat addressing,
   IP/DNS checks. Expected: Home returns while SSID and password remain unchanged.
9. At pilot closeout, reconnect to the original household SSID and restore previous phone settings.

Stop at wrong VLAN, failure to renew, unexpected Home egress in VPN mode, missing IPv6,
unexpected admin access, or loss of 6 GHz. No automatic VPN-to-Home fallback is allowed. Remove
or disable only the pilot SSID after returning the test phone to the original household SSID.
Restore/delete only the pilot profile, mapping and server components owned by this experiment.
Do not change production Home authentication to recover a failed pilot.

## Gates before touching the existing Home SSID

Prove personal WPA3/6 GHz compatibility, third-party target VLAN assignment, DHCP/RA renewal,
DNS, local isolation, reassignment/Undo, AP roaming and server-outage behavior. Then define how
existing and unknown clients are handled, how stable randomized MACs are enrolled, and what
happens during RADIUS failure. An allowlisted pilot must not become a production lockout of
unenrolled household clients. Any default-Home policy is a separate reviewed admission decision.

Switching the current Home SSID to MAC RADIUS affects every client that authenticates there.
It needs a separate rollout and recovery window, not just one-device test authorization. Existing
sessions may retain their old VLAN until reauthentication; controller reconnect and observation
must be part of the app workflow. Credentials remain local/secret-managed; no browser-login
session is needed by the eventual service.

## Independent remote work

`stargate-vpn` remains independent of Wi-Fi/RADIUS. Read-only checks found the host's `ip`,
`tailscaled`, `wg` and TUN device available, with existing Tailscale/local VPN services active.
These are prerequisites, not an operational isolated exit. Proceed by staging the reviewed
namespace, firewall, service and credential-reference payload; validate in a sandbox before
requesting installation. New VPN credentials and a new tailnet identity still need private enrollment.

## Immediate next step

Assistant owns preparation of the sandboxed RADIUS pilot configuration and the independent
remote-exit payload. Operator has no phone task now. Next operator actions will be review of the
concrete pilot scope, private credential entry, and the numbered phone test after approved setup.
