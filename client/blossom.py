"""Zuzify's own 3D ASCII blossom renderer. No external rendering library."""
import math
import colorsys
from functools import lru_cache

RESET="\033[0m"
HUES={"blue":.59,"red":.99,"orange":.075,"yellow":.15,"purple":.76,"pink":.92,"white":0}
GLYPHS=" .,:;irsXA253hMHGS#9B&@"

@lru_cache(maxsize=1)
def petals():
    points=[]
    # Five staggered rings; asymmetrical, folded rose petals.
    for ring,count in enumerate((8,7,6,5,4)):
        for k in range(count):
            a=2*math.pi*k/count+ring*.69
            ca,sa=math.cos(a),math.sin(a)
            for i in range(29):
                u=i/28
                wave=math.sin(math.pi*u)**.72
                for j in range(23):
                    v=j/11-1
                    r=.065+u*(1.27-ring*.205)
                    t=v*(.58-ring*.078)*wave+.075*u*u*math.sin(k*2.4+ring)
                    r-=.085*v*v*u
                    z=.06+ring*.14+.20*u+.31*v*v*u+.24*u**7
                    z+=.037*math.sin(v*12+u*11+k*.7)*u
                    vein=.04*math.cos(v*22+u*8)+.035*math.sin(u*40+abs(v)*12)
                    edge=max(0,abs(v)-.65)*.5+u**10*.27
                    light=.28+.24*u+.13*math.cos(a+.8)+.17*abs(v)+vein+edge
                    points.append((r*ca-t*sa,r*sa+t*ca,z,ring,light,edge))
    for i in range(16):
        r=.18*i/15
        for j in range(52):
            a=j*2*math.pi/52
            points.append((r*math.cos(a),r*math.sin(a),.91-r*.75,5,.56+.26*math.cos(a*3+r*28),.10))
    return tuple(points)

def frame(phase,width=85,height=35,color=False,bloom=1.,palette="pink"):
    width=max(15,int(width));height=max(7,int(height))
    grid=[[None]*width for _ in range(height)]
    a=phase*.24;ca,sa=math.cos(a),math.sin(a)
    tilt=.28+.19*math.sin(phase*.42);ct,st=math.cos(tilt),math.sin(tilt)
    scale=min((width-3)/5.55,(height-3)/2.85)*max(.035,bloom)
    openings=[min(1.,max(.045,bloom*1.75-ring*.13)) for ring in range(6)]
    for x,y,z,ring,shade,edge in petals():
        opening=openings[ring];x*=opening;y*=opening
        z+=.25*(1-opening)*min(1.,math.hypot(x,y)*2)
        x,y=x*ca-y*sa,x*sa+y*ca
        y,z=y*ct-z*st,y*st+z*ct
        p=5.3/(5.3-z)
        ix=round((width-1)/2+x*scale*2*p)
        iy=round((height-1)/2-y*scale*p)
        if 0<=ix<width and 0<=iy<height:
            old=grid[iy][ix]
            if old is None or z>old[0]:
                lambert=.13*math.sin(x*2.4+phase*.55)+.10*math.cos(y*3.2-phase*.35)
                val=max(.075,min(1.,shade+lambert+.1*z))
                grid[iy][ix]=(z,val,edge,ring)
    # Subtle detached pollen specks, always behind the bloom.
    if bloom>.48:
        for j in range(23):
            a=j*2.399963+phase*.10
            rad=(.95+.34*math.sin(j*5.1+phase*.28))*scale
            ix=round((width-1)/2+math.cos(a)*rad*2.0)
            iy=round((height-1)/2+math.sin(a)*rad)
            if 0<=ix<width and 0<=iy<height and grid[iy][ix] is None:
                grid[iy][ix]=(-9,.10+.09*(1+math.sin(phase*1.4+j)),0,0)
    rows=[]
    for iy,row in enumerate(grid):
        out=[];prev=None
        for ix,p in enumerate(row):
            if p is None:
                if color and prev is not None:out.append(RESET);prev=None
                out.append(" ");continue
            z,val,edge,ring=p
            band=min(len(GLYPHS)-1,max(1,round(val*(len(GLYPHS)-1))))
            glyph=GLYPHS[band]
            if z==-9:glyph="."
            if color:
                hue=(ix/width*.85+iy/height*.45+phase*.045+ring*.025)%1 if palette=="rainbow" else HUES.get(palette,.92)
                sat=0 if palette=="white" else max(.10,.92-.64*val-.40*edge)
                rgb=tuple(round(v*255) for v in colorsys.hsv_to_rgb(hue,sat,.15+.85*val))
                # Quantization reduces terminal escape overhead.
                rgb=tuple(min(255,round(v/12)*12) for v in rgb)
                if rgb!=prev:out.append("\033[38;2;%d;%d;%dm"%rgb);prev=rgb
            out.append(glyph)
        if color:out.append(RESET)
        rows.append("".join(out))
    return "\n".join(rows)
