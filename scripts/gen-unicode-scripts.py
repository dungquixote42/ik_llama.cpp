
from collections import defaultdict

import requests

MAX_CODEPOINTS = 0x110000

SCRIPT_DATA_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Scripts.txt"


res = requests.get(SCRIPT_DATA_URL)
res.raise_for_status()
data = res.content.decode()
script_cptL_cptU = []

for line in data.splitlines():
    line = line.split()
    if len(line) <= 1 or line[0] == "#":
        continue
    assert line[1] == ";"
    assert line[3] == "#"

    cpt = line[0].split("..")
    if len(cpt) == 1:
        cpt += cpt
    cpt_lower, cpt_upper = cpt

    cpt_lower = int(cpt_lower, 16)
    assert cpt_lower < MAX_CODEPOINTS

    cpt_upper = int(cpt_upper, 16)
    assert cpt_upper < MAX_CODEPOINTS

    script = line[2].lower()

    script_cptL_cptU.append([script, cpt_lower, cpt_upper])

script_cptL_cptU.sort(key=lambda x: x[1])

# merge neighboring codepoints that belong to same script
im = 0  # merge index
for script, cpt_lower, cpt_upper in script_cptL_cptU[1:]:
    if (script_cptL_cptU[im][0] == script) and (script_cptL_cptU[im][2] + 1 == cpt_lower):
        script_cptL_cptU[im][2] = cpt_upper
    else:
        im += 1
        script_cptL_cptU[im] = [script, cpt_lower, cpt_upper]
del script_cptL_cptU[im + 1:]

# group codepoint ranges by scripts
script_cptLUs = defaultdict(list)
for script, cpt_lower, cpt_upper in script_cptL_cptU:
    script_cptLUs[script].append([cpt_lower, cpt_upper])
del script_cptL_cptU


# Generate 'unicode-script-data.cpp':
#   python ik_llama.cpp/scripts/gen-unicode-scripts.py > ik_llama.cpp/src/unicode-scripts.cpp

def out(line=""):
    print(line, end='\n')  # noqa


out("""\
// generated with scripts/gen-unicode-scripts.py

#include "unicode-data.h"

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>
""")

out("const std::unordered_map<std::string, std::pair<std::vector<uint32_t>, std::vector<uint32_t>>> unicode_scripts = {")

out("{ \"ascii\", { {")
out("    0x000000,")
out("}, {")
out("    0x00007F,")
out("} } },")

for script in script_cptLUs:
    out("{ \"%s\", { {" % script)
    for cpt_lower, _ in script_cptLUs[script]:
        out("    0x%06X," % cpt_lower)
    out("}, {")
    for _, cpt_upper in script_cptLUs[script]:
        out("    0x%06X," % cpt_upper)
    out("} } },")

out("};")
