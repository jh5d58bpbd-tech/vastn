"""Photographic finish for Cycles renders, matching the look of render/post2.py
(ACES tone map, bloom, vignette, grain, light sharpening).  Cycles already denoised (OIDN).

    python3 post_cycles.py in.npy out.jpg [exposure_scale=0.85]
"""
import os
import sys

import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'render'))
from post2 import tonemap  # noqa: E402

if __name__ == '__main__':
    src, outp = sys.argv[1], sys.argv[2]
    scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
    img = np.load(src).astype(np.float32)
    L = 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]
    exposure = 0.19 / np.exp(np.mean(np.log(L + 1e-4))) * scale
    print('exposure', exposure)
    out = tonemap(img, exposure, wb=(0.97, 1.0, 1.05))
    sharp = cv2.addWeighted(out, 1.15, cv2.GaussianBlur(out, (0, 0), 1.0), -0.15, 0)
    cv2.imwrite(outp, (np.clip(sharp, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
