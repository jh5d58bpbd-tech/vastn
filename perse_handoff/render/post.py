"""Denoise (albedo/normal/depth guided a-trous filter) and photographic tone mapping."""
import sys
import numpy as np
import cv2

def load(pre, W, H):
    col = np.fromfile(pre + '_col.bin', np.float32).reshape(H, W, 3)
    alb = np.fromfile(pre + '_alb.bin', np.float32).reshape(H, W, 3)
    nrm = np.fromfile(pre + '_nrm.bin', np.float32).reshape(H, W, 3)
    dep = np.fromfile(pre + '_dep.bin', np.float32).reshape(H, W)
    return col, alb, nrm, dep

def shift(a, dy, dx):
    return np.roll(np.roll(a, dy, 0), dx, 1)

def atrous(col, alb, nrm, dep, iters=5, sc=0.6, sn=64.0, sd=0.02, sa=0.08):
    eps = 0.02
    irr = col / (alb + eps)
    lum = lambda x: 0.2126*x[..., 0] + 0.7152*x[..., 1] + 0.0722*x[..., 2]
    k = np.array([1/16, 1/4, 3/8, 1/4, 1/16], np.float32)
    for it in range(iters):
        step = 1 << it
        acc = np.zeros_like(irr); wsum = np.zeros(irr.shape[:2], np.float32)
        L0 = np.log1p(lum(irr))
        for i, ky in enumerate(k):
            for j, kx in enumerate(k):
                dy, dx = (i-2)*step, (j-2)*step
                ci = shift(irr, dy, dx); ni = shift(nrm, dy, dx); di = shift(dep, dy, dx); ai = shift(alb, dy, dx)
                wn = np.clip((nrm*ni).sum(-1), 0, 1) ** sn
                wd = np.exp(-np.abs(dep-di) / (sd*dep + 1e-3) * 1.0)
                wa = np.exp(-((alb-ai)**2).sum(-1) / sa**2 * 0.5)
                wc = np.exp(-np.abs(L0 - np.log1p(lum(ci))) / (sc * (1.0 + 0.5*it)))
                w = ky*kx*wn*wd*wa*wc
                acc += ci*w[..., None]; wsum += w
        irr = acc / np.maximum(wsum, 1e-8)[..., None]
    return irr * (alb + eps)

def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x*(a*x+b))/(x*(c*x+d)+e), 0, 1)

def tonemap(img, exposure, wb=(1.0, 1.0, 1.0)):
    img = img * np.array(wb, np.float32) * exposure
    # bloom
    bright = np.maximum(img - 2.0, 0)
    bl = cv2.GaussianBlur(bright, (0, 0), 3) * 0.18 + cv2.GaussianBlur(bright, (0, 0), 16) * 0.10
    img = img + bl
    out = aces(img)
    out = np.where(out <= 0.0031308, out*12.92, 1.055*np.power(np.maximum(out, 0), 1/2.4) - 0.055)
    H, W = out.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W/2)/(W/2))**2 + ((yy - H/2)/(H/2))**2)
    vig = 1 - 0.18*np.clip(r - 0.35, 0, None)**1.6
    out = out * vig[..., None]
    # gentle s-curve + slight warmth in shadows
    out = np.clip(out, 0, 1)
    out = out + 0.06*(out - out**2)*(out - 0.5)*-2 + 0.0
    # subtle grain
    rng = np.random.default_rng(1)
    out = out + rng.normal(0, 0.006, out.shape[:2])[..., None]
    return np.clip(out, 0, 1)

if __name__ == '__main__':
    pre, W, H, outp = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    exposure = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    col, alb, nrm, dep = load(pre, W, H)
    den = atrous(col, alb, nrm, dep)
    if exposure <= 0:
        L = 0.2126*den[..., 0] + 0.7152*den[..., 1] + 0.0722*den[..., 2]
        exposure = 0.15 / np.exp(np.mean(np.log(L + 1e-4)))
    print('exposure', exposure)
    img = tonemap(den, exposure, wb=(0.93, 1.0, 1.12))
    sharp = cv2.addWeighted(img, 1.25, cv2.GaussianBlur(img, (0, 0), 1.2), -0.25, 0)
    cv2.imwrite(outp, (np.clip(sharp, 0, 1)[..., ::-1]*255+0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
