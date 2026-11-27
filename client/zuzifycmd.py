import secrets, random, colorsys, base64, datetime, getpass, hashlib, json, math, os, platform, re, shutil, sys, threading, time, uuid
from pathlib import Path
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlparse

VERSION = "1.2.0.1a"
RELEASE_API = "https://api.github.com/repos/taithedev/ZuzifyCMD/releases/latest"
API = "https://zuzifycmd.vercel.app/api/cmd"
INSTALL = ""
PROFILE = {}
BOOT = {}
STOP = threading.Event()
RARITIES = (
    ("blue","Common",30.0),("red","Common",25.0),("orange","Common",20.0),
    ("white","Uncommon",12.0),("yellow","Rare",7.0),("purple","Epic",4.0),
    ("pink","Legendary",1.8),("rainbow","Mythic",0.2),
)
PALETTE, RARITY, CHANCE = random.SystemRandom().choices(RARITIES,weights=[r[2] for r in RARITIES],k=1)[0]
STARTUP_FLOWER = (PALETTE,RARITY,CHANCE)

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

def flower_frame(phase,width=85,height=35,color=False,bloom=1.0):
    pixels=[[None]*width for _ in range(height)]
    ca,sa=math.cos(phase*.27),math.sin(phase*.27)
    tilt=.36+.18*math.sin(phase*.45);ct,st=math.cos(tilt),math.sin(tilt)
    def point(x,y,z,shade):
        x,y=x*ca-y*sa,x*sa+y*ca
        y,z=y*ct-z*st,y*st+z*ct
        scale=min((width-2)/4.7,(height-2)/2.7)*max(.025,bloom)
        p=5/(5-z)
        ix=round((width-1)/2+x*scale*2*p);iy=round((height-1)/2-y*scale*p)
        if 0<=ix<width and 0<=iy<height and (pixels[iy][ix] is None or z>pixels[iy][ix][0]):
            pixels[iy][ix]=(z,max(0,min(1,shade)))
    for layer,count in enumerate((7,6,5,4)):
        opening=min(1,max(.04,bloom*1.55-layer*.12))
        for petal in range(count):
            theta=petal*2*math.pi/count+layer*.8;cs,sn=math.cos(theta),math.sin(theta)
            for i in range(29):
                u=i/28
                r=.09+u*(1.14-layer*.21)*opening
                spread=(.51-layer*.075)*math.sin(math.pi*u)**.65*opening
                for j in range(21):
                    v=j/10-1;y=v*spread
                    z=.10+layer*.16+.25*u+.33*v*v*u+.28*u**6+(1-opening)*u*.55
                    z+=.035*math.sin(v*13+u*14+petal)*u
                    shade=.24+.34*u+.22*abs(v)+.16*math.cos(theta+phase*.27+1.0)+.11*math.sin(u*17+v*8)
                    point(r*cs-y*sn,r*sn+y*cs,z,shade)
    for i in range(12):
        r=.13*i/11
        for j in range(40):
            t=j*2*math.pi/40
            point(r*math.cos(t),r*math.sin(t),.84-r*.9,.5+.35*math.sin(t*3+phase))
    chars=".:;i1l+ox%#@";hues={"blue":.59,"red":.99,"orange":.075,"yellow":.15,"purple":.76,"pink":.92,"white":0}
    rows=[]
    for iy,row in enumerate(pixels):
        line=[];prev=None
        for ix,pix in enumerate(row):
            if pix is None:
                if color and prev is not None:line.append(RESET);prev=None
                line.append(" ");continue
            _,s=pix;band=min(11,int(s*12));ch=chars[band]
            hue=(ix/max(width,1)+iy/max(height,1)*.4+phase*.06)%1 if PALETTE=="rainbow" else hues.get(PALETTE,.92)
            rgb=tuple(round(v*255) for v in colorsys.hsv_to_rgb(hue,0 if PALETTE=="white" else .88-.70*s,.24+.76*s))
            if color and rgb!=prev:line.append("\033[38;2;%d;%d;%dm"%rgb);prev=rgb
            line.append(ch)
        if color:line.append(RESET)
        rows.append("".join(line))
    return "\n".join(rows)

