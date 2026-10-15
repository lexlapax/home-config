# Remote VPN exit: Samsung operator test

Status: review-only. The new exit is not deployed. Complete the local proof separately and deploy
only after the isolated-exit configuration, credentials and restricted test access are approved.

## Preconditions (assistant)

Verify the namespace design checks in ../network/stargate-vpn/README.md, dedicated identity and
healthy dual-stack tunnel. Keep the existing Home exit and management access available. Supply
the operator with exact private admin URL(s) expected to remain accessible under tailnet policy.
Do not publish actual client identities, addresses or results in this public document.

## Operator steps on Samsung

1. Open Quick Settings: turn Wi-Fi OFF and Mobile data ON. Disconnect the provider VPN app or
   any other VPN. Keep the phone's Tailscale app as the only active VPN service.
2. Open Tailscale and connect. Open Exit Node and select `stargate`.
3. Open https://ip.me and https://test-ipv6.com. Expected: the existing Home exit addresses and
   working IPv6. Record results privately. Check approved home/admin access as the baseline.
4. Return to Tailscale -> Exit Node and select `stargate-vpn`. Keep any "Allow LAN access"
   option OFF for this test. If the new exit is absent/offline, stop and tell the assistant.
5. Open https://ip.me and https://test-ipv6.com again. Expected: Netherlands VPN egress for
   IPv4 AND IPv6, with functioning IPv6. Run Standard test at https://dnsleaktest.com.
6. Play a video for two minutes. Check the private home/admin URL(s) supplied by the assistant.
   Access should match existing tailnet policy; VPN egress is not a new grant or revocation.
7. Keep `stargate-vpn` selected during the coordinated NEW-tunnel failure test. Do not select
   None, enable Wi-Fi, or enable another VPN to make a test page work.
8. When told the NEW tunnel is down, try a fresh uncached page and continue the active video.
   Expected: public internet fails/stalls. Report any page loading through ordinary cellular internet.
9. When told the tunnel is restored, retry. Expected: VPN egress returns. If it needs a manual
   exit re-selection, report that; do not record recovery as automatic.
10. At the end, explicitly select Exit Node -> `stargate` to return to Home, or select the exact
    exit setting recorded before the test. Verify restored egress. Restore the phone's prior Wi-Fi,
    Mobile data and VPN settings.

If the phone UI labels differ, the operator reports the visible screen before proceeding. The
assistant supplies exact revised steps; the operator does not guess a similarly named control.

## Assistant validation and stop conditions

Record configuration accepted, node reachable, client-reported egress and DNS proof separately.
DNS tests must distinguish public queries from intentionally retained private split-DNS queries.
Browser DoH/Android Private DNS may bypass advertised resolvers: note their settings and perform
an explicitly agreed temporary resolver test if needed, restoring them afterward. Successful IP
checks alone do not establish DNS behavior. Use private packet capture for stronger leakage proof.

Stop on non-VPN public egress, missing IPv6, unexpected public DNS path, lost authorized admin
access, ordinary cellular fallback, or regression of the existing exit/local VPN clients.

After initial checks pass, independently approve namespace daemon restart, new-tunnel deletion/
recreation, and host reboot tests. Validate existing SSH, DNS, subnet routing, Home exit, local VPN
clients and failed-new-exit behavior before and after. Do not interrupt the existing local VPN tunnel
for a remote-exit test. Record performance with direct/relayed Tailscale transport and test sustained
transfers before enabling general use.

The assistant owns setup verification and recovery through the unchanged host/admin path; the
operator owns phone selections and interactive browser checks. No secret contents are returned
in chat or committed to Git.
