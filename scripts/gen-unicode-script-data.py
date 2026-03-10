import requests


MAX_CODEPOINTS = 0x110000

SCRIPTS_DATA_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Scripts.txt"


def get_script_data():
    res = requests.get(SCRIPTS_DATA_URL)
    res.raise_for_status()
    data = res.content.decode()
    
    script_data = []
    
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

        script_data.append([script, cpt_lower, cpt_upper])

    script_data.sort(key=lambda x: x[1])

    merged_data = [script_data[0]]
    for sd in script_data[1:]:
        if merged_data[-1][0] == sd[0] and merged_data[-1][2] + 1 == sd[1]:
            merged_data[-1][2] = sd[2]
        else:
            merged_data.append(sd)

    script_data = {}
    # script_heads = {}
    # script_tails = {}
    for md in merged_data:
        # if md[0] not in script_heads:
        #     script_heads[md[0]] = []
        # script_heads[md[0]].append(md[1])
        # if md[0] not in script_tails:
        #     script_heads[md[0]] = []
        # script_tails[md[0]].append(md[2])
        if md[0] in script_data:
            script_data[md[0]].append([md[1], md[2]])
        else:
            script_data[md[0]] = [[md[1], md[2]]]

    # return script_heads, script_tails
    return script_data


# def cpt_to_base16(cpt):
#     return int(chr(cpt).encode("utf-8").hex(), 16)


# Generate 'unicode-script-data.cpp':
#   python ./scripts//gen-unicode-script-data.py > unicode-script-data.cpp

def out(line=""):
    print(line, end='\n')  # noqa


# heads, tails = get_script_data()
data = get_script_data()

out("""\
// generated with scripts/gen-unicode-scripts-data.py

#include "unicode-data.h"

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>
""")

out("constexpr std::unordered_map<std::string, std::pair<std::vector<uint32_t>, std::vector<uint32_t>> unicode_scripts_ranges = {")

for script in script_data:
    out("{ \"%s\", { {" % script)
    for data in script_data[script]:
        out("    0x%06X," % data[0])
    out("}, {")
    for data in script_data[script]:
        out("    0x%06X," % data[1])
    out("} } },")

out("};")
