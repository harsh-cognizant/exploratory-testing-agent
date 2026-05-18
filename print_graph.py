import json, sys
data = json.load(sys.stdin)
for node in data.get("nodes", []):
    print(node["id"], node["type"], node.get("element_type", "MISSING"))

