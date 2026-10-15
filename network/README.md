# Shared network design

This directory will hold reusable topology models, assignment schemas and sanitized deployment
examples. Actual household inventory and deployment values are private and are not stored here.

The initial operator profiles are `home` and `vpn`. For remote Tailscale clients the intended exit
identities are `stargate` and `stargate-vpn`. Local VLAN assignment and remote internet egress are
separate mechanisms. Tailnet permissions remain a separate policy.
