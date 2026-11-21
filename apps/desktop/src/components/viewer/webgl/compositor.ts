/**
 * CorridorKey 2.0 Desktop — WebGL2 GPU Compositor.
 */

import { VERTEX_SHADER_SOURCE, FRAGMENT_SHADER_SOURCE } from "./shaders";

export interface CompositorParams {
  displayMode: "original" | "foreground" | "alpha" | "composite" | "background" | "mask_only";
  backgroundType: "checkerboard" | "black" | "white" | "custom_color" | "gradient" | "image" | "video";
  compareMode: "none" | "wipe" | "side_by_side" | "difference";
  wipePosition: number; // 0.0 to 1.0
  contrast: number; // 0.1 to 3.0
  alphaThreshold: number; // 0.0 to 1.0
  invertMatte: boolean;
  despillStrength: number; // 0.0 to 1.0
  exposure: number; // -3.0 to +3.0 EV
  saturation: number; // 0.0 to 2.0
  alphaMode: "straight" | "premultiplied";
  backgroundColor: string; // hex string e.g. '#1e293b'
  gradientColorA: string;
  gradientColorB: string;
  checkerboardSize: number;

  // Phase 8 VFX Extensions
  temperature?: number;
  tint?: number;
  lift?: number;
  gamma?: number;
  gain?: number;
  vignette?: number;
  filmGrain?: number;
  blendMode?: "normal" | "multiply" | "screen" | "add" | "overlay" | "difference";
  hasMask?: boolean;
  maskRect?: [number, number, number, number];
  maskInvert?: boolean;
  maskFeather?: number;
}

export class WebGLCompositor {
  private gl: WebGL2RenderingContext;
  private program: WebGLProgram;
  private vao: WebGLVertexArrayObject | null = null;
  private sourceTexture: WebGLTexture | null = null;
  private bgTexture: WebGLTexture | null = null;
  private uniforms: Record<string, WebGLUniformLocation | null> = {};
  private hasSource = false;
  private hasBg = false;
  private sourceWidth = 0;
  private sourceHeight = 0;
  private bgWidth = 0;
  private bgHeight = 0;

  constructor(canvas: HTMLCanvasElement) {
    const gl = canvas.getContext("webgl2", {
      alpha: false,
      antialias: false,
      depth: false,
      stencil: false,
      premultipliedAlpha: false,
      preserveDrawingBuffer: false,
      powerPreference: "high-performance",
    });

    if (!gl) {
      throw new Error("WebGL2 context could not be initialized.");
    }
    this.gl = gl;
    this.program = this.initProgram();
    this.initGeometry();
    this.initTextures();
    this.cacheUniforms();
  }

  private initProgram(): WebGLProgram {
    const gl = this.gl;
    const vs = gl.createShader(gl.VERTEX_SHADER)!;
    gl.shaderSource(vs, VERTEX_SHADER_SOURCE);
    gl.compileShader(vs);
    if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
      const err = gl.getShaderInfoLog(vs);
      gl.deleteShader(vs);
      throw new Error(`Vertex shader compilation failed: ${err}`);
    }

