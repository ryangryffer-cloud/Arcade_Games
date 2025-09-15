# simple generate_assets.py
# Requires Pillow for images.
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import wave, struct, math

ASSETS = Path(__file__).parent / "assets"
ASSETS.mkdir(exist_ok=True)

def make_bubble(p):
    size = 64
    img = Image.new("RGBA",(size,size),(0,0,0,0))
    d = ImageDraw.Draw(img)
    d.ellipse((3,3,size-4,size-4), outline=(30,150,255,220), width=3)
    inner = Image.new("RGBA",(size,size),(0,0,0,0))
    idraw = ImageDraw.Draw(inner)
    idraw.ellipse((6,8,size-8,size-6), fill=(180,220,255,90))
    inner = inner.filter(ImageFilter.GaussianBlur(radius=1.2))
    img = Image.alpha_composite(img, inner)
    d.ellipse((12,10,26,22), fill=(255,255,255,200))
    img.save(p)

def make_background(p):
    w,h = 1080,1920
    base = Image.new("RGB",(w,h),(135,206,250))
    px = base.load()
    top = (135,206,250)
    bottom = (60,120,180)
    for y in range(h):
        t = y / (h-1)
        r = int(top[0]*(1-t) + bottom[0]*t)
        g = int(top[1]*(1-t) + bottom[1]*t)
        b = int(top[2]*(1-t) + bottom[2]*t)
        for x in range(w):
            px[x,y] = (r,g,b)
    base.save(p)

def make_pop(p):
    sr = 44100
    dur = 0.15
    n = int(sr*dur)
    frames = bytearray()
    for i in range(n):
        t = i / sr
        freq = 500 + (1200-500)*(i/n)
        env = math.exp(-8.0*(i/n))
        sample = 0.8*env*math.sin(2*math.pi*freq*t)
        noise = 0.05*env*math.sin(2*math.pi*3500*t)
        val = int(max(-1,min(1,sample+noise))*32767)
        frames.extend(struct.pack('<h',val))
    with wave.open(str(p),'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)

if __name__ == '__main__':
    make_bubble(ASSETS/'bubble.png')
    make_background(ASSETS/'background.png')
    make_pop(ASSETS/'pop.wav')
    print('Assets generated in', ASSETS)
