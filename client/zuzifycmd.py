import base64, datetime, getpass, hashlib, json, math, os, platform, re, shutil, sys, threading, time, uuid
from pathlib import Path
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlparse

VERSION = "1.0.0"
RELEASE_API = "https://api.github.com/repos/taithedev/ZuzifyCMD/releases/latest"
API = os.getenv("ZUZIFY_API_URL", "").strip()
START = time.monotonic()
RESET = "\033[0m"
DIM = "\033[90m"
WHITE = "\033[97m"
ACCENT = "\033[97m"
TTY = sys.stdout.isatty()
user, token = "guest", ""
updates = {}
catalog = {}
CORE = {"help":"List commands","clear":"Clear display","exit":"Exit","whoami":"Show account","logout":"Sign out","sync":"Refresh catalog","update":"Check app update","version":"Show version","time":"Local time","date":"Local date","sysinfo":"OS and CPU count","uptime":"App uptime","echo":"Print text","uuid":"Random UUID","hash":"SHA-256 text","base64":"Encode text","decode64":"Decode Base64","theme":"Change theme","flower":"Preview loader","about":"About","login":"Sign in","register":"Create account"}
ALIASES = {"commands":"help","cls":"clear","now":"time","guid":"uuid"}
ALWAYS = {"help","exit","login","register","logout","sync","update"}

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

def flower_frame(phase,width=45,height=17):
    grid=[[" "]*width for _ in range(height)]
    for i in range(900):
        t=2*math.pi*i/900
        r=0.29+0.64*abs(math.cos(3*t+phase))
        x=round((width-1)/2 + (width-2)*0.46*r*math.cos(t+phase*0.25))
        y=round((height-1)/2 + (height-2)*0.50*r*math.sin(t+phase*0.25))
        if 0<=x<width and 0<=y<height:
            grid[y][x]="@#*+."[min(4,int((math.sin(t*2+phase)+1)*2.49))]
    grid[height//2][width//2]="*"
    return "\n".join("".join(row).rstrip() for row in grid)
def animate(duration=1.3,done=None,label="Starting ZuzifyCMD"):
    if not TTY: return
    end=time.monotonic()+duration
    frame=0
    print("\033[?25l",end="")
    try:
        while (time.monotonic()<end or (done and not done.is_set())):
            width=max(15,min(45,shutil.get_terminal_size((80,24)).columns-4))
            height=max(7,min(17,shutil.get_terminal_size((80,24)).lines-5))
            clear()
            print(paint("  Z U Z I F Y  /  C M D",ACCENT))
            print(paint(flower_frame(frame*0.11,width,height),ACCENT))
            print(paint("  "+label+" "+"."*(frame%4),DIM),flush=True)
            time.sleep(0.055);frame+=1
    finally: print("\033[?25h",end="",flush=True)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
def cloud(action,**values):
    p=urlparse(API)
    if not API or p.username or p.password or p.query or p.fragment or not (p.scheme=="https" and p.hostname or p.scheme=="http" and p.hostname in ("localhost","127.0.0.1","::1")):
        raise RuntimeError("Cloud endpoint not configured; set ZUZIFY_API_URL.")
    headers={"Content-Type":"application/json","User-Agent":"ZuzifyCMD/"+VERSION}
    if token: headers["Authorization"]="Bearer "+token
    req=Request(API,data=json.dumps({"action":action,**values}).encode(),headers=headers)
    try:
        with build_opener(NoRedirect()).open(req,timeout=8) as r:
            return json.loads(r.read(1024*1024))
    except HTTPError as e:
        try: msg=json.loads(e.read(4096)).get("error","Cloud request failed")
        except Exception: msg="Cloud request failed"
        raise RuntimeError(safe(msg)) from None
    except (OSError,ValueError) as e: raise RuntimeError("Cloud unavailable.") from e

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
        assert len(flower_frame(0).splitlines())==17
        assert flower_frame(0)!=flower_frame(1)
        assert safe("hello\033[31m")=="hello[31m"
        print("Self-test passed.");return
    enable_vt()
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
    print("  login / register / guest")
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
