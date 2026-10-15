export const devices = [
  { id: 'example-phone', name: 'Example phone', connection: 'wifi', network: 'home', status: 'Sample device', ssid: 'House Wi-Fi' },
  { id: 'example-tv', name: 'Example TV', connection: 'wifi', network: 'vpn', status: 'Sample device', ssid: 'House Wi-Fi' },
  { id: 'example-laptop', name: 'Example remote laptop', connection: 'tailscale', network: 'home', status: 'Sample device' },
];

export function planChange(input, inventory = devices) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('Choose a device and a network.');
  const device = inventory.find(entry => entry.id === input.deviceId);
  if (!device) throw new Error('This device is unavailable. Refresh the device list.');
  if (!['home', 'vpn'].includes(input.target)) throw new Error('Choose Home or VPN.');
  if (!['wifi', 'tailscale'].includes(device.connection) || device.protected) throw new Error('This device cannot be moved with this tool.');
  if (device.network === input.target) throw new Error('This device is already assigned to that network.');
  const vpn = input.target === 'vpn';
  return {
    preview: true,
    executable: false,
    deviceId: device.id,
    deviceName: device.name,
    current: device.network,
    target: input.target,
    title: `Review ${device.name} → ${vpn ? 'VPN' : 'Home'}`,
    description: vpn ? 'Internet through the Netherlands VPN exit.' : 'Internet through your home connection.',
    steps: device.connection === 'wifi' ? [
      'Save the current device assignment for Undo.',
      `Assign only this client to ${vpn ? 'the VPN network' : 'the Home network'} in the network controller.`,
      'Request a reconnect. Keep the existing Wi-Fi name and password.',
      'Check the new network assignment, IPv4 and IPv6 addresses, and DNS.',
      'Confirm internet egress on the client before marking the move verified.',
    ] : [
      'Open Tailscale on this device.',
      'Open the Exit Node menu.',
      `Select ${vpn ? 'stargate-vpn' : 'stargate'}.`,
      'Check internet egress and DNS on the client.',
      'Tailnet and home access remain governed by their existing access policies.',
    ],
    notices: [
      'This is a preview using sample devices. No settings will be changed.',
      device.connection === 'wifi' ? 'A real move briefly interrupts calls, streams and other connections. If necessary, toggle Wi-Fi off and on.' : 'The exit node is selected on the client. This app cannot currently change a remote device’s Tailscale settings.',
      ...(vpn ? [device.connection === 'wifi' ? 'The local VPN network blocks home and admin access.' : 'VPN internet egress does not by itself remove existing tailnet permissions.', 'If the VPN fails, internet should stop. Never automatically fall back to Home.'] : ['Returning Home is an explicit change of internet path.']),
    ],
  };
}
