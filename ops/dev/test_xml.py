import xml.parsers.expat
import sys

parser = xml.parsers.expat.ParserCreate()

path = []

def start_element(name, attrs):
    path.append((name, parser.CurrentLineNumber))

def end_element(name):
    start_tag, start_line = path.pop()
    if start_line == 4 and name == "div":
        print(f"MAIN DIV CLOSED AT LINE {parser.CurrentLineNumber}")

parser.StartElementHandler = start_element
parser.EndElementHandler = end_element

with open("rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml", "rb") as f:
    try:
        parser.ParseFile(f)
    except xml.parsers.expat.ExpatError as e:
        print(f"Error at line {e.lineno}")
