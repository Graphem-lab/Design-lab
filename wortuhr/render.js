// SVG -> PNG (Vorschau) und SVG -> PDF (Druckebenen) mit Chromium
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const out = path.join(__dirname, 'out');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1600 } });
  for (const n of ['preview_aus', 'preview_an', 'preview_alle', 'check_zellen']) {
    const svg = fs.readFileSync(path.join(out, n + '.svg'), 'utf8')
      .replace(/width="300(\.0)?mm" height="300(\.0)?mm"/, 'width="1600" height="1600"');
    await page.setContent(`<body style="margin:0;background:#000">${svg}</body>`);
    await page.screenshot({ path: path.join(out, n + '.png'), clip: { x: 0, y: 0, width: 1600, height: 1600 } });
  }
  for (const n of ['layer_1_farbe', 'layer_2_weiss_schwarz']) {
    const svg = fs.readFileSync(path.join(out, n + '.svg'), 'utf8');
    await page.setContent(`<style>@page{size:300mm 300mm;margin:0}body{margin:0}svg{display:block}</style>${svg}`);
    await page.pdf({ path: path.join(out, n + '.pdf'), width: '300mm', height: '300mm', printBackground: true, pageRanges: '1' });
  }
  await browser.close();
})();
