import base64, datetime, getpass, hashlib, json, math, os, platform, re, shutil, sys, threading, time, uuid
from pathlib import Path
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlparse

VERSION = "1.1.0"
RELEASE_API = "https://api.github.com/repos/taithedev/ZuzifyCMD/releases/latest"
DSN = ""
START = time.monotonic()
RESET = "\033[0m"
DIM = "\033[90m"
WHITE = "\033[97m"
ACCENT = "\033[97m"
TTY = sys.stdout.isatty()
user, token = "guest", ""
updates = {}
catalog = {}
CORE = {"help":"List commands","clear":"Clear display","exit":"Exit","whoami":"Show account","logout":"Sign out","sync":"Refresh catalog","update":"Check app update","version":"Show version","time":"Local time","date":"Local date","sysinfo":"OS and CPU count","uptime":"App uptime","echo":"Print text","uuid":"Random UUID","hash":"SHA-256 text","base64":"Encode text","decode64":"Decode Base64","theme":"Change theme","flower":"Preview loader","about":"About","login":"Sign in","register":"Create account","connect":"Connect to Neon","disconnect":"Forget Neon connection"}
ALIASES = {"commands":"help","cls":"clear","now":"time","guid":"uuid"}
ALWAYS = {"help","exit","login","register","logout","sync","update","connect","disconnect"}

def safe(value):
    return "".join(c for c in str(value) if c.isprintable())
def paint(s,color=WHITE):
    return color+s+RESET if TTY else s
def clear():
    if TTY: print("\033[2J\033[H",end="",flush=True)
def enable_vt():
    if os.name=="nt" and TTY:
        import ctypes
        k=ctypes.windll.kernel32
        handle=k.GetStdHandle(-11)
        mode=ctypes.c_uint()
        if k.GetConsoleMode(handle,ctypes.byref(mode)):
            k.SetConsoleMode(handle,mode.value|4)

def flower_frame(phase,width=75,height=33,color=False,bloom=1.0):
    pixels=[[None]*width for _ in range(height)]
    ca,sa=math.cos(phase*.48),math.sin(phase*.48)
    tilt=.20+.18*math.sin(phase*.6)
    ct,st=math.cos(tilt),math.sin(tilt)
    def point(x,y,z,shade,kind):
        x,y=x*ca-y*sa,x*sa+y*ca
        y,z=y*ct-z*st,y*st+z*ct
        scale=min((width-2)/4.8,(height-2)/2.3)*max(.025,bloom)
        p=4.5/(4.5-z)
        ix=round((width-1)/2+x*scale*1.8*p)
        iy=round((height-1)/2-y*scale*p)
        if 0<=ix<width and 0<=iy<height and (pixels[iy][ix] is None or z>pixels[iy][ix][0]):
            pixels[iy][ix]=(z,max(0,min(1,shade)),kind)
    for layer in range(2):
        for petal in range(5):
            theta=petal*2*math.pi/5+layer*.66
            cs,sn=math.cos(theta),math.sin(theta)
            for i in range(31):
                u=i/30
                r=.13+u*(.90 if layer==0 else .57)
                spread=(.49 if layer==0 else .29)*math.sin(math.pi*u)**.7
                for j in range(25):
                    v=j/12-1
                    y=v*spread
                    z=(.18+.23*layer+.12*u+.31*v*v*u+.19*u**5)*bloom
                    z+=.045*math.sin(v*9+u*8+petal)*u
                    shade=.24+.38*u+.24*abs(v)+.13*math.cos(theta+1.1)+.10*math.sin(u*12+v*4)
                    point(r*cs-y*sn,r*sn+y*cs,z,shade,0)
    for i in range(14):
        r=.155*i/13
        for j in range(50):
            t=j*2*math.pi/50
            point(r*math.cos(t),r*math.sin(t),.58-.8*r,.45+.4*math.cos(t+1)*r/.155,1)
    chars=".:;i+ox%#@"
    rows=[]
    for row in pixels:
        line=[];prev=None
        for pix in row:
            if pix is None:
                if color and prev is not None:line.append(RESET);prev=None
                line.append(" ");continue
            _,shade,kind=pix
            band=min(9,int(shade*10));ch=chars[band]
            if kind:rgb=(min(255,130+band*14),min(255,75+band*16),45+band*8)
            else:rgb=(min(255,83+band*20),min(255,17+band*25),min(255,46+band*22))
            if color and rgb!=prev:line.append("\033[38;2;%d;%d;%dm"%rgb);prev=rgb
            line.append(ch)
        if color:line.append(RESET)
        rows.append("".join(line))
    return "\n".join(rows)

