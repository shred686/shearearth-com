import { spawn } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';

const chrome = process.env.CHROME_BIN ?? 'google-chrome';
const outputDir = new URL('../source/live-site/screenshots/', import.meta.url);
const pages = [
  ['home', 'https://www.shearearth.com/'],
  ['about', 'https://www.shearearth.com/about/'],
  ['services', 'https://www.shearearth.com/services/'],
  ['contact', 'https://www.shearearth.com/contact/'],
  ['image-gallery', 'https://www.shearearth.com/image-gallery/'],
];
const port = 9229;
const profile = '/tmp/shearearth-live-site-chrome';

const browser = spawn(chrome, [
  '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
  '--window-size=1440,900', `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, 'about:blank',
], { stdio: 'ignore' });

function send(socket, id, method, params = {}) {
  socket.send(JSON.stringify({ id, method, params }));
}

try {
  await mkdir(outputDir, { recursive: true });
  let targets;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      if (targets.length) break;
    } catch { /* Chrome is still starting. */ }
    await delay(250);
  }
  if (!targets?.length) throw new Error('Chrome remote debugging did not start.');

  const socket = new WebSocket(targets.find((target) => target.type === 'page').webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  let nextId = 1;
  const request = (method, params) => new Promise((resolve, reject) => {
    const id = nextId++;
    const receive = ({ data }) => {
      const message = JSON.parse(data);
      if (message.id !== id) return;
      socket.removeEventListener('message', receive);
      message.error ? reject(new Error(message.error.message)) : resolve(message.result);
    };
    socket.addEventListener('message', receive);
    send(socket, id, method, params);
  });

  await request('Page.enable');
  await request('Emulation.setDeviceMetricsOverride', {
    width: 1440, height: 900, deviceScaleFactor: 1, mobile: false,
  });
  for (const [name, url] of pages) {
    await request('Page.navigate', { url });
    await delay(3000);
    await request('Runtime.evaluate', {
      expression: 'document.fonts ? document.fonts.ready : Promise.resolve()',
      awaitPromise: true,
    });
    const { data } = await request('Page.captureScreenshot', {
      format: 'png', captureBeyondViewport: true,
    });
    await writeFile(new URL(`${name}.png`, outputDir), Buffer.from(data, 'base64'));
  }
  socket.close();
} finally {
  browser.kill();
}
