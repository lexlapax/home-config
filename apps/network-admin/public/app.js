const list = document.querySelector('#devices');
const message = document.querySelector('#message');
const search = document.querySelector('#search');
const review = document.querySelector('#review');
let devices = [];

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function render() {
  list.replaceChildren();
  const matches = devices.filter(d => d.name.toLowerCase().includes(search.value.toLowerCase()));
  for (const device of matches) {
    const card = element('article', '', 'device');
    const info = element('div');
    info.append(element('h3', device.name), element('p', device.connection === 'wifi' ? `Wi-Fi · ${device.ssid}` : 'Remote · Tailscale'), element('span', 'Sample device', 'muted'));
    const controls = element('div', '', 'controls');
    controls.append(element('span', device.network === 'vpn' ? 'VPN · Netherlands' : 'Home', `badge ${device.network}`));
    const label = element('label', 'Move to');
    const select = element('select');
    select.setAttribute('aria-label', `Network for ${device.name}`);
    for (const [value, name] of [['home', 'Home'], ['vpn', 'VPN · Netherlands']]) {
      const option = element('option', name);
      option.value = value;
      select.append(option);
    }
    select.value = device.network === 'home' ? 'vpn' : 'home';
    label.append(select);
    const button = element('button', device.connection === 'wifi' ? 'Review move' : 'View steps', 'primary');
    button.type = 'button';
    button.addEventListener('click', () => showPlan(device.id, select.value, button));
    controls.append(label, button);
    card.append(info, controls);
    list.append(card);
  }
  if (!matches.length) list.append(element('p', 'No matching devices. Try another name.'));
}

async function showPlan(deviceId, target, button) {
  button.disabled = true;
  message.textContent = 'Preparing review…';
  try {
    const response = await fetch('/api/plans', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ deviceId, target }) });
    const plan = await response.json();
    if (!response.ok) throw new Error(plan.error);
    document.querySelector('#review-title').textContent = plan.title;
    document.querySelector('#review-description').textContent = plan.description;
    document.querySelector('#steps').replaceChildren(...plan.steps.map(text => element('li', text)));
    document.querySelector('#notices').replaceChildren(...plan.notices.map(text => element('p', text, 'notice')));
    review.hidden = false;
    review.focus();
    message.textContent = 'Review ready. Nothing has changed.';
  } catch (error) { message.textContent = error.message || 'Could not prepare the review. Try again.'; }
  finally { button.disabled = false; }
}

search.addEventListener('input', render);
document.querySelector('#close-review').addEventListener('click', () => { review.hidden = true; search.focus(); });

try {
  const response = await fetch('/api/devices');
  if (!response.ok) throw new Error('Could not load devices. Refresh this page to retry.');
  const data = await response.json();
  devices = data.devices;
  render();
} catch (error) { message.textContent = error.message; }
