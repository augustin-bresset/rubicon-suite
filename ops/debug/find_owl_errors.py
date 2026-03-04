import re

with open("rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml", "r") as f:
    xml = f.read()

with open("rubicon_addons/pdp_frontend/static/src/js/pdp_workspace.js", "r") as f:
    js = f.read()

bindings = re.findall(r't-(?:on-click|on-change|if|foreach)="(.*?)"', xml)
for b in bindings:
    # simple extraction of fn names
    fns = re.findall(r'this\.([a-zA-Z_0-9]+)', b)
    for fn in fns:
        if "state" not in fn and fn not in js:
            print(f"Missing method: {fn} bound in: {b}")

    fns2 = re.findall(r'\b([a-zA-Z_0-9]+)\(', b)
    for fn in fns2:
        if "state" not in fn and fn not in ["Array", "parseFloat", "parseInt", "find", "map"]:
            if fn not in js:
                print(f"Missing direct method: {fn} bound in: {b}")

