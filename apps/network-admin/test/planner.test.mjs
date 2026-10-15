import test from 'node:test';
import assert from 'node:assert/strict';
import { planChange } from '../planner.mjs';
import { createServer } from '../server.mjs';

test('Wi-Fi preview preserves SSID and explicitly requires egress verification', () => {
  const plan = planChange({ deviceId: 'example-phone', target: 'vpn' });
  assert.equal(plan.executable, false);
  assert.ok(plan.steps.some(s => s.includes('existing Wi-Fi name and password')));
  assert.ok(plan.steps.some(s => s.includes('Confirm internet egress on the client')));
  assert.ok(plan.notices.some(s => s.includes('Never automatically fall back')));
});

test('remote instructions use vendor-neutral exit identity and retain separate access policy', () => {
  const plan = planChange({ deviceId: 'example-laptop', target: 'vpn' });
  assert.ok(plan.steps.includes('Select stargate-vpn.'));
  assert.ok(plan.notices.some(s => s.includes('does not by itself remove')));
});

test('reject unknown destinations, clients and protected infrastructure', () => {
  assert.throws(() => planChange({ deviceId: 'example-phone', target: 'admin' }));
  assert.throws(() => planChange({ deviceId: 'unknown', target: 'vpn' }));
  assert.throws(() => planChange({ deviceId: 'router', target: 'vpn' }, [{ id: 'router', connection: 'wifi', protected: true }]));
  assert.throws(() => planChange({ deviceId: 'example-phone', target: 'home' }));
});

test('API exposes only sample previews and no apply endpoint', async t => {
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  const url = `http://127.0.0.1:${server.address().port}`;
  const inventory = await (await fetch(`${url}/api/devices`)).json();
  assert.equal(inventory.liveChanges, false);
  const plan = await fetch(`${url}/api/plans`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ deviceId: 'example-phone', target: 'vpn' }) });
  assert.equal(plan.status, 200);
  assert.equal((await plan.json()).executable, false);
  assert.equal((await fetch(`${url}/api/apply`, { method: 'POST' })).status, 404);
  assert.equal((await fetch(`${url}/api/plans`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' })).status, 400);
  assert.equal((await fetch(`${url}/api/plans`, { method: 'POST', headers: { 'Content-Type': 'application/json', Origin: 'https://example.invalid' }, body: '{}' })).status, 403);
  assert.equal((await fetch(`${url}/../server.mjs`)).status, 404);
});
