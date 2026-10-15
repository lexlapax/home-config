# Shared network design

This directory will hold reusable topology models, assignment schemas and sanitized deployment
examples. Actual household inventory and deployment values are private and are not stored here.

The initial operator profiles are `home` and `vpn`. For remote Tailscale clients the intended exit
identities are `stargate` and `stargate-vpn`. Local VLAN assignment and remote internet egress are
separate mechanisms. Tailnet permissions remain a separate policy.

[stargate-vpn/](stargate-vpn/README.md) contains the review-only isolated exit design and
configuration manifest. It uses a separate tunnel/key and does not move the existing local tunnel.

[radius-pilot/design.example.json](radius-pilot/design.example.json) records the candidate
one-AP/one-phone MAC authorization design; it is not an installer or a production admission policy.