    const fs = gl.createShader(gl.FRAGMENT_SHADER)!;
    gl.shaderSource(fs, FRAGMENT_SHADER_SOURCE);
    gl.compileShader(fs);
    if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
      const err = gl.getShaderInfoLog(fs);
      gl.deleteShader(fs);
      gl.deleteShader(vs);
      throw new Error(`Fragment shader compilation failed: ${err}`);
    }

    const prog = gl.createProgram()!;
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);

    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      const err = gl.getProgramInfoLog(prog);
      gl.deleteProgram(prog);
      throw new Error(`Shader program linking failed: ${err}`);
    }

    gl.deleteShader(vs);
    gl.deleteShader(fs);
    return prog;
  }

  private initGeometry() {
    const gl = this.gl;
    this.vao = gl.createVertexArray();
    gl.bindVertexArray(this.vao);

    // Quad covering [-1, 1] clip space and [0, 1] UV space (Y-flipped for video)
    const vertices = new Float32Array([
      // pos x, y   uv u, v
      -1.0, -1.0, 0.0, 1.0,
       1.0, -1.0, 1.0, 1.0,
      -1.0,  1.0, 0.0, 0.0,
      -1.0,  1.0, 0.0, 0.0,
       1.0, -1.0, 1.0, 1.0,
       1.0,  1.0, 1.0, 0.0,
    ]);

    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    // Attribute 0: Position vec2
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 4 * Float32Array.BYTES_PER_ELEMENT, 0);

    // Attribute 1: UV TexCoord vec2
    gl.enableVertexAttribArray(1);
    gl.vertexAttribPointer(
      1,
      2,
      gl.FLOAT,
      false,
      4 * Float32Array.BYTES_PER_ELEMENT,
      2 * Float32Array.BYTES_PER_ELEMENT
    );

    gl.bindVertexArray(null);
  }

  private initTextures() {
    const gl = this.gl;
    this.sourceTexture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.sourceTexture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

    this.bgTexture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.bgTexture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

    gl.bindTexture(gl.TEXTURE_2D, null);
  }

  private cacheUniforms() {
    const gl = this.gl;
    const names = [
      "u_sourceTexture",
      "u_bgTexture",
      "u_hasBgTexture",
      "u_displayMode",
      "u_backgroundType",
      "u_compareMode",
      "u_wipePosition",
      "u_contrast",
      "u_alphaThreshold",
      "u_invertMatte",
      "u_despillStrength",
      "u_exposure",
      "u_saturation",
      "u_alphaMode",
      "u_bgColor",
      "u_gradientColorA",
      "u_gradientColorB",
      "u_resolution",
      "u_checkerSize",
      // Phase 8 extensions
      "u_temperature",
      "u_tint",
      "u_lift",
      "u_gamma",
      "u_gain",
      "u_vignette",
      "u_filmGrain",
      "u_blendMode",
      "u_hasMask",
      "u_maskRect",
      "u_maskInvert",
      "u_maskFeather",
    ];

    for (const name of names) {
      this.uniforms[name] = gl.getUniformLocation(this.program, name);
    }
  }

  private hexToRgb(hex: string): [number, number, number] {
    const clean = hex.replace("#", "");
    if (clean.length === 3) {
      const r = parseInt(clean[0] + clean[0], 16) / 255;
      const g = parseInt(clean[1] + clean[1], 16) / 255;
      const b = parseInt(clean[2] + clean[2], 16) / 255;
      return [r, g, b];
    }
    const num = parseInt(clean, 16);
    return [
      ((num >> 16) & 255) / 255,
      ((num >> 8) & 255) / 255,
      (num & 255) / 255,
    ];
  }

  public uploadSourceFrame(source: HTMLVideoElement | HTMLImageElement | HTMLCanvasElement) {
    const gl = this.gl;
    const w = "videoWidth" in source ? source.videoWidth : source.width;
    const h = "videoHeight" in source ? source.videoHeight : source.height;
    if (w === 0 || h === 0) return;

    gl.bindTexture(gl.TEXTURE_2D, this.sourceTexture);
    if (w === this.sourceWidth && h === this.sourceHeight) {
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, gl.RGBA, gl.UNSIGNED_BYTE, source);
    } else {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
      this.sourceWidth = w;
      this.sourceHeight = h;
    }
    this.hasSource = true;
  }

  public uploadBackground(image: HTMLImageElement | HTMLVideoElement | HTMLCanvasElement) {
    const gl = this.gl;
    const w = "videoWidth" in image ? image.videoWidth : image.width;
    const h = "videoHeight" in image ? image.videoHeight : image.height;
    if (w === 0 || h === 0) return;

    gl.bindTexture(gl.TEXTURE_2D, this.bgTexture);
    if (w === this.bgWidth && h === this.bgHeight) {
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, gl.RGBA, gl.UNSIGNED_BYTE, image);
    } else {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
      this.bgWidth = w;
      this.bgHeight = h;
    }
    this.hasBg = true;
  }

  public clearBackground() {
    this.hasBg = false;
  }

  public render(params: CompositorParams) {
    const gl = this.gl;
    if (!this.hasSource) return;

    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
    gl.clearColor(0.08, 0.08, 0.1, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    gl.useProgram(this.program);

    // Bind textures
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.sourceTexture);
    gl.uniform1i(this.uniforms["u_sourceTexture"], 0);

    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, this.bgTexture);
    gl.uniform1i(this.uniforms["u_bgTexture"], 1);
    gl.uniform1i(this.uniforms["u_hasBgTexture"], this.hasBg ? 1 : 0);

    // Display mode
    const modeMap: Record<string, number> = {
      original: 0,
      foreground: 1,
      alpha: 2,
      composite: 3,
      background: 4,
      mask_only: 5,
    };
    gl.uniform1i(this.uniforms["u_displayMode"], modeMap[params.displayMode] ?? 3);

    // Background type
    let bgType = 0;
    if (params.backgroundType === "black") {
      bgType = 1;
      gl.uniform3f(this.uniforms["u_bgColor"], 0.0, 0.0, 0.0);
    } else if (params.backgroundType === "white") {
      bgType = 1;
      gl.uniform3f(this.uniforms["u_bgColor"], 1.0, 1.0, 1.0);
    } else if (params.backgroundType === "custom_color") {
      bgType = 1;
      const [r, g, b] = this.hexToRgb(params.backgroundColor);
      gl.uniform3f(this.uniforms["u_bgColor"], r, g, b);
    } else if (params.backgroundType === "gradient") {
      bgType = 2;
      const [ar, ag, ab] = this.hexToRgb(params.gradientColorA);
      const [br, bg, bb] = this.hexToRgb(params.gradientColorB);
      gl.uniform3f(this.uniforms["u_gradientColorA"], ar, ag, ab);
      gl.uniform3f(this.uniforms["u_gradientColorB"], br, bg, bb);
    } else if (params.backgroundType === "image" || params.backgroundType === "video") {
      bgType = 3;
    } else {
      bgType = 0; // checkerboard
    }
    gl.uniform1i(this.uniforms["u_backgroundType"], bgType);

    // Compare mode
    const compareMap: Record<string, number> = {
      none: 0,
      wipe: 1,
      side_by_side: 2,
      difference: 3,
    };
    gl.uniform1i(this.uniforms["u_compareMode"], compareMap[params.compareMode] ?? 0);
    gl.uniform1f(this.uniforms["u_wipePosition"], params.wipePosition);

    // Matte & grade adjustments
    gl.uniform1f(this.uniforms["u_contrast"], params.contrast);
    gl.uniform1f(this.uniforms["u_alphaThreshold"], params.alphaThreshold);
    gl.uniform1i(this.uniforms["u_invertMatte"], params.invertMatte ? 1 : 0);
    gl.uniform1f(this.uniforms["u_despillStrength"], params.despillStrength);
    gl.uniform1f(this.uniforms["u_exposure"], params.exposure);
    gl.uniform1f(this.uniforms["u_saturation"], params.saturation);
    gl.uniform1i(this.uniforms["u_alphaMode"], params.alphaMode === "premultiplied" ? 1 : 0);

    // Resolution & checker size
    gl.uniform2f(this.uniforms["u_resolution"], gl.canvas.width, gl.canvas.height);
    gl.uniform1f(this.uniforms["u_checkerSize"], params.checkerboardSize);

    // Phase 8 Advanced Color Grade & VFX uniforms
    gl.uniform1f(this.uniforms["u_temperature"], params.temperature ?? 0.0);
    gl.uniform1f(this.uniforms["u_tint"], params.tint ?? 0.0);
    gl.uniform1f(this.uniforms["u_lift"], params.lift ?? 0.0);
    gl.uniform1f(this.uniforms["u_gamma"], params.gamma ?? 1.0);
    gl.uniform1f(this.uniforms["u_gain"], params.gain ?? 1.0);
    gl.uniform1f(this.uniforms["u_vignette"], params.vignette ?? 0.0);
    gl.uniform1f(this.uniforms["u_filmGrain"], params.filmGrain ?? 0.0);

    const blendMap: Record<string, number> = {
      normal: 0,
      multiply: 1,
      screen: 2,
      add: 3,
      overlay: 4,
      difference: 5,
    };
    gl.uniform1i(this.uniforms["u_blendMode"], blendMap[params.blendMode ?? "normal"] ?? 0);

    // Vector Mask Uniforms
    gl.uniform1i(this.uniforms["u_hasMask"], params.hasMask ? 1 : 0);
    const rect = params.maskRect ?? [0.2, 0.2, 0.6, 0.6];
    gl.uniform4f(this.uniforms["u_maskRect"], rect[0], rect[1], rect[2], rect[3]);
    gl.uniform1i(this.uniforms["u_maskInvert"], params.maskInvert ? 1 : 0);
    gl.uniform1f(this.uniforms["u_maskFeather"], params.maskFeather ?? 0.02);

    // Draw
    gl.bindVertexArray(this.vao);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    gl.bindVertexArray(null);
  }

  public dispose() {
    const gl = this.gl;
    if (this.sourceTexture) gl.deleteTexture(this.sourceTexture);
    if (this.bgTexture) gl.deleteTexture(this.bgTexture);
    if (this.vao) gl.deleteVertexArray(this.vao);
    if (this.program) gl.deleteProgram(this.program);
  }
}
