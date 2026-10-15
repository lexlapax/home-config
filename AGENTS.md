# Working in home-config

This repository is PUBLIC. Never copy private household inventory, real client identities, network
addresses, keys, tokens, passwords, controller exports or captures into it. Use fictional examples;
keep deployment values in ignored private files or a secret manager. Do not read secret values.

Read README.md and docs/network-admin-plan.md before changing scope. Code lives in apps/<name>/;
shared designs and sanitized templates live in network/. Machine bootstrap remains in dotsetup.

Run the affected app's tests before committing and add a succinct CHANGELOG.md entry. Do not
modify live network settings, deploy services, use sudo, or grant access without authorization.
Keep operator wording vendor-neutral: Home, VPN, stargate, stargate-vpn. Adapter internals can
name products when necessary for maintenance.

Clearly distinguish requested settings, observed state and verified behavior. No automatic fallback
from VPN to Home. Do not claim controller readback verifies client egress. Protect infrastructure
and management clients from routine moves. Do not assume a server can change an unmanaged
Tailscale client's exit-node selection.

Give clear numbered manual steps with the exact machine, controls and expected result. Every
handoff states completed work, pending work, the next action and who owns it. Do authorized work
autonomously; request only the operator actions that actually require them. No agent attribution.