def animate(duration=3.0,done=None,label="Starting ZuzifyCMD"):
    if not TTY:return
    start=time.monotonic()
    print("\033[?25l\033[2J",end="",flush=True)
    try:
        while True:
            elapsed=time.monotonic()-start
            if elapsed>=duration and (done is None or done.is_set()):break
            if elapsed>12:break
            size=shutil.get_terminal_size((100,36))
            w=max(15,min(85,size.columns-4));h=max(7,min(35,size.lines-5))
            grow=min(1,elapsed/1.65);grow=grow*grow*(3-2*grow)
            art=flower_frame(elapsed,w,h,True,grow)
            pad=" "*max(0,(size.columns-w)//2)
            lines=["\033[2K"+pad+r for r in art.split("\n")]
            print("\033[H"+"\n".join(lines)+"\n\033[2K"+paint(("Z U Z I F Y  /  C M D").center(max(15,size.columns-1)),WHITE)+"\n\033[2K"+paint(label.center(max(15,size.columns-1)),DIM),end="",flush=True)
            time.sleep(.045)
    finally:print("\033[?25h"+RESET,end="",flush=True)

def load_connection():
    global DSN
    try:
        import keyring
        DSN=keyring.get_password("ZuzifyCMD","neon-connection") or ""
    except Exception:DSN=""

def configure_connection():
    global DSN
    candidate=getpass.getpass("  Paste your restricted Neon connection URL (hidden): ").strip()
    if not candidate:return
    old=DSN;DSN=candidate
    try:cloud("catalog")
    except Exception:
        DSN=old
        raise
    if input("  Save to Windows Credential Manager? [y/N] ").strip().lower()=="y":
        try:
            import keyring
            keyring.set_password("ZuzifyCMD","neon-connection",DSN)
        except Exception:print("  Credential storage unavailable; connection works for this session.")
    print("  "+refresh())

def forget_connection():
    global DSN,user,token
    try:
        if token:cloud("logout")
    except Exception:pass
    DSN="";user,token="guest",""
    try:
        import keyring
        keyring.delete_password("ZuzifyCMD","neon-connection")
    except Exception:pass
    print("  "+refresh())

def cloud(action,**values):
    if not DSN:raise RuntimeError("Type connect to configure your Neon connection.")
    try:
        import psycopg,certifi
        from psycopg.conninfo import conninfo_to_dict
        params=conninfo_to_dict(DSN)
        host=params.get("host","")
        if not re.fullmatch(r"[a-zA-Z0-9.-]+\.neon\.tech",host) or not params.get("user") or not params.get("dbname") or not params.get("password"):
            raise ValueError("Invalid Neon connection URL")
        if set(params)-{"host","port","user","password","dbname","sslmode","channel_binding"}:
            raise ValueError("Unsupported connection options")
        with psycopg.connect(host=host,port=params.get("port",5432),user=params["user"],password=params["password"],dbname=params["dbname"],sslmode="verify-full",sslrootcert=certifi.where(),connect_timeout=6,options="-c statement_timeout=10000") as conn:
            with conn.cursor() as cur:
                if action=="catalog":cur.execute("SELECT zuzifycmd.direct_catalog()")
                elif action in ("login","register"):cur.execute("SELECT zuzifycmd.direct_auth(%s,%s,%s)",(action,values["username"],values["password"]))
                elif action in ("me","logout"):cur.execute("SELECT zuzifycmd.direct_session(%s,%s)",(action,token))
                else:raise ValueError("Unknown cloud action")
                result=cur.fetchone()[0]
        if result.get("error"):raise RuntimeError(safe(result["error"]))
        return result
    except RuntimeError:raise
    except Exception:raise RuntimeError("Neon connection failed. Check your connection URL, restricted role grants, and network.") from None

def refresh():
    global catalog
    local={k:{"handler":k,"description":v,"category":"local"} for k,v in CORE.items()}
    local.update({k:{"handler":v,"description":"Alias for "+v,"category":"local"} for k,v in ALIASES.items()})
    try:
        rows=cloud("catalog")["commands"]
        for row in rows:
            name,handler=row.get("name",""),row.get("handler","")
            if not isinstance(name,str) or not re.fullmatch(r"[a-z0-9_]{1,32}",name) or handler not in CORE or name in ALWAYS: continue
            if row.get("enabled") is not True: local.pop(name,None);continue
            local[name]={"handler":handler,"description":safe(row.get("description",""))[:150],"category":safe(row.get("category","cloud"))[:30]}
        status="Cloud catalog synchronized"
    except Exception: status="Offline catalog"
    catalog=local
    return status

def version_tuple(s):
    m=re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)",s or "")
    return tuple(map(int,m.groups())) if m else (0,0,0)
