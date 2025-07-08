// focus_box.frag
#version 120

uniform sampler2D p3d_Texture0;
uniform vec4 box;      // x, y, width, height in UV coords
varying vec2 texcoord;

// is uv inside the focus box?
bool inBox(vec2 uv, vec4 b) {
    return uv.x >= b.x && uv.x <= (b.x + b.z)
        && uv.y >= b.y && uv.y <= (b.y + b.w);
}

// 3×3 box blur using derivatives for pixel offsets
vec4 blur9(vec2 uv) {
    // uv change per screen-pixel
    vec2 fx = dFdx(uv);
    vec2 fy = dFdy(uv);

    vec4 sum = vec4(0.0);
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            sum += texture2D(p3d_Texture0, uv + fx * float(x) + fy * float(y));
        }
    }
    return sum / 16.0;
}

void main() {
    vec4 col = texture2D(p3d_Texture0, texcoord);
    
    // if outside box → blur, else keep sharp
    if (!inBox(texcoord, box)) {
        col = blur9(texcoord);

        // tint blend
        vec3 tinted = mix(col.rgb, vec3(0.2, 0.0, 0.4), 0.5);
        col.rgb = tinted;

    }

    gl_FragColor = col;
}