def animate(duration=15,done=None,label="Initializing ZuzifyCMD"):
    if not TTY:return
    start=time.monotonic()
    print("\033[?25l\033[2J",end="",flush=True)
    try:
        while True:
            elapsed=time.monotonic()-start
            if elapsed>=duration:break
            size=shutil.get_terminal_size((110,42));w=max(15,min(101,size.columns-4));h=max(7,min(39,size.lines-6))
            grow=min(1,elapsed/max(.1,duration*.65));grow=grow*grow*(3-2*grow)
            art=flower_frame(elapsed,w,h,True,grow)
            pad=" "*max(0,(size.columns-w)//2);bar="━"*int(24*elapsed/duration)+"─"*(24-int(24*elapsed/duration))
            status="Cloud synchronized" if done and done.is_set() and BOOT else label
            rarity_label=(f"{RARITY.upper()}  /  {PALETTE.upper()}  /  {CHANCE:g}% startup chance" if (PALETTE,RARITY,CHANCE)==STARTUP_FLOWER else f"{PALETTE.upper()}  /  PREVIEW")
            if elapsed<duration*.65:rarity_label="B L O O M I N G"
            print("\033[H"+"\n".join("\033[2K"+pad+r for r in art.split("\n"))+"\n\033[2K"+paint(("Z U Z I F Y  /  C M D   "+VERSION).center(max(15,size.columns-1)),WHITE)+"\n\033[2K"+paint((bar+"  "+str(int(elapsed/duration*100))+"%").center(max(15,size.columns-1)),DIM)+"\n\033[2K"+paint(status.center(max(15,size.columns-1)),DIM)+"\n\033[2K"+paint(rarity_label.center(max(15,size.columns-1)),WHITE),end="",flush=True)
            time.sleep(.035)
    finally:print("\033[?25h"+RESET,end="",flush=True)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def cloud(action,**values):
    headers={"Content-Type":"application/json","User-Agent":"ZuzifyCMD/"+VERSION}
    if token:headers["Authorization"]="Bearer "+token
    req=Request(API,data=json.dumps({"action":action,**values}).encode(),headers=headers)
    try:
        with build_opener(NoRedirect()).open(req,timeout=8) as r:
            result=json.loads(r.read(2*1024*1024))
        if result.get("error"):raise RuntimeError(safe(result["error"]))
        return result
    except HTTPError as e:
        try:msg=json.loads(e.read(4096)).get("error","Cloud unavailable")
        except Exception:msg="Cloud unavailable"
        raise RuntimeError(safe(msg)) from None
    except (OSError,ValueError):raise RuntimeError("Cloud unavailable; offline tools still work.") from None

def initialize():
    global INSTALL,token,user
    folder=Path(os.getenv("LOCALAPPDATA",str(Path.home())))/"ZuzifyCMD";folder.mkdir(parents=True,exist_ok=True)
    path=folder/"install-id"
    try:INSTALL=str(uuid.UUID(path.read_text().strip()))
    except Exception:INSTALL=str(uuid.uuid4());path.write_text(INSTALL)
    try:
        import keyring
        token=keyring.get_password("ZuzifyCMD","session") or ""
    except Exception:token=""
    if token:
        try:PROFILE.update(cloud("me"));user=safe(PROFILE["username"])
        except RuntimeError:token=""

def heartbeat():
    global token,user
    while not STOP.wait(30):
        try:BOOT.update(cloud("bootstrap",install=INSTALL,version=VERSION))
        except RuntimeError:pass
        if token:
            try:PROFILE.update(cloud("heartbeat"))
            except RuntimeError as e:
                if "Session expired" in str(e) or "Sign in required" in str(e):
                    token="";user="guest";PROFILE.clear()
                    try:
                        import keyring
                        keyring.delete_password("ZuzifyCMD","session")
                    except Exception:pass
                    print("\n  Session revoked. Sign in again.",flush=True)

CORE.update({"rarity":"Show startup flower rarity","rarities":"List flower rarity chances","search":"Search command names and descriptions","login":"Sign in","register":"Create account","profile":"Show rank and profile","redeem":"Redeem a license key","friends":"Show friend requests and friends","friendadd":"Add a friend","friendaccept":"Accept a request","friendremove":"Remove a friend","discord":"Create an eight digit pairing code","discordunlink":"Unlink Discord","prostatus":"View paid entitlement","ownerstats":"Owner dashboard","ownerusers":"List users and presence","ownerban":"Ban account","ownerunban":"Unban account","ownerkick":"Revoke user sessions","ownerrank":"Change rank","ownerkey":"Create a Pro license","ownermotd":"Set message of the day","owneraudit":"Review moderation audit","motd":"Show message of the day","online":"Show active app count","calc":"Basic calculator","reverse":"Reverse text","count":"Count characters and words","upper":"Uppercase text","lower":"Lowercase text","json":"Format JSON","hex":"Encode text as hex","unhex":"Decode hex","timer":"Start a local timer","color":"Select loader color","export":"Export your profile to JSON"})
UNITS = {"length":{"mm":0.001,"cm":0.01,"dm":0.1,"m":1,"km":1000,"um":0.000001,"nm":1e-9,"in":0.0254,"ft":0.3048,"yd":0.9144,"mi":1609.344,"nmi":1852,"ang":1e-10,"fathom":1.8288,"furlong":201.168},"mass":{"mg":0.000001,"g":0.001,"kg":1,"t":1000,"ug":1e-9,"lb":0.45359237,"oz":0.028349523125,"st":6.35029318,"grain":0.00006479891,"carat":0.0002,"shortton":907.18474,"longton":1016.0469088},"time":{"ms":0.001,"s":1,"min":60,"h":3600,"d":86400,"w":604800,"us":0.000001,"ns":1e-9,"fortnight":1209600,"day365":31536000}}
CONVERSIONS = {f"{cat}_{a}_{b}":(cat,a,b) for cat,units in UNITS.items() for a in units for b in units if a!=b}

def refresh():
    global catalog
    local={k:{"handler":k,"description":v,"category":"local"} for k,v in CORE.items()}
    local.update({k:{"handler":v,"description":"Alias for "+v,"category":"local"} for k,v in ALIASES.items()})
    local.update({k:{"handler":"convert","description":f"Convert {a} to {b}","category":cat} for k,(cat,a,b) in CONVERSIONS.items()})
    try:
        BOOT.update(cloud("bootstrap",install=INSTALL,version=VERSION))
        rows=BOOT["catalog"]
        for row in rows:
            name,handler=row.get("name",""),row.get("handler","")
            if not isinstance(name,str) or not re.fullmatch(r"[a-z0-9_]{1,40}",name) or (handler not in CORE and not (handler=="convert" and name in CONVERSIONS)) or name in ALWAYS: continue
            if row.get("enabled") is not True: local.pop(name,None);continue
            local[name]={"handler":handler,"description":safe(row.get("description",""))[:150],"category":safe(row.get("category","cloud"))[:30]}
        status="Cloud catalog synchronized"
    except Exception: status="Offline catalog"
    catalog=local
    return status

def version_tuple(s):
    m=re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)\.(\d+)([a-z])",s or "")
    return (*map(int,m.groups()[:4]),ord(m.group(5))) if m else (0,0,0,0,0)
