import secrets, random, colorsys, base64, datetime, getpass, hashlib, json, math, os, platform, re, shutil, sys, threading, time, uuid
from pathlib import Path
import blossom
import terminal_ui as tui
import local_tools
import text_tools
import difflib
import unicodedata
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlparse

VERSION = "1.2.0.6a"
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
ROLLED_FLOWER = (PALETTE,RARITY,CHANCE)
STARTUP_FLOWER = ROLLED_FLOWER
CLOUD_STATE = 'Offline'

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
    return blossom.frame(phase,width,height,color,bloom,PALETTE)

def apply_flower_rank():
    global PALETTE,RARITY,CHANCE,STARTUP_FLOWER
    desired=("rainbow","Owner exclusive",100.0) if PROFILE.get("rank")=="owner" else ROLLED_FLOWER
    if STARTUP_FLOWER!=desired:
        PALETTE,RARITY,CHANCE=desired
        STARTUP_FLOWER=desired

def flower_label():
    color,tier,chance=STARTUP_FLOWER
    return f"{color.title()} / {tier} / "+("Guaranteed" if tier=="Owner exclusive" else f"{chance:g}% chance")

def animate(duration=15,done=None,label="Initializing ZuzifyCMD"):
    if not TTY:return
    start=time.monotonic()
    print("\033[?25l\033[2J",end="",flush=True)
    try:
        while True:
            elapsed=time.monotonic()-start
            if elapsed>=duration:break
            size=shutil.get_terminal_size((110,42));w=max(15,min(125,size.columns-4));h=max(7,min(49,size.lines-6))
            grow=min(1,elapsed/max(.1,duration*.65));grow=grow*grow*(3-2*grow)
            art=flower_frame(elapsed,w,h,True,grow)
            pad=" "*max(0,(size.columns-w)//2);bar="━"*int(24*elapsed/duration)+"─"*(24-int(24*elapsed/duration))
            status="Cloud synchronized" if done and done.is_set() and BOOT else label
            rarity_label=flower_label().upper() if PALETTE==STARTUP_FLOWER[0] else f"{PALETTE.upper()} / PREVIEW"
            if elapsed<duration*.65:rarity_label="B L O O M I N G"
            print("\033[H"+"\n".join("\033[2K"+pad+r for r in art.split("\n"))+"\n\033[2K"+paint(("Z U Z I F Y  /  C M D   "+VERSION).center(max(15,size.columns-1)),WHITE)+"\n\033[2K"+paint((bar+"  "+str(int(elapsed/duration*100))+"%").center(max(15,size.columns-1)),DIM)+"\n\033[2K"+paint(status.center(max(15,size.columns-1)),DIM)+"\n\033[2K"+paint(rarity_label.center(max(15,size.columns-1)),WHITE),end="",flush=True)
            time.sleep(.015)
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
    apply_flower_rank()

def heartbeat():
    global token,user
    while not STOP.wait(30):
        try:BOOT.update(cloud("bootstrap",install=INSTALL,version=VERSION))
        except RuntimeError:pass
        if token:
            try:PROFILE.update(cloud("heartbeat"));apply_flower_rank()
            except RuntimeError as e:
                if "Session expired" in str(e) or "Sign in required" in str(e):
                    token="";user="guest";PROFILE.clear();apply_flower_rank()
                    try:
                        import keyring
                        keyring.delete_password("ZuzifyCMD","session")
                    except Exception:pass
                    print("\n  Session revoked. Sign in again.",flush=True)

CORE.update({"dashboard":"Show the Zuzify dashboard","status":"Show connection and session status","history":"Show recent command names","shortcuts":"Show keyboard shortcuts","categories":"List command groups","textstats":"Analyze text length","slug":"Convert text to a URL slug","timestamp":"Print Unix timestamp","fromtimestamp":"Convert Unix timestamp to UTC","randomnum":"Generate a random integer"})
CORE.update({"rarity":"Show startup flower rarity","rarities":"List flower rarity chances","search":"Search command names and descriptions","login":"Sign in","register":"Create account","profile":"Show rank and profile","redeem":"Redeem a license key","friends":"Show friend requests and friends","friendadd":"Add a friend","friendaccept":"Accept a request","friendremove":"Remove a friend","discord":"Create an eight digit pairing code","discordunlink":"Unlink Discord","prostatus":"View paid entitlement","ownerstats":"Owner dashboard","ownerusers":"List users and presence","ownerban":"Ban account","ownerunban":"Unban account","ownerkick":"Revoke user sessions","ownerrank":"Change rank","ownerkey":"Create a Pro license","ownermotd":"Set message of the day","owneraudit":"Review moderation audit","motd":"Show message of the day","online":"Show active app count","calc":"Basic calculator","reverse":"Reverse text","count":"Count characters and words","upper":"Uppercase text","lower":"Lowercase text","json":"Format JSON","hex":"Encode text as hex","unhex":"Decode hex","timer":"Start a local timer","color":"Select loader color","export":"Export your profile to JSON"})
UNITS = {"length":{"mm":0.001,"cm":0.01,"dm":0.1,"m":1,"km":1000,"um":0.000001,"nm":1e-9,"in":0.0254,"ft":0.3048,"yd":0.9144,"mi":1609.344,"nmi":1852,"ang":1e-10,"fathom":1.8288,"furlong":201.168},"mass":{"mg":0.000001,"g":0.001,"kg":1,"t":1000,"ug":1e-9,"lb":0.45359237,"oz":0.028349523125,"st":6.35029318,"grain":0.00006479891,"carat":0.0002,"shortton":907.18474,"longton":1016.0469088},"time":{"ms":0.001,"s":1,"min":60,"h":3600,"d":86400,"w":604800,"us":0.000001,"ns":1e-9,"fortnight":1209600,"day365":31536000}}
UNITS.update({"data":{"bit":0.125,"byte":1,"kb":1000,"mb":1000000,"gb":1000000000,"tb":1000000000000,"pb":1000000000000000,"eb":1000000000000000000,"kib":1024,"mib":1048576,"gib":1073741824,"tib":1099511627776,"pib":1125899906842624,"eib":1152921504606847000,"kbit":125,"mbit":125000},"area":{"mm2":0.000001,"cm2":0.0001,"dm2":0.01,"m2":1,"km2":1000000,"um2":1e-12,"nm2":1e-18,"in2":0.00064516,"ft2":0.09290304,"yd2":0.83612736,"mi2":2589988.110336,"acre":4046.8564224,"ha":10000,"are":100,"rood":1011.7141056},"volume":{"ml":0.001,"l":1,"kl":1000,"ul":0.000001,"nl":1e-9,"m3":1000,"cm3":0.001,"mm3":0.000001,"usgal":3.785411784,"usqt":0.946352946,"uspt":0.473176473,"uscup":0.2365882365,"usfloz":0.0295735295625,"impgal":4.54609},"speed":{"mps":1,"kph":0.2777777777777778,"mph":0.44704,"knot":0.5144444444444445,"fps":0.3048,"ips":0.0254,"cmps":0.01,"mmps":0.001,"kmps":1000,"mmin":0.016666666666666666,"ftmin":0.00508,"ydps":0.9144,"ydmin":0.01524},"pressure":{"pa":1,"kpa":1000,"mpa":1000000,"gpa":1000000000,"hpa":100,"bar":100000,"mbar":100,"atm":101325,"psi":6894.757293168,"torr":133.32236842105263,"mmhg":133.322387415,"inhg":3386.389},"energy":{"j":1,"kj":1000,"mj":1000000,"wh":3600,"kwh":3600000,"mwh":3600000000,"cal":4.184,"kcal":4184}})
UNITS.update({"angle":{"rad":1,"deg":0.017453292519943295,"grad":0.015707963267948967,"turn":6.283185307179586,"arcmin":0.0002908882086657216,"arcsec":0.00000484813681109536,"urad":0.000001,"mrad":0.001,"quadrant":1.5707963267948966,"sextant":1.0471975511965976,"octant":0.7853981633974483,"sign":0.5235987755982988,"hourangle":0.2617993877991494,"minuteangle":0.004363323129985824,"secondangle":0.0000727220521664304,"mil_nato":0.0009817477042468104,"mil_sv":0.0009973310011396168,"mil_ru":0.0010471975511965976,"point":0.19634954084936207,"brad":0.02454369260617026},"force":{"n":1,"kn":1000,"dyn":0.00001,"kgf":9.80665,"gf":0.00980665,"mgf":0.00000980665,"lbf":4.4482216152605,"ozf":0.2780138509537812,"pdl":0.138254954376,"kip":4448.2216152605,"tf":9806.65,"short_tonf":8896.443230521,"long_tonf":9964.01641818352,"un":0.000001,"mn":0.001,"megan":1000000},"power":{"uw":0.000001,"mw":0.001,"w":1,"kw":1000,"mwatt":1000000,"gw":1000000000,"tw":1000000000000,"hp_mech":745.6998715822702,"hp_metric":735.49875,"btuph":0.2930710701722222,"btups":1055.05585262,"ftlbps":1.3558179483314,"ftlbpm":0.0225969658055233,"ergps":1e-7,"calps":4.184},"frequency":{"hz":1,"khz":1000,"mhz":1000000,"ghz":1000000000,"thz":1000000000000,"rpm":0.016666666666666666,"cpm":0.016666666666666666,"cph":0.0002777777777777778,"bpm":0.016666666666666666,"rps":1},"density":{"kgm3":1,"gcm3":1000,"gml":1000,"mgml":1,"lbft3":16.01846337396014,"lbin3":27679.904710191,"ozgal_us":7.489151707306039,"ozin3":1729.994044999,"slugft3":515.378818}})
CORE.update(text_tools.TOOLS)
CORE.update(local_tools.TOOLS)
CONVERSIONS = {f"{cat}_{a}_{b}":(cat,a,b) for cat,units in UNITS.items() for a in units for b in units if a!=b}

def refresh():
    global catalog,CLOUD_STATE
    local={k:{"handler":k,"description":v,"category":local_tools.CATEGORIES.get(k,"text" if k in text_tools.TOOLS else "local")} for k,v in CORE.items()}
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
    CLOUD_STATE="Connected" if status=="Cloud catalog synchronized" else "Offline"
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
    apply_flower_rank()
    if input("  Remember session on this PC? [y/N] ").strip().lower()=="y":
        try:
            import keyring
            keyring.set_password("ZuzifyCMD","session",token)
        except Exception:print("  Credential storage unavailable.")
    print("  Signed in as "+user+" / "+refresh())
    print("  Flower: "+flower_label())

def execute(handler,arg,name=""):
    global user,token,ACCENT,PALETTE
    if handler=="help":
        print("  "+str(len(catalog))+" commands. Use search <term>, help all, or help <category>.")
        for name,row in sorted(catalog.items(),key=lambda item:(item[1]["category"],item[0])):
            if arg=="all" or arg==row["category"] or (not arg and row["handler"]!="convert"):
                if name.startswith("owner") and PROFILE.get("rank")!="owner":continue
                print(paint("  "+name.ljust(22),ACCENT)+row["description"])
    elif handler=="rarity":
        print("  Flower: "+flower_label())
    elif handler=="rarities":
        for color,tier,chance in RARITIES:print(f"  {color.title():12} {tier:12} {chance:g}%")
        print("  Verified owners: guaranteed rainbow")
    elif handler=="search":
        q=arg.lower().strip()
        if not q:raise ValueError("Use search <term>")
        hits=[]
        for n,row in sorted(catalog.items()):
            if n.startswith("owner") and PROFILE.get("rank")!="owner":continue
            if q in (n+" "+row["description"]+" "+row["category"]).lower():hits.append((n,row))
        for n,row in hits[:80]:print(f"  {n:32} {row['description']}")
        print(f"  {len(hits)} matches"+(" (first 80 shown; narrow your search)" if len(hits)>80 else ""))
    elif handler=="dashboard":
        clear();show_dashboard()
    elif handler=="status":
        print("  Cloud:",CLOUD_STATE,"| Account:",user,"| Rank:",PROFILE.get("rank","guest"))
        print("  Flower:",flower_label())
    elif handler=="history":
        for idx,cmd in enumerate(tui.HISTORY,1):print(f"  {idx:3}  {cmd}")
    elif handler=="shortcuts":print("  Tab: complete | Up/Down: command history | Home/End: navigate | Esc: clear | Ctrl+U: delete to start")
    elif handler=="categories":
        from collections import Counter
        for cat,n in sorted(Counter(row["category"] for row in catalog.values()).items()):
            if cat!="owner" or PROFILE.get("rank")=="owner":print(f"  {cat:18} {n}")
    elif handler=="textstats":print(f"  {len(arg)} chars | {len(arg.split())} words | {len(arg.encode())} UTF-8 bytes")
    elif handler=="slug":print(re.sub(r"[^a-z0-9]+","-",unicodedata.normalize("NFKD",arg).encode("ascii","ignore").decode().lower()).strip("-"))
    elif handler=="timestamp":print(int(time.time()))
    elif handler=="fromtimestamp":print(datetime.datetime.fromtimestamp(float(arg),datetime.timezone.utc).isoformat())
    elif handler=="randomnum":
        lo,hi=map(int,arg.split());print(lo+secrets.randbelow(hi-lo+1))
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
            user,token="guest","";PROFILE.clear();apply_flower_rank()
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
    elif handler=="flower":animate(5);clear();show_dashboard()
    elif handler=="convert":
        cat,a,b=CONVERSIONS[name];v=float(arg)
        if not math.isfinite(v):raise ValueError("Enter a finite number")
        print(f"{v*UNITS[cat][a]/UNITS[cat][b]:.12g} {b}")
    elif handler in ("profile","friends","prostatus","ownerstats","ownerusers","owneraudit","ownerkey","discord","discordunlink"):
        actions={"profile":"me","friends":"friends","prostatus":"pro_status","ownerstats":"admin_stats","ownerusers":"admin_users","owneraudit":"admin_audit","ownerkey":"admin_license","discord":"discord_pair","discordunlink":"discord_unlink"}
        result=cloud(actions[handler])
        print(json.dumps(result,indent=2,ensure_ascii=True))
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
        if PROFILE.get("rank")=="owner" and arg!="rainbow":print("  Owner flower is locked to rainbow.");return True
        previous=PALETTE
        try:
            PALETTE=arg;animate(4)
        finally:PALETTE=previous
        clear();show_dashboard()
    elif handler=="export":
        result=cloud("pro_status")
        profile=cloud("me");folder=Path.home()/"Downloads";folder.mkdir(exist_ok=True)
        path=folder/("ZuzifyCMD-profile-"+uuid.uuid4().hex[:8]+".json");path.write_text(json.dumps(profile,indent=2),encoding="utf-8");print("Saved "+str(path))
    elif handler=="about":print("ZuzifyCMD "+VERSION+" / By Zuzify")
    elif handler in local_tools.TOOLS:local_tools.run(handler,arg)
    elif handler in text_tools.TOOLS:text_tools.run(handler,arg)
    return True

def show_dashboard():
    tui.dashboard(VERSION,user,PROFILE.get("rank","guest"),CLOUD_STATE,len(catalog),flower_label(),BOOT.get("motd",""),TTY)

def main():
    if "--self-test" in sys.argv:
        assert version_tuple("v1.2.0.6a")==(1,2,0,6,97)
        PROFILE["rank"]="owner";apply_flower_rank();assert STARTUP_FLOWER[0]=="rainbow" and STARTUP_FLOWER[2]==100
        PROFILE.clear();apply_flower_rank();assert STARTUP_FLOWER==ROLLED_FLOWER
        assert len(blossom.petals())>40000
        assert all(len(row)==85 for row in flower_frame(1).splitlines())
        assert "Guaranteed" not in flower_label()
        tui.remember("help");tui.remember("help");assert list(tui.HISTORY)==["help"]
        tui.HISTORY.clear()
        assert abs(sum(r[2] for r in RARITIES)-100)<1e-9
        assert min(RARITIES,key=lambda r:r[2])[0]=="rainbow"
        assert next(r for r in RARITIES if r[0]=="white")[1]=="Uncommon"
        assert password_problem("","test_user")
        assert password_problem("short","test_user")
        assert not password_problem("correct-horse-battery-planet","test_user")
        assert len(CONVERSIONS)==2400
        text_tools.self_test()
        local_tools.self_test()
        assert len(set(CORE)|set(ALIASES)|set(CONVERSIONS))==2500
        assert abs(UNITS["speed"]["mph"]/UNITS["speed"]["kph"]-1.609344)<1e-9
        assert UNITS["data"]["kib"]==1024
        assert UNITS["volume"]["usgal"]==3.785411784
        assert len(flower_frame(0).splitlines())==35
        assert "\033[38;2;" in flower_frame(0,color=True)
        assert flower_frame(0)!=flower_frame(1)
        assert safe("hello\033[31m")=="hello[31m"
        print("Self-test passed.");return
    enable_vt()
    done=threading.Event();status=[]
    def boot():
        try:
            initialize();status.append(refresh())
        finally:done.set()
    threading.Thread(target=boot,daemon=True).start()
    
    animate(done=done,label="Syncing account and command catalog");done.wait(timeout=1)
    if not catalog:refresh()
    apply_flower_rank()
    threading.Thread(target=heartbeat,daemon=True).start()
    update_background()
    clear()
    show_dashboard()
    notified=False
    while True:
        if updates and not notified:print(paint("  "+updates["status"],DIM));notified=True
        try:
            visible=[n for n in catalog if not n.startswith("owner") or PROFILE.get("rank")=="owner"]
            print()
            raw=tui.read_command(paint(user+"@zuzify",ACCENT)+paint(" ["+safe(PROFILE.get("rank","guest"))+"]",DIM)+" > ",visible).strip()
            if not raw:continue
            name,_,arg=raw.partition(" ");row=catalog.get(name.lower())
            if not row:
                suggestions=difflib.get_close_matches(name.lower(),visible,n=3,cutoff=.55)
                print("  Unknown command."+(" Did you mean "+", ".join(suggestions)+"?" if suggestions else " Type help."));continue
            if name.lower().startswith("owner") and PROFILE.get("rank")!="owner":
                print("  Owner rank required.");continue
            tui.remember(name.lower())
            if not execute(row["handler"],arg,name.lower()):break
        except (KeyboardInterrupt,EOFError):print("\nBye.");break
        except Exception as e:print("  Error: "+safe(e)[:200])
    STOP.set()

if __name__=="__main__":main()
