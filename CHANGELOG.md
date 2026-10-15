# Changelog

## 2026-10-15

- network: add a minimal standalone RADIUS pilot server template for private host packaging and validate it with real authentication packets.

- tests: recognize the standard zero tag in RADIUS VLAN reply attributes.

- tests: isolate MAC/PAP parser checks from unrelated stock EAP modules, matching the dedicated pilot configuration.

- tests: restrict RADIUS discovery to binary directories and expose parser diagnostics for fictional CI fixtures.

- tests: restrict container binary discovery to executable files so package metadata cannot be selected.

- tests: locate the pinned FreeRADIUS image binaries independently of its entrypoint PATH setup.

- network: use loose reverse-path filtering inside the isolated exit and adapt disposable tests to the official server binary and tailnet return routes.

- network: stage one-device RADIUS policy compilation and isolated VPN exit runtime/services with unit and disposable CI integration checks.

- network: research same-SSID alternatives and specify an isolated MAC RADIUS pilot with explicit WPA3/6 GHz and production rollout gates.

- network: record unavailable third-party VPN override target; cancel the unsaved client test and require a compatible replacement design.

- docs: require thoroughly researched, detailed operator configuration steps with explicit expected outcomes, verification and recovery.

- network: draft the same-SSID client test, isolated stargate-vpn exit manifest and remote Samsung validation/rollback procedure.

- network-admin: add a runnable sample-device preview, vendor-neutral Home/VPN plans, validation tests and phased implementation plan.