def check_update():
    data=BOOT.get("update") or {}
    if not isinstance(data,dict) or version_tuple(data.get("tag"))<=version_tuple(VERSION):return {"status":"No newer update announced"}
    url=data.get("url","");digest=data.get("digest","");tag=data.get("tag","")
    if not url.startswith("https://") or not re.fullmatch(r"[a-f0-9]{64}",digest):return {"status":"Invalid update manifest"}
    return {"status":"Update available: "+tag,"url":url,"digest":digest,"tag":tag}
def update_background():
    updates.update(check_update())
def download_update(info):
    folder=Path.home()/"Downloads";folder.mkdir(exist_ok=True)
    target=folder/("ZuzifyCMD-Setup-"+info["tag"]+".exe")
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

def password_problem(password,username,register=True):
    if not password:return "Password is empty."
    if len(password.encode("utf-8"))>72:return "Password exceeds 72 UTF-8 bytes."
    if register and len(password)<8:return "Use at least 8 characters (15+ recommended)."
    if register and (password.lower()==username or password.lower() in {"password","password1","password123","12345678","123456789","1234567890","qwerty123","letmein123","iloveyou","admin123","qwertyuiop","11111111","abcdefgh","welcome123"}):return "Choose a less predictable password."
    return ""

def masked_password(prompt):
    # On native Windows show asterisks so typing feedback is visible.
    if os.name!="nt" or not sys.stdin.isatty():return getpass.getpass(prompt)
    import msvcrt
    chars=[]
    print(prompt,end="",flush=True)
    while True:
        c=msvcrt.getwch()
        if c in ("\r","\n"):print();return "".join(chars)
        if c=="\x03":print();raise KeyboardInterrupt
        if c=="\x1b":print();return None
        if c in ("\x00","\xe0"):msvcrt.getwch();continue
        if c=="\b":
            if chars:chars.pop();print("\b \b",end="",flush=True)
        elif c.isprintable() and len(chars)<72:
            chars.append(c);print("*",end="",flush=True)