def check_update():
    try:
        req=Request(RELEASE_API,headers={"User-Agent":"ZuzifyCMD/"+VERSION,"Accept":"application/vnd.github+json"})
        with urlopen(req,timeout=7) as r: release=json.loads(r.read(1024*1024))
        tag=release.get("tag_name","")
        if release.get("draft") or release.get("prerelease") or version_tuple(tag)<=version_tuple(VERSION):return {"status":"Up to date"}
        asset=next((a for a in release.get("assets",[]) if a.get("name")=="ZuzifyCMD.exe"),None)
        if not asset:return {"status":"New version "+safe(tag)+"; no executable available"}
        digest=asset.get("digest") or ""
        url=asset.get("browser_download_url","")
        if not re.fullmatch(r"sha256:[a-f0-9]{64}",digest) or url!="https://github.com/taithedev/ZuzifyCMD/releases/download/"+tag+"/ZuzifyCMD.exe":
            return {"status":"Update lacks a valid release digest"}
        return {"status":"Update available: "+tag,"url":url,"digest":digest[7:],"tag":tag}
    except HTTPError as e: return {"status":"No published release" if e.code==404 else "Update check unavailable"}
    except Exception: return {"status":"Update check unavailable"}
def update_background():
    updates.update(check_update())
def download_update(info):
    folder=Path.home()/"Downloads";folder.mkdir(exist_ok=True)
    target=folder/("ZuzifyCMD-"+info["tag"]+".exe")
    partial=target.with_suffix(".part")
    h=hashlib.sha256();total=0
    try:
        with urlopen(Request(info["url"],headers={"User-Agent":"ZuzifyCMD/"+VERSION}),timeout=20) as r, partial.open("xb") as out:
            if urlparse(r.geturl()).scheme!="https":raise RuntimeError("Untrusted redirect")
            while chunk:=r.read(65536):
                total+=len(chunk)
                if total>100*1024*1024:raise RuntimeError("Update exceeds size limit")
                h.update(chunk);out.write(chunk)
        if h.hexdigest()!=info["digest"]:raise RuntimeError("Release integrity check failed")
        partial.replace(target)
        print("Verified download: "+str(target))
        print("Close CMD and open the new file when ready.")
    finally:
        if partial.exists():partial.unlink()

