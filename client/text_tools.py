import codecs
import json
import re
from collections import Counter
from urllib.parse import quote, unquote

TOOLS = {"wordfreq":"Count the most frequent words in text","textsort":"Sort words alphabetically","textunique":"Remove duplicate words","textswap":"Swap letter case","jsonmin":"Minify JSON text","urlencode":"Percent-encode text","urldecode":"Decode percent-encoded text","textrot13":"Apply ROT13 to text"}

def clean(s):
    return "".join(c for c in str(s) if c.isprintable())

def run(name,arg):
    if name=="wordfreq":
        for word,n in Counter(re.findall(r"\w+",arg.casefold())).most_common(30):
            print(f"{n:5} {clean(word)}")
    elif name=="textsort":print(clean(" ".join(sorted(arg.split(),key=str.casefold))))
    elif name=="textunique":print(clean(" ".join(dict.fromkeys(arg.split()))))
    elif name=="textswap":print(clean(arg.swapcase()))
    elif name=="jsonmin":print(json.dumps(json.loads(arg),separators=(",",":"),ensure_ascii=True))
    elif name=="urlencode":print(quote(arg,safe=""))
    elif name=="urldecode":print(clean(unquote(arg,errors="strict")))
    elif name=="textrot13":print(clean(codecs.decode(arg,"rot_13")))
    else:raise ValueError("Unknown text tool")

def self_test():
    assert len(TOOLS)==8
    assert unquote(quote("a b",safe=""))=="a b"
    assert codecs.decode("abc","rot_13")=="nop"
