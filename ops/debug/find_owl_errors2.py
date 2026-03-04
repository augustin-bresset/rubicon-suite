import re

with open("rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml", "r") as f:
    xml = f.read()

# check for t-esc bindings that might be evaluating undefined
bindings = re.findall(r't-esc="(.*?)"', xml)
for b in bindings:
    if "activeMargin" in b or "newMargin" in b or "copySource" in b:
        print(f"Checking esc: {b}")