def sign_in(action,initial_name=""):
    global user,token
    if token:print("Already signed in. Use logout to switch accounts.");return
    print("\n  "+("CREATE ACCOUNT" if action=="register" else "SIGN IN")+"  |  Enter / Esc to cancel")
    if action=="register":print("  Username: 3-24 letters, numbers or underscores. Password: 8+ characters (15+ recommended).")
    name=initial_name.strip().lower()
    while not re.fullmatch(r"[a-z0-9_]{3,24}",name):
        name=input("  Username (blank to cancel): ").strip().lower()
        if not name:return
        if not re.fullmatch(r"[a-z0-9_]{3,24}",name):print("  Invalid username. Try again.")
    while True:
        password=masked_password("  Password: ")
        if password is None:return
        problem=password_problem(password,name,action=="register")
        if problem:print("  "+problem);continue
        if action=="register":
            confirm=masked_password("  Confirm password: ")
            if confirm is None:return
            if confirm!=password:print("  Passwords do not match. Try again.");continue
        try:result=cloud(action,username=name,password=password)
        except RuntimeError as e:
            print("  "+safe(e))
            if "password" in str(e).lower() and "Too many" not in str(e):continue
            return
        finally:password=None
        break
    user=safe(result["username"]);token=result["token"]
    try:PROFILE.update(cloud("me"))
    except RuntimeError:PROFILE.update({"username":user})
    if input("  Remember session on this PC? [y/N] ").strip().lower()=="y":
        try:
            import keyring
            keyring.set_password("ZuzifyCMD","session",token)
        except Exception:print("  Credential storage unavailable.")
    print("  Signed in as "+user+" / "+refresh())

def execute(handler,arg,name=""):
    global user,token,ACCENT,PALETTE
    if handler=="help":
        print("  "+str(len(catalog))+" commands. Use search <term>, help all, or help <category>.")
        for name,row in sorted(catalog.items(),key=lambda item:(item[1]["category"],item[0])):
            if arg=="all" or arg==row["category"] or (not arg and row["handler"]!="convert"):
                if name.startswith("owner") and PROFILE.get("rank")!="owner":continue
                print(paint("  "+name.ljust(22),ACCENT)+row["description"])
    elif handler=="rarity":
        print(f"Startup: {STARTUP_FLOWER[0].title()} | {STARTUP_FLOWER[1]} | {STARTUP_FLOWER[2]:g}%")
    elif handler=="rarities":
        for color,tier,chance in RARITIES:print(f"  {color.title():12} {tier:12} {chance:g}%")
    elif handler=="search":
        q=arg.lower().strip()
        if not q:raise ValueError("Use search <term>")
        for n,row in sorted(catalog.items()):
            if n.startswith("owner") and PROFILE.get("rank")!="owner":continue
            if q in (n+" "+row["description"]).lower():print(f"  {n:24} {row['description']}")
    elif handler=="clear":clear()
    elif handler=="exit":return False
    elif handler in ("login","register"):sign_in(handler,arg)
    elif handler=="whoami":
        if token:
            try:print(cloud("me")["username"])
            except RuntimeError:print("Session not verified; sign in again.")
        else:print("guest")
    elif handler=="logout":
        try:
            if token:cloud("logout")
        finally:
            user,token="guest","";PROFILE.clear()
            try:
                import keyring
                keyring.delete_password("ZuzifyCMD","session")
            except Exception:pass
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
    elif handler=="convert":
        cat,a,b=CONVERSIONS[name];v=float(arg)
        if not math.isfinite(v):raise ValueError("Enter a finite number")
        print(f"{v*UNITS[cat][a]/UNITS[cat][b]:.12g} {b}")
    elif handler in ("profile","friends","prostatus","ownerstats","ownerusers","owneraudit","ownerkey","discord","discordunlink"):
        actions={"profile":"me","friends":"friends","prostatus":"pro_status","ownerstats":"admin_stats","ownerusers":"admin_users","owneraudit":"admin_audit","ownerkey":"admin_license","discord":"discord_pair","discordunlink":"discord_unlink"}
        result=cloud(actions[handler])
        print(safe(json.dumps(result,indent=2)).replace("\\n","\n") if False else json.dumps(result,indent=2,ensure_ascii=True))
        if handler=="discord":print("Pair using your trusted Discord bot when enabled. Code expires in 5 minutes.")
    elif handler in ("friendadd","friendaccept","friendremove","ownerban","ownerunban","ownerkick"):
        actions={"friendadd":"friend_add","friendaccept":"friend_accept","friendremove":"friend_remove","ownerban":"admin_ban","ownerunban":"admin_unban","ownerkick":"admin_kick"}
        if not arg:raise ValueError("Username required")
        if handler in ("ownerban","ownerkick") and input("Confirm action? [y/N] ").lower()!="y":return True
        print(cloud(actions[handler],username=arg))
    elif handler=="ownerrank":
        target,_,rank=arg.partition(" ");print(cloud("admin_rank",username=target,rank=rank))
    elif handler=="ownermotd":print(cloud("admin_motd",text=arg))
    elif handler=="redeem":
        print(cloud("redeem",key=getpass.getpass("License key: ")));PROFILE.update(cloud("me"))
    elif handler=="motd":print(safe(BOOT.get("motd","Offline")))
    elif handler=="online":print("Active app instances (last 90 seconds):",BOOT.get("online","Unavailable"))
    elif handler=="calc":
        import operator
        m=re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*([+*/%-])\s*(-?\d+(?:\.\d+)?)",arg)
        if not m:raise ValueError("Use calc 12 + 4")
        print({"+":operator.add,"-":operator.sub,"*":operator.mul,"/":operator.truediv,"%":operator.mod}[m[2]](float(m[1]),float(m[3])))
    elif handler=="reverse":print(safe(arg[::-1]))
    elif handler=="count":print(len(arg),"characters;",len(arg.split()),"words")
    elif handler=="upper":print(safe(arg.upper()))
    elif handler=="lower":print(safe(arg.lower()))
    elif handler=="json":print(json.dumps(json.loads(arg),indent=2,ensure_ascii=True))
    elif handler=="hex":print(arg.encode().hex())
    elif handler=="unhex":print(safe(bytes.fromhex(arg).decode()))
    elif handler=="timer":
        seconds=float(arg)
        if not 0<=seconds<=3600:raise ValueError("0–3600 seconds")
        time.sleep(seconds);print("Timer finished.")
    elif handler=="color":
        if arg not in ("blue","red","orange","yellow","purple","pink","white","rainbow"):raise ValueError("Choose blue/red/orange/yellow/purple/pink/white/rainbow")
        PALETTE=arg;animate(4);clear()
    elif handler=="export":
        result=cloud("pro_status")
        profile=cloud("me");folder=Path.home()/"Downloads";folder.mkdir(exist_ok=True)
        path=folder/("ZuzifyCMD-profile-"+uuid.uuid4().hex[:8]+".json");path.write_text(json.dumps(profile,indent=2),encoding="utf-8");print("Saved "+str(path))
    elif handler=="about":print("ZuzifyCMD "+VERSION+" / By Zuzify")
    return True