def sign_in(action):
    global user,token
    name=input("  Username: ").strip()
    password=getpass.getpass("  Password: ")
    if action=="register" and getpass.getpass("  Confirm password: ")!=password:print("Passwords do not match.");return
    result=cloud(action,username=name,password=password)
    user=safe(result["username"]);token=result["token"]
    print("  Signed in as "+user+" / "+refresh())

def execute(handler,arg):
    global user,token,ACCENT
    if handler=="help":
        for name,row in sorted(catalog.items(),key=lambda item:(item[1]["category"],item[0])):
            print(paint("  "+name.ljust(14),ACCENT)+row["description"])
    elif handler=="clear":clear()
    elif handler=="exit":return False
    elif handler in ("login","register"):sign_in(handler)
    elif handler=="whoami":
        if token:
            try:print(cloud("me")["username"])
            except RuntimeError:print("Session not verified; sign in again.")
        else:print("guest")
    elif handler=="logout":
        try:
            if token:cloud("logout")
        finally:user,token="guest",""
        print("Signed out.")
    elif handler=="sync":print(refresh())
    elif handler=="connect":configure_connection()
    elif handler=="disconnect":forget_connection()
    elif handler=="update":
        result=check_update();print(result["status"])
        if "url" in result and input("Download verified update? [y/N] ").strip().lower()=="y":download_update(result)
    elif handler=="version":print(VERSION)
    elif handler=="time":print(datetime.datetime.now().strftime("%H:%M:%S"))
    elif handler=="date":print(datetime.date.today().isoformat())
    elif handler=="sysinfo":print(platform.system(),platform.release(),"| CPUs:",os.cpu_count())
    elif handler=="uptime":print(str(datetime.timedelta(seconds=int(time.monotonic()-START))))
    elif handler=="echo":print(safe(arg))
    elif handler=="uuid":print(uuid.uuid4())
    elif handler=="hash":print(hashlib.sha256(arg.encode()).hexdigest())
    elif handler=="base64":print(base64.b64encode(arg.encode()).decode())
    elif handler=="decode64":print(safe(base64.b64decode(arg,validate=True).decode()))
    elif handler=="theme":
        ACCENT="\033[96m" if ACCENT==WHITE else WHITE
        print(paint("Theme changed.",ACCENT))
    elif handler=="flower":animate(2);clear()
    elif handler=="about":print("ZuzifyCMD "+VERSION+" / By Zuzify")
    return True

def main():
    if "--self-test" in sys.argv:
        assert version_tuple("v1.2.3")==(1,2,3)
        assert len(flower_frame(0).splitlines())==33
        assert "\033[38;2;" in flower_frame(0,color=True)
        assert flower_frame(0)!=flower_frame(1)
        assert safe("hello\033[31m")=="hello[31m"
        print("Self-test passed.");return
    enable_vt()
    load_connection()
    done=threading.Event();status=[]
    def boot():
        try:status.append(refresh())
        finally:done.set()
    threading.Thread(target=boot,daemon=True).start()
    threading.Thread(target=update_background,daemon=True).start()
    animate(done=done,label="Syncing command catalog");done.wait()
    clear()
    print(paint("  Z U Z I F Y  /  C M D",ACCENT))
    print(paint("  v"+VERSION+" | "+(status[0] if status else "Offline")+" | help for commands",DIM))
    print("  connect / login / register / help")
    notified=False
    while True:
        if updates and not notified:print(paint("  "+updates["status"],DIM));notified=True
        try:
            raw=input(paint("\n"+user+"@zuzify",ACCENT)+" > ").strip()
            if not raw:continue
            name,_,arg=raw.partition(" ");row=catalog.get(name.lower())
            if not row:print("Unknown command. Type help.");continue
            if not execute(row["handler"],arg):break
        except (KeyboardInterrupt,EOFError):print("\nBye.");break
        except Exception as e:print("  Error: "+safe(e)[:200])
    if token:
        try:cloud("logout")
        except Exception:pass

if __name__=="__main__":main()
