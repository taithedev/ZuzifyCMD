import ctypes
import datetime
import getpass
import hashlib
import locale
import os
import platform
import shutil
import socket
import subprocess
from pathlib import Path

TOOLS = {"ipconfig":"Show local Windows IP configuration","ipconfigall":"Show detailed local adapter configuration","hostname":"Show local computer name","netadapters":"List local network interfaces","diskspace":"Show available disk capacity","memory":"Show physical RAM usage","cpuinfo":"Show processor information","osinfo":"Show operating system details","processlist":"List local running processes","localroutes":"Show local IPv4 routing table","netstats":"Show local network protocol counters","drives":"List local drive letters","systeminfo":"Show local Windows system report","whoamilocal":"Show local operating system username","datetimeutc":"Show current UTC time","filesize":"Show size of a local file","filehash":"Calculate SHA-256 of a local file","basename":"Get filename from path","dirname":"Get parent from path","extension":"Get file extension","textlines":"Count text lines","titlecase":"Convert text to title case"}

CATEGORIES = {"ipconfig":"network","ipconfigall":"network","hostname":"utilities","netadapters":"network","diskspace":"utilities","memory":"utilities","cpuinfo":"utilities","osinfo":"utilities","processlist":"utilities","localroutes":"network","netstats":"network","drives":"utilities","systeminfo":"utilities","whoamilocal":"utilities","datetimeutc":"utilities","filesize":"files","filehash":"files","basename":"files","dirname":"files","extension":"files","textlines":"utilities","titlecase":"utilities"}

WINDOWS = {
    "ipconfig": ("ipconfig.exe",()),
    "ipconfigall": ("ipconfig.exe",("/all",)),
    "netadapters": ("netsh.exe",("interface","show","interface")),
    "processlist": ("tasklist.exe",("/FO","TABLE")),
    "localroutes": ("route.exe",("print","-4")),
    "netstats": ("netstat.exe",("-s",)),
    "systeminfo": ("systeminfo.exe",()),
}

def safe(s):
    return "".join(c for c in str(s) if c.isprintable() or c in "\n\t")

def windows_report(name):
    if os.name!="nt":raise RuntimeError("This diagnostic requires Windows.")
    exe,args=WINDOWS[name]
    root=Path(os.environ.get("SystemRoot",r"C:\Windows"))/"System32"
    result=subprocess.run([str(root/exe),*args],shell=False,capture_output=True,timeout=45,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    encoding="oem" if os.name=="nt" else locale.getpreferredencoding(False)
    output=safe(result.stdout.decode(encoding,errors="replace"))
    if output:print(output.rstrip())
    if result.returncode:raise RuntimeError("Windows diagnostic returned "+str(result.returncode))

def memory_report():
    if os.name!="nt":raise RuntimeError("This diagnostic requires Windows.")
    class MemoryStatus(ctypes.Structure):
        _fields_=[("length",ctypes.c_ulong),("load",ctypes.c_ulong),("total",ctypes.c_ulonglong),("available",ctypes.c_ulonglong),("page_total",ctypes.c_ulonglong),("page_available",ctypes.c_ulonglong),("virtual_total",ctypes.c_ulonglong),("virtual_available",ctypes.c_ulonglong),("extended",ctypes.c_ulonglong)]
    m=MemoryStatus();m.length=ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):raise RuntimeError("RAM information unavailable")
    print(f"Total RAM: {m.total/1024**3:.2f} GiB\nAvailable: {m.available/1024**3:.2f} GiB\nUsage: {m.load}%")

def local_file(arg):
    if not arg.strip():raise ValueError("Specify a local file path")
    p=Path(arg.strip().strip('"')).expanduser()
    if str(p).startswith(("\\\\","//")):raise ValueError("Local paths only")
    if not p.is_file():raise ValueError("File not found")
    return p

def run(name,arg):
    if name in WINDOWS:
        if arg:raise ValueError("This command takes no arguments")
        windows_report(name)
    elif name=="hostname":print(safe(socket.gethostname()))
    elif name=="whoamilocal":print(safe(getpass.getuser()))
    elif name=="diskspace":
        p=Path(arg.strip().strip('"') or Path.cwd())
        if str(p).startswith(("\\\\","//")):raise ValueError("Local paths only")
        d=shutil.disk_usage(p);print(f"Total: {d.total/1024**3:.2f} GiB | Used: {d.used/1024**3:.2f} GiB | Free: {d.free/1024**3:.2f} GiB")
    elif name=="memory":memory_report()
    elif name=="cpuinfo":print(safe(platform.processor() or platform.machine()),"| Logical CPUs:",os.cpu_count())
    elif name=="osinfo":print(safe(platform.platform()))
    elif name=="drives":
        if os.name=="nt":
            mask=ctypes.windll.kernel32.GetLogicalDrives()
            print("  ".join(chr(65+i)+":\\" for i in range(26) if mask&(1<<i)))
        else:print("/")
    elif name=="datetimeutc":print(datetime.datetime.now(datetime.timezone.utc).isoformat())
    elif name=="filesize":print(local_file(arg).stat().st_size,"bytes")
    elif name=="filehash":
        p=local_file(arg)
        if p.stat().st_size>512*1024**2:raise ValueError("File exceeds 512 MiB limit")
        h=hashlib.sha256();size=0
        with p.open("rb") as stream:
            while chunk:=stream.read(1024*1024):
                size+=len(chunk)
                if size>512*1024**2:raise ValueError("File exceeds 512 MiB limit")
                h.update(chunk)
        print(h.hexdigest())
    elif name=="basename":print(safe(Path(arg.strip().strip('"')).name))
    elif name=="dirname":print(safe(Path(arg.strip().strip('"')).parent))
    elif name=="extension":print(safe(Path(arg.strip().strip('"')).suffix))
    elif name=="textlines":print(len(arg.splitlines()))
    elif name=="titlecase":print(safe(arg.title()))
    else:raise ValueError("Unknown utility")

def self_test():
    assert len(TOOLS)==22
    assert set(CATEGORIES)==set(TOOLS)
    assert WINDOWS["ipconfig"]==("ipconfig.exe",())
    assert all(isinstance(v[1],tuple) for v in WINDOWS.values())
    if os.name=="nt":
        for exe,_ in WINDOWS.values():
            assert (Path(os.environ.get("SystemRoot",r"C:\Windows"))/"System32"/exe).is_file()
