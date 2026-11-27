"""Native Zuzify command-line editor and dashboard (no shell subprocess)."""
import os,sys,shutil
from collections import deque

RESET="\033[0m"
DIM="\033[90m"
BRIGHT="\033[97m"
ACCENT="\033[38;2;160;130;255m"
HISTORY=deque(maxlen=100)
# Only store command names, never input arguments, credentials or license keys.
def remember(name):
    if name and (not HISTORY or HISTORY[-1]!=name):HISTORY.append(name)

def read_command(prompt,commands):
    if os.name!="nt" or not sys.stdin.isatty() or not sys.stdout.isatty():
        return input(prompt)
    import msvcrt
    buf=[];cursor=0;index=len(HISTORY);draft=""
    def redraw():
        # Keep editing within a single visible line; longer pasted commands are still retained.
        width=max(16,shutil.get_terminal_size((100,30)).columns)
        usable=max(5,width-32)
        start=max(0,cursor-usable+1)
        shown="".join(buf[start:start+usable])
        tail=max(0,len(shown)-(cursor-start))
        sys.stdout.write("\r\033[2K"+prompt+shown+("\033[%dD"%tail if tail else ""))
        sys.stdout.flush()
    sys.stdout.write(prompt);sys.stdout.flush()
    while True:
        c=msvcrt.getwch()
        if c in ("\r","\n"):print();return "".join(buf)
        if c=="\x03":print();raise KeyboardInterrupt
        if c=="\x1a":print();raise EOFError
        if c=="\x1b":buf=[];cursor=0;redraw();continue
        if c=="\x15":del buf[:cursor];cursor=0;redraw();continue
        if c=="\b":
            if cursor:cursor-=1;buf.pop(cursor)
        elif c=="\t":
            part="".join(buf)
            if " " not in part and part:
                matches=sorted(n for n in commands if n.startswith(part))
                if len(matches)==1:buf=list(matches[0]+" ");cursor=len(buf)
                elif matches:
                    print("\n"+"  ".join(matches[:24]));redraw();continue
        elif c in ("\x00","\xe0"):
            k=msvcrt.getwch()
            if k=="K":cursor=max(0,cursor-1)
            elif k=="M":cursor=min(len(buf),cursor+1)
            elif k=="G":cursor=0
            elif k=="O":cursor=len(buf)
            elif k=="S" and cursor<len(buf):buf.pop(cursor)
            elif k=="H" and index>0:
                if index==len(HISTORY):draft="".join(buf)
                index-=1;buf=list(HISTORY[index]);cursor=len(buf)
            elif k=="P" and index<len(HISTORY):
                index+=1;buf=list(HISTORY[index] if index<len(HISTORY) else draft);cursor=len(buf)
        elif c.isprintable() and len(buf)<4096:
            buf.insert(cursor,c);cursor+=1
        redraw()

def dashboard(version,user,rank,cloud,commands,flower,motd,tty=True):
    width=max(34,min(74,shutil.get_terminal_size((80,24)).columns-2))
    def clip(s):return "".join(c for c in str(s) if c.isprintable())[:width-4]
    def line(s):return "  "+clip(s)
    def tint(s,c):return c+s+RESET if tty else s
    print()
    print(tint(line("Z U Z I F Y  /  C M D"),BRIGHT))
    print(tint(line("━"*(width-4)),DIM))
    print(line("v"+version+"   •   "+cloud))
    print(line("ACCOUNT  "+user+"   /   "+rank.upper()))
    print(line("FLOWER   "+flower))
    print(line("COMMANDS "+str(commands)+"   /   help, search, dashboard"))
    if motd:print(tint(line("MOTD     "+str(motd)),DIM))
    print(tint(line("━"*(width-4)),DIM))
