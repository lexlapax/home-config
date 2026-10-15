# home-config

Home infrastructure configuration and operator tools. This is a public repository: examples use
fictional devices, and private inventory, credentials, addresses and controller exports stay outside Git.

- [`apps/network-admin/`](apps/network-admin/): Device Networks, a phone-friendly Home/VPN control app.
- [`network/`](network/): reusable network design and public configuration examples.
- [`docs/`](docs/): architecture, implementation plan and operator procedures.

The first app is a runnable **preview**, with sample devices and review screens. It does not read
live inventory, connect to a controller, or change routes or client assignments.

```sh
cd ~/projects/lexlapax/homeconfig/apps/network-admin
npm test
npm start
```

Requires Node.js 22 or newer. No dependencies or package installation are needed. Open
<http://127.0.0.1:3000> on the same machine. The preview listens only on loopback; remote hosting
and authenticated access are later deployment steps.

See [the implementation plan](docs/network-admin-plan.md) for what is proven, what remains,
and the next operator action. System deployment configuration currently remains in the separate
`dotsetup` repository; no private material is copied here.

Review-ready procedures: [same-SSID local test](docs/local-client-test.md),
[isolated stargate-vpn design](network/stargate-vpn/README.md),
and [remote exit test](docs/remote-exit-test.md). These are drafts; no live exit or client switch has been deployed.

The override test found an unsupported target. See [the researched replacement and isolated
MAC RADIUS pilot](docs/same-ssid-alternatives.md); current household Wi-Fi remains unchanged.
