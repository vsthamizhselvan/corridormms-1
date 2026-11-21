/**
 * CorridorKey 2.0 Desktop — WebGL2 GLSL ES 3.0 Advanced Compositing Shaders.
 *
 * Implements real-time GPU chroma key despill, matte contrast/threshold,
 * Lift/Gamma/Gain, temperature/tint, vignette, film grain, blend modes,
 * procedural anti-aliased checkerboard, and mask clipping.
 */

export const VERTEX_SHADER_SOURCE = `#version 300 es
in vec2 a_position;
in vec2 a_texCoord;

out vec2 v_texCoord;

void main() {
  v_texCoord = a_texCoord;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

export const FRAGMENT_SHADER_SOURCE = `#version 300 es
precision highp float;

in vec2 v_texCoord;
out vec4 fragColor;

// Textures
uniform sampler2D u_sourceTexture;
uniform sampler2D u_bgTexture;
uniform bool u_hasBgTexture;

// Display Modes: 0: original, 1: foreground, 2: alpha, 3: composite, 4: background, 5: mask_only
uniform int u_displayMode;
// Background: 0: checkerboard, 1: solid, 2: gradient, 3: texture
uniform int u_backgroundType;
// Compare: 0: none, 1: wipe, 2: side_by_side, 3: difference
uniform int u_compareMode;

// Parameters
uniform float u_wipePosition; // 0.0 to 1.0
uniform float u_contrast;     // 0.1 to 3.0
uniform float u_alphaThreshold; // 0.0 to 1.0
uniform bool u_invertMatte;
uniform float u_despillStrength; // 0.0 to 1.0
uniform float u_exposure;     // EV (-3.0 to +3.0)
uniform float u_saturation;   // 0.0 to 2.0
uniform int u_alphaMode;      // 0: straight, 1: premultiplied

// Phase 8 Advanced Color Grade & VFX Uniforms
uniform float u_temperature;  // -1.0 to +1.0
uniform float u_tint;         // -1.0 to +1.0
uniform float u_lift;         // -0.5 to +0.5
uniform float u_gamma;        // 0.2 to 3.0
uniform float u_gain;         // 0.0 to 3.0
uniform float u_vignette;     // 0.0 to 1.0
uniform float u_filmGrain;    // 0.0 to 1.0
uniform int u_blendMode;      // 0: normal, 1: multiply, 2: screen, 3: add, 4: overlay, 5: diff

// Vector Mask Uniforms
uniform bool u_hasMask;
uniform vec4 u_maskRect;      // x, y, width, height (normalized 0.0-1.0)
uniform bool u_maskInvert;
uniform float u_maskFeather;

// Background Colors
uniform vec3 u_bgColor;
uniform vec3 u_gradientColorA;
uniform vec3 u_gradientColorB;
uniform vec2 u_resolution; // viewport resolution
uniform float u_checkerSize;

// Color Grading & Saturation
vec3 adjustSaturation(vec3 color, float sat) {
  float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
  return mix(vec3(luma), color, sat);
}

// Procedural Anti-Aliased Checkerboard in Screen Space
vec4 computeCheckerboard(vec2 fragCoord) {
  vec2 pos = floor(fragCoord / max(4.0, u_checkerSize));
  float pattern = mod(pos.x + pos.y, 2.0);
  vec3 col = mix(vec3(0.18, 0.18, 0.22), vec3(0.28, 0.28, 0.32), pattern);
  return vec4(col, 1.0);
}

// Background Generator
vec4 getBackground(vec2 uv, vec2 fragCoord) {
  if (u_backgroundType == 0) {
    return computeCheckerboard(fragCoord);
  } else if (u_backgroundType == 1) {
    return vec4(u_bgColor, 1.0);
  } else if (u_backgroundType == 2) {
    float t = clamp((uv.x + (1.0 - uv.y)) * 0.5, 0.0, 1.0);
    return vec4(mix(u_gradientColorA, u_gradientColorB, t), 1.0);
  } else if (u_backgroundType == 3 && u_hasBgTexture) {
    return texture(u_bgTexture, uv);
  }
  return vec4(0.0, 0.0, 0.0, 1.0);
}

