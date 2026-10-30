const fs = require('fs');

const htmlFiles = fs.readdirSync('.').filter(f => f.endsWith('.html'));
let missingCount = 0;

htmlFiles.forEach(file => {
  const content = fs.readFileSync(file, 'utf8');
  const srcMatches = Array.from(content.matchAll(/src=["']([^"']+)["']/g)).map(m => m[1]);
  const linkMatches = Array.from(content.matchAll(/href=["']([^"']+\.css)["']/g)).map(m => m[1]);

  srcMatches.forEach(src => {
    if (!src.startsWith('http') && !src.startsWith('//') && !src.startsWith('data:')) {
      const clean = src.split('?')[0].split('#')[0];
      if (!fs.existsSync(clean)) {
        console.error('In', file, 'MISSING src:', clean);
        missingCount++;
      }
    }
  });

  linkMatches.forEach(href => {
    if (!href.startsWith('http') && !href.startsWith('//')) {
      const clean = href.split('?')[0].split('#')[0];
      if (!fs.existsSync(clean)) {
        console.error('In', file, 'MISSING css:', clean);
        missingCount++;
      }
    }
  });
});

console.log('Checked', htmlFiles.length, 'HTML files. Total missing assets:', missingCount);
