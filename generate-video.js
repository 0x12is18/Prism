// generate-video.js — capture the hypercar animation as a WebM video
// Usage: node generate-video.js
const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');

const HTML_FILE   = path.resolve(__dirname, 'hypercar.html');
const OUT_DIR     = __dirname;
const DURATION_MS = 36000; // 36 seconds
const WIDTH       = 1280;
const HEIGHT      = 720;

(async () => {
  console.log('Launching browser…');
  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu-sandbox',
      '--allow-file-access-from-files',
      '--autoplay-policy=no-user-gesture-required',
    ],
  });

  const context = await browser.newContext({
    viewport: { width: WIDTH, height: HEIGHT },
    recordVideo: {
      dir: OUT_DIR,
      size: { width: WIDTH, height: HEIGHT },
    },
  });

  const page = await context.newPage();

  // Silence console noise from page
  page.on('console', msg => {
    if (msg.type() === 'error') console.error('[page]', msg.text());
  });

  console.log(`Opening ${HTML_FILE} …`);
  await page.goto(`file://${HTML_FILE}`, { waitUntil: 'load' });

  // Let the animation breathe before the race starts (~6s of title+cockpit scenes)
  console.log(`Recording ${DURATION_MS/1000}s of animation…`);
  await page.waitForTimeout(DURATION_MS);

  // Save video
  const videoPath = await page.video().path();
  await context.close();
  await browser.close();

  // Rename to something friendly
  const dest = path.join(OUT_DIR, 'hypercar.webm');
  if (fs.existsSync(dest)) fs.unlinkSync(dest);
  fs.renameSync(videoPath, dest);

  console.log(`\n✓ Video saved: ${dest}`);
  console.log(`  Size: ${(fs.statSync(dest).size/1024/1024).toFixed(1)} MB`);
  console.log('\nTo convert to MP4:');
  console.log(`  ffmpeg -i hypercar.webm -c:v libx264 -crf 18 -preset slow hypercar.mp4`);
})().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