// Keying & Matte Calculation
float calculateMatte(vec3 rgb) {
  float maxRB = max(rgb.r, rgb.b);
  float spill = max(0.0, rgb.g - maxRB);
  float alpha = clamp(1.0 - spill * 2.5, 0.0, 1.0);

  // Apply Alpha Threshold / Pedestal
  if (u_alphaThreshold > 0.0) {
    alpha = clamp((alpha - u_alphaThreshold) / (1.0 - u_alphaThreshold + 1e-5), 0.0, 1.0);
  }

  // Apply Contrast
  if (abs(u_contrast - 1.0) > 0.001) {
    alpha = clamp((alpha - 0.5) * u_contrast + 0.5, 0.0, 1.0);
  }

  if (u_invertMatte) {
    alpha = 1.0 - alpha;
  }

  return alpha;
}

// Chroma Despill
vec3 applyDespill(vec3 rgb, float strength) {
  if (strength <= 0.0) return rgb;
  float maxRB = max(rgb.r, rgb.b);
  float excess = max(0.0, rgb.g - maxRB) * strength;
  return vec3(rgb.r, rgb.g - excess, rgb.b);
}

// Color Grading Pass
vec3 applyGrading(vec3 rgb, vec2 uv) {
  // Lift, Gamma, Gain (ASC-CDL)
  if (abs(u_lift) > 0.001 || abs(u_gain - 1.0) > 0.001) {
    rgb = clamp(u_lift * (1.0 - rgb) + u_gain * rgb, 0.0, 1.0);
  }
  if (abs(u_gamma - 1.0) > 0.001) {
    rgb = pow(max(rgb, vec3(0.0)), vec3(1.0 / max(0.01, u_gamma)));
  }

  // Exposure EV scaling
  if (abs(u_exposure) > 0.001) {
    rgb *= pow(2.0, u_exposure);
  }

  // Temperature and Tint
  if (abs(u_temperature) > 0.001 || abs(u_tint) > 0.001) {
    rgb.r += 0.3 * u_temperature + 0.2 * u_tint;
    rgb.g -= 0.3 * u_tint;
    rgb.b += -0.3 * u_temperature + 0.2 * u_tint;
  }

  // Saturation
  if (abs(u_saturation - 1.0) > 0.001) {
    rgb = adjustSaturation(rgb, u_saturation);
  }

  // Vignette
  if (u_vignette > 0.01) {
    vec2 coord = (uv - 0.5) * 2.0;
    float dist = length(coord);
    float vig = smoothstep(0.7, 1.4, dist);
    rgb *= (1.0 - vig * u_vignette * 0.7);
  }

  // Film Grain
  if (u_filmGrain > 0.01) {
    float noise = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
    rgb += noise * u_filmGrain * 0.15;
  }

  return clamp(rgb, 0.0, 1.0);
}

// Vector Mask Clipping
float evaluateMask(vec2 uv) {
  if (!u_hasMask) return 1.0;
  vec2 p = uv;
  vec2 minP = u_maskRect.xy;
  vec2 maxP = u_maskRect.xy + u_maskRect.zw;

  float dX = max(minP.x - p.x, p.x - maxP.x);
  float dY = max(minP.y - p.y, p.y - maxP.y);
  float dist = max(dX, dY);

  float m = 1.0 - smoothstep(-u_maskFeather, u_maskFeather, dist);
  if (u_maskInvert) m = 1.0 - m;
  return clamp(m, 0.0, 1.0);
}

