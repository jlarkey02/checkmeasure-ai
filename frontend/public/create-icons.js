// Node.js script to create PWA icons
const fs = require('fs');
const { createCanvas } = require('canvas');

function createIcon(size) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');
  
  // Background
  ctx.fillStyle = '#1890ff';
  ctx.fillRect(0, 0, size, size);
  
  // Rounded corners
  const radius = size * 0.15;
  ctx.globalCompositeOperation = 'destination-in';
  ctx.beginPath();
  ctx.roundRect(0, 0, size, size, radius);
  ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  
  // Text
  ctx.fillStyle = 'white';
  ctx.font = `bold ${size * 0.25}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('CM', size / 2, size / 2 - size * 0.05);
  
  // AI text
  ctx.font = `${size * 0.15}px Arial`;
  ctx.fillText('AI', size / 2, size / 2 + size * 0.2);
  
  // Border
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
  ctx.lineWidth = size * 0.02;
  ctx.beginPath();
  ctx.roundRect(size * 0.05, size * 0.05, size * 0.9, size * 0.9, radius);
  ctx.stroke();
  
  return canvas.toBuffer('image/png');
}

// Create all icon sizes
const sizes = [48, 72, 96, 144, 192, 512];
sizes.forEach(size => {
  const buffer = createIcon(size);
  fs.writeFileSync(`icon-${size}x${size}.png`, buffer);
  console.log(`Created icon-${size}x${size}.png`);
});

console.log('All icons created successfully!');