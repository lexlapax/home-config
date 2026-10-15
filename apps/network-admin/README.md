# Device Networks

A small operator interface for choosing Home or VPN internet paths. Current version: sample-device
preview only. Search devices, review a local move, or view remote exit-selection instructions.

Run `npm test` and `npm start` here; visit http://127.0.0.1:3000. Node.js 22+ is required. There are no
third-party dependencies. The server binds to loopback and contains no live mutation endpoint.

- `planner.mjs`: proposed actions and validation; Home/VPN targets only.
- `server.mjs`: static assets, sample inventory and plan API.
- `public/`: responsive interface using text-only DOM rendering for device data.
- `test/`: rejected targets/infrastructure, remote instructions and HTTP preview boundaries.

A real deployment needs authentication, private inventory, controller adapters, persistent jobs,
rollback state, end-to-end validation and explicit operator authorization. Do not expose the preview
publicly or treat it as a completed administration service. See ../../docs/network-admin-plan.md.