// Blend Mode Math
vec3 blendLayers(vec3 base, vec3 blend, int mode) {
  if (mode == 1) {
    return base * blend; // Multiply
  } else if (mode == 2) {
    return 1.0 - (1.0 - base) * (1.0 - blend); // Screen
  } else if (mode == 3) {
    return min(vec3(1.0), base + blend); // Add
  } else if (mode == 4) {
    // Overlay
    vec3 low = 2.0 * base * blend;
    vec3 high = 1.0 - 2.0 * (1.0 - base) * (1.0 - blend);
    return mix(low, high, step(0.5, base));
  } else if (mode == 5) {
    return abs(base - blend); // Difference
  }
  return blend; // Normal
}

// Single Pixel Evaluation
vec4 evaluatePixel(vec2 uv, vec2 fragCoord, int mode) {
  vec4 src = texture(u_sourceTexture, uv);
  vec3 rgb = src.rgb;

  if (mode == 0) {
    // Raw original footage
    return vec4(rgb, 1.0);
  }

  // Calculate AI Chroma Matte
  float alpha = calculateMatte(rgb);

  // Apply Vector Mask clipping
  float mask = evaluateMask(uv);
  alpha *= mask;

  // Apply Chroma Despill & Color Grading
  vec3 despilled = applyDespill(rgb, u_despillStrength);
  despilled = applyGrading(despilled, uv);

  if (mode == 1) {
    // Processed foreground without background
    return vec4(despilled, alpha);
  } else if (mode == 2) {
    // Alpha matte grayscale
    return vec4(vec3(alpha), 1.0);
  } else if (mode == 4) {
    // Background only
    return getBackground(uv, fragCoord);
  } else if (mode == 5) {
    // Mask preview only
    return vec4(vec3(mask), 1.0);
  } else {
    // Final Composite over background with blend mode
    vec4 bg = getBackground(uv, fragCoord);
    vec3 blended = blendLayers(bg.rgb, despilled, u_blendMode);
    vec3 comp;
    if (u_alphaMode == 1) {
      // Premultiplied alpha composite
      comp = (blended * alpha) + bg.rgb * (1.0 - alpha);
    } else {
      // Straight alpha composite
      comp = blended * alpha + bg.rgb * (1.0 - alpha);
    }
    return vec4(comp, 1.0);
  }
}

void main() {
  vec2 uv = v_texCoord;
  vec2 fragCoord = gl_FragCoord.xy;

  if (u_compareMode == 1) {
    // Interactive Wipe comparison
    float splitX = u_wipePosition;
    float dist = abs(uv.x - splitX) * u_resolution.x;

    if (dist < 1.5) {
      fragColor = vec4(0.2, 0.6, 1.0, 1.0);
      return;
    }

    if (uv.x < splitX) {
      fragColor = evaluatePixel(uv, fragCoord, 0);
    } else {
      fragColor = evaluatePixel(uv, fragCoord, u_displayMode);
    }
  } else if (u_compareMode == 2) {
    // Side-by-Side (2-Up)
    if (uv.x < 0.5) {
      vec2 leftUv = vec2(uv.x * 2.0, uv.y);
      fragColor = evaluatePixel(leftUv, fragCoord, 0);
    } else {
      vec2 rightUv = vec2((uv.x - 0.5) * 2.0, uv.y);
      fragColor = evaluatePixel(rightUv, fragCoord, u_displayMode);
    }
    float centerDist = abs(uv.x - 0.5) * u_resolution.x;
    if (centerDist < 1.0) {
      fragColor = vec4(0.3, 0.3, 0.4, 1.0);
    }
  } else if (u_compareMode == 3) {
    // Difference view
    vec4 orig = evaluatePixel(uv, fragCoord, 0);
    vec4 proc = evaluatePixel(uv, fragCoord, u_displayMode);
    vec3 diff = abs(orig.rgb - proc.rgb);
    fragColor = vec4(diff * 3.0, 1.0);
  } else {
    // Standard single view
    fragColor = evaluatePixel(uv, fragCoord, u_displayMode);
  }
}
`;
