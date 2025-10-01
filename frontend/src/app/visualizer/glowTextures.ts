import * as THREE from 'three';

const textureCache = new Map<string, THREE.Texture>();

function createGlowTexture(color: string, innerAlpha: number, outerAlpha: number): THREE.Texture | null {
  if (typeof document === 'undefined') {
    return null;
  }

  const key = `${color}-${innerAlpha}-${outerAlpha}`;
  const cached = textureCache.get(key);
  if (cached) {
    return cached;
  }

  const size = 128;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;

  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return null;
  }

  const center = size / 2;
  const gradient = ctx.createRadialGradient(center, center, 0, center, center, center);

  const colorInstance = new THREE.Color(color);
  const r = Math.round(colorInstance.r * 255);
  const g = Math.round(colorInstance.g * 255);
  const b = Math.round(colorInstance.b * 255);

  gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${innerAlpha})`);
  gradient.addColorStop(0.5, `rgba(${r}, ${g}, ${b}, ${innerAlpha * 0.55})`);
  gradient.addColorStop(0.8, `rgba(${r}, ${g}, ${b}, ${innerAlpha * 0.25})`);
  gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, ${outerAlpha})`);

  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);

  const texture = new THREE.CanvasTexture(canvas);
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;

  textureCache.set(key, texture);
  return texture;
}

export function createGlowSpriteMaterial(color: string, innerAlpha = 0.7, outerAlpha = 0): THREE.SpriteMaterial {
  const texture = createGlowTexture(color, innerAlpha, outerAlpha);
  const material = new THREE.SpriteMaterial({
    map: texture ?? undefined,
    color: texture ? 0xffffff : color,
    transparent: true,
    depthWrite: false,
    opacity: texture ? 1.05 : innerAlpha,
  });

  return material;
}
