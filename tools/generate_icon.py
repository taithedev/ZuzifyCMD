"""Generate an original multi-resolution Windows icon with supersampling."""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import math
S=1024
im=Image.new("RGBA",(S,S),(0,0,0,0))
d=ImageDraw.Draw(im)
d.rounded_rectangle((48,48,976,976),radius=230,fill=(8,11,20,255),outline=(77,92,133,255),width=12)
glow=Image.new("RGBA",(S,S));g=ImageDraw.Draw(glow)
for j in range(8):
    t=2*math.pi*j/8
    x=512+205*math.cos(t);y=440+205*math.sin(t)
    g.ellipse((x-150,y-150,x+150,y+150),fill=(120,65,255,160))
im=Image.alpha_composite(im,glow.filter(ImageFilter.GaussianBlur(65)))
d=ImageDraw.Draw(im)
for ring,n in [(0,8),(1,5)]:
    for j in range(n):
        theta=2*math.pi*j/n+ring*.65
        poly=[]
        for i in range(81):
            t=2*math.pi*i/80
            x=(172-ring*55)+(191-ring*71)*math.cos(t);y=(89-ring*30)*math.sin(t)
            poly.append((512+x*math.cos(theta)-y*math.sin(theta),440+x*math.sin(theta)+y*math.cos(theta)))
        d.polygon(poly,fill=(133+ring*60,90+ring*64,249,255),outline=(230,218,255,255),width=5)
d.ellipse((464,392,560,488),fill=(255,255,255,255))
d.line([(302,729),(392,802),(302,875)],fill=(235,242,255),width=36,joint="curve")
d.rounded_rectangle((458,853,709,880),radius=10,fill=(235,242,255))
out=Path(__file__).resolve().parents[1]/"assets"/"zuzifycmd.ico"
out.parent.mkdir(exist_ok=True)
im.save(out,format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(out)
