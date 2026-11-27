import math
import colorsys
from functools import lru_cache

RESET="\033[0m"
HUES={"blue":.59,"red":.99,"orange":.075,"yellow":.15,"purple":.76,"pink":.92,"white":0}
GLYPHS=" .,:;irsXA253hMHGS#9B&@"

@lru_cache(maxsize=1)
def petals():
    pts=[]
    for ring,count in enumerate((10,9,8,7,6,5,4)):
        radius=1.30-ring*.157
        for k in range(count):
            theta=k*math.tau/count+ring*2.399963
            ca,sa=math.cos(theta),math.sin(theta)
            for i in range(33):
                u=i/32
                spread=(.53-ring*.055)*math.sin(math.pi*u)**.63
                twist=.24*u*u+.035*math.sin(k*3.7)
                for j in range(27):
                    v=j/13-1
                    r=.055+radius*u-.12*u*v*v
                    t=v*spread+twist*u
                    rim=.13*abs(v)**5*u+.10*u**9
                    z=.055+ring*.115+.17*u+.33*v*v*u+.30*u**6+rim
                    z+=.028*math.sin(v*16+u*13+k)*u
                    vein=.07*math.cos(v*28+u*8)*math.sin(math.pi*u)+.028*math.sin(u*45-v*9)
                    shade=.23+.25*u+.11*math.cos(theta+.65)+.13*abs(v)+vein+rim
                    pts.append((r*ca-t*sa,r*sa+t*ca,z,ring,shade,rim))
    for k in range(540):
        a=k*2.399963;r=.16*math.sqrt(k/540)
        pts.append((r*math.cos(a),r*math.sin(a),.96-r*.65,7,.65+.16*math.sin(k*1.7),.08))
    return tuple(pts)

def frame(phase,width=85,height=35,color=False,bloom=1.,palette="pink"):
    width=max(15,int(width));height=max(7,int(height))
    grid=[[None]*width for _ in range(height)]
    phase=float(phase);bloom=max(.015,min(1.,bloom))
    a=phase*.19;ca,sa=math.cos(a),math.sin(a)
    tilt=.36+.12*math.sin(phase*.35);ct,st=math.cos(tilt),math.sin(tilt)
    scale=min((width-4)/5.65,(height-3)/3.1)*(.17+.83*bloom)
    openings=[max(.035,min(1.,bloom*1.60-ring*.075)) for ring in range(8)]
    for x,y,z,ring,shade,rim in petals():
        opening=openings[ring]
        x*=opening;y*=opening;z+=.24*(1-opening)
        x,y=x*ca-y*sa,x*sa+y*ca
        y,z=y*ct-z*st,y*st+z*ct
        p=5.7/(5.7-z)
        ix=round((width-1)/2+x*scale*2.05*p)
        iy=round((height-1)/2-y*scale*p)
        if 0<=ix<width and 0<=iy<height:
            old=grid[iy][ix]
            if old is None or z>old[0]:
                light=.11*math.sin(x*3+phase*.6)+.09*math.cos(y*4-phase*.5)
                val=max(.06,min(1.,shade+light+.12*z))
                grid[iy][ix]=(z,val,rim,ring)
    if bloom>.35:
        for k in range(36):
            a=k*2.399963+phase*.09
            r=(1.12+.28*math.sin(k*4.6+phase*.4))*scale
            ix=round((width-1)/2+math.cos(a)*r*2)
            iy=round((height-1)/2+math.sin(a)*r)
            if 0<=ix<width and 0<=iy<height and grid[iy][ix] is None:
                grid[iy][ix]=(-9,.12+.07*(1+math.sin(phase*1.5+k)),0,0)
    rows=[]
    for iy,row in enumerate(grid):
        out=[];prev=None
        for ix,p in enumerate(row):
            if p is None:
                if color and prev is not None:out.append(RESET);prev=None
                out.append(" ");continue
            z,val,rim,ring=p
            glyph="." if z==-9 else GLYPHS[max(1,min(len(GLYPHS)-1,round(val*(len(GLYPHS)-1))))]
            if color:
                hue=(ix/width*.85+iy/height*.4+phase*.035+ring*.027)%1 if palette=="rainbow" else HUES.get(palette,.92)
                sat=0 if palette=="white" else max(.09,.92-.51*val-.68*rim)
                rgb=tuple(min(255,round(v*255/10)*10) for v in colorsys.hsv_to_rgb(hue,sat,.12+.88*val))
                if rgb!=prev:out.append("\033[38;2;%d;%d;%dm"%rgb);prev=rgb
            out.append(glyph)
        if color:out.append(RESET)
        rows.append("".join(out))
    return "\n".join(rows)
