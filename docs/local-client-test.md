# Same-SSID client move: operator test

Status: blocked at target selection; no assignment saved and no client move performed. Run only after the operator approves
one named device and the specific Home -> VPN -> Home sequence. Real names, MACs, addresses
and screenshots remain private. Keep this public document free of filled-in household values.

## Feasibility result (2026-10-15)

Read-only client identification and gateway health checks passed. Opening the per-client override
form exposed controller-routed Home and DMZ choices, but not the existing third-party-gateway VPN
network. The draft was canceled without clicking Apply Changes; override remained disabled and
the client retained its original Home assignment. No reconnect was requested.

This UI workflow cannot currently perform the intended move. Do not force an undocumented API
value or change the entire SSID/shared port to bypass the selector. Research an AP-level dynamic
VLAN method, including RADIUS-based assignment, and verify compatibility with the existing
security mode and 6 GHz before proposing a replacement. This is a candidate, not an approved
migration. The remote isolated exit design is independent of this controller limitation.

Operator may restore their original Mobile data and VPN settings while this is investigated.
Repeat phone preparation only when the replacement test is concrete and authorized.

## Before the test

Assistant, using the existing signed-in Chrome profile:

1. Open UniFi Network -> Client Devices. Select the approved test phone by its current Wi-Fi MAC,
   not its guessed model. Confirm it is online, uses DHCP and is not the administration device.
2. Record privately: displayed name, MAC, SSID, AP, current network, Virtual Network Override
   enabled/disabled state and its exact value, plus any fixed-IP setting. Do not change fixed-IP
   settings during this test. Reject a static-address client for this first test.
3. Open the client's Settings -> IP Settings. Confirm Virtual Network Override is available.
   Inspect the available network choices only when the control's save behavior is understood.
   If the VPN network is unavailable, stop; do not change the SSID or a shared switch port.
4. Confirm the VPN gateway is healthy and the AP uplink carries both target networks. Prepare
   the exact previous override as the Undo operation. Existing controller and host records are
   the private source for expected subnet, router and DNS values.

Operator, on the Samsung test phone:

1. Keep a different computer connected to the admin network, with the controller open.
2. Open Settings -> Connections -> Wi-Fi. Connect the test phone to its usual Home SSID and
   leave that same SSID selected throughout this test. Do not forget the network or change its password.
3. Turn Mobile data OFF in Quick Settings. Disconnect Tailscale and any other VPN on the test
   phone. This prevents a second connection from hiding a failed Wi-Fi move.
4. Open Settings -> Connections -> More connection settings -> Private DNS. Note its existing
   selection, then choose Off for the DNS-path test. Restore the original setting at the end.
   Note any browser Secure DNS setting; turn it off for resolver verification and restore afterward.
5. In the browser, open https://ip.me and https://test-ipv6.com. Record the baseline public IPv4,
   IPv6 availability and provider/country privately. Open https://dnsleaktest.com and run Standard test.
6. Tell the assistant: "Phone is on Home, mobile data and VPNs are off; ready for the approved move."

## Move Home -> VPN

Assistant:

1. In the approved client's Settings -> IP Settings, enable Virtual Network Override and select
   the existing VPN network. Review the displayed change before clicking Apply/Save (the label
   may vary by controller version). This is a per-client change only.
2. Read the saved setting back, then click that client's Reconnect once. Wait up to 60 seconds
   for a fresh association and addressing. Record requested and observed states separately.
3. If the client stays on the old address, ask for one Wi-Fi toggle. If it remains wrong, stop;
   do not repeatedly reconnect or call the move successful based on controller readback.

Operator:

1. If instructed, open Quick Settings, turn Wi-Fi OFF, wait five seconds, then turn Wi-Fi ON.
   Confirm it reconnects to the SAME SSID. Leave Mobile data OFF.
2. Open Settings -> Connections -> Wi-Fi -> gear beside the connected network -> View more,
   where available. Compare IP/router/DNS values with the private expected VPN values supplied
   by the assistant. Some Android versions omit IPv6 details; report that instead of guessing.
3. Open https://ip.me, https://test-ipv6.com and https://dnsleaktest.com again. Expected:
   Netherlands VPN egress for both families, IPv6 functioning, and expected VPN resolver results.
4. Open the private controller and gateway administration URLs supplied by the assistant.
   Expected: unavailable from the local VPN network. Do not post those URLs publicly.
5. Play a video for two minutes. Report whether it plays normally. Keep phone settings unchanged
   until the return move is complete.

Assistant: verify private gateway DHCP/neighbor observations where available. A controller may
misreport addressing when the DHCP server is external; resolve discrepancies using gateway and
client observations. Do not mark IPv6 or DNS verified merely because browsing works. Browser
checks are functional evidence; packet captures are a separate requirement for stronger leakage proof.

Stop on wrong egress, missing IPv6, unexpected admin access or failure to reconnect. Report exactly
what failed. Do not silently restore Home; the approved return sequence below is an explicit step.
Gateway-wide tunnel-down tests are excluded here because they interrupt other VPN clients.

## Return VPN -> Home / Undo

Assistant:

1. Check that the client's current override still matches this test's change. If another admin
   changed it, stop and report the conflict.
2. Restore the EXACT previous state: if override was off, turn it off; if it was on, restore its
   original network. Saving an explicit Home override is not equivalent to restoring a disabled override.
3. Apply/Save, read back, and Reconnect once. Confirm fresh Home addressing and unchanged SSID.

Operator:

1. If instructed, toggle only Wi-Fi off and on as above.
2. Repeat the public IP, IPv6 and DNS checks. Expected: the original Home path returns.
3. Restore the noted Private DNS and browser Secure DNS settings, then restore Mobile data and
   Tailscale/other VPN to their previous states. Do not enable a VPN before the return checks finish.
4. Report: same SSID throughout; Home restored; any manual toggle needed in each direction.

If reconnect/Undo fails, retain access from the separate admin computer. The assistant restores
only the approved client's recorded override through the controller; do not reset APs, switches,
DHCP services or the gateway. Further changes require a specific recovery proposal.

## Acceptance record (private)

Record initial/final override, unchanged SSID, new addressing, IPv4/IPv6 egress, DNS observations,
isolation checks, reconnect timing and whether manual toggles were needed. App implementation
proceeds only after the required checks pass; unsupported or unobserved checks stay explicitly pending.