def main():
    if "--self-test" in sys.argv:
        assert version_tuple("v1.2.0.1a")==(1,2,0,1,97)
        assert abs(sum(r[2] for r in RARITIES)-100)<1e-9
        assert min(RARITIES,key=lambda r:r[2])[0]=="rainbow"
        assert next(r for r in RARITIES if r[0]=="white")[1]=="Uncommon"
        assert password_problem("","test_user")
        assert password_problem("short","test_user")
        assert not password_problem("correct-horse-battery-planet","test_user")
        assert len(CONVERSIONS)==432
        assert len(flower_frame(0).splitlines())==35
        assert "\033[38;2;" in flower_frame(0,color=True)
        assert flower_frame(0)!=flower_frame(1)
        assert safe("hello\033[31m")=="hello[31m"
        print("Self-test passed.");return
    enable_vt()
    initialize()
    done=threading.Event();status=[]
    def boot():
        try:status.append(refresh())
        finally:done.set()
    threading.Thread(target=boot,daemon=True).start()
    
    animate(done=done,label="Syncing account and command catalog");done.wait(timeout=1)
    if not catalog:refresh()
    threading.Thread(target=heartbeat,daemon=True).start()
    update_background()
    clear()
    print(paint("  Z U Z I F Y  /  C M D",ACCENT))
    print(paint("  v"+VERSION+" | "+(status[0] if status else "Offline")+" | help for commands",DIM))
    print("  login / register / help | "+str(len(catalog))+" commands")
    print(f"  Flower: {STARTUP_FLOWER[0].title()} / {STARTUP_FLOWER[1]} ({STARTUP_FLOWER[2]:g}%)")
    if BOOT.get("motd"):print("  "+safe(BOOT["motd"]))
    notified=False
    while True:
        if updates and not notified:print(paint("  "+updates["status"],DIM));notified=True
        try:
            raw=input(paint("\n"+user+"@zuzify",ACCENT)+" > ").strip()
            if not raw:continue
            name,_,arg=raw.partition(" ");row=catalog.get(name.lower())
            if not row:print("Unknown command. Type help.");continue
            if not execute(row["handler"],arg,name.lower()):break
        except (KeyboardInterrupt,EOFError):print("\nBye.");break
        except Exception as e:print("  Error: "+safe(e)[:200])
    STOP.set()

if __name__=="__main__":main()
