#!/usr/bin/python

# bam2clone - Takes an original Bambuzle level and converts it to
# the CSV out format used by the pygame clone

# Usage: bam2clone <infile> [<outfile>]
# If no infile is supplied then the output is set to infile.csv

import sys

tiles=[
    "B",        # 0 = Blank
    "H",        # 1 = Horizontal
    "V",        # 2 = Vertical
    "SEL",      # 3 = South East corner
    "SWL",      # 4 = South West corner
    "NEL",      # 5 = North East corner
    "NWL",      # 6 = North West corner
    "W",        # 7 = Wheel
    "PV.Y",     # 8 = Yellow vertical painter
    "PV.B",     # 9 = Blue vertical painter
    "PV.G",     # A = Green vertical painter
    "PV.R",     # B = Red vertical painter
    "PH.Y",     # C = Yellow horizontal painter
    "PH.B",     # D = Blue horizontal painter
    "PH.G",     # E = Green horizontal painter
    "PH.R",     # F = Red horizontal painter
    "BV.Y",     # 10 = Yellow vertical blocker
    "BV.B",     # 11 = Blue vertical blocker
    "BV.G",     # 12 = Green vertical blocker
    "BV.R",     # 13 = Red vertical blocker
    "BH.Y",      # 14 = Yellow horizontal blocker
    "BH.B",      # 15 = Blue horizontal blocker
    "BH.G",     # 16 = Green hosizontal blocker
    "BH.R",     # 17 = Red horizontal blocker
    "ST",       # 18 = SouthT
]
if len(sys.argv) < 2:
    print("Usage: bam2clone <infile> [<outfile>]")
    exit(1)
sys.argv.pop(0)
infile=sys.argv.pop(0)
if len(sys.argv)==0:
    # No second argument
    outfile=infile+".csv"
else:
    outfile=sys.argv.pop(0)

print("Converting {} into {}....".format(infile, outfile))

with open(infile, "rb") as levfile:
    # Read the entire file into a byte array
    levarray = levfile.read()
fileSize=len(levarray)

ofile = open(outfile, "w")

hasUnknown=False
for row in range(0,6):
    for col in range(0,8):
        # Data is in 5 byte blocks with the last byte being the most significat
        # The layout is also sideways so we start at the bottom left, then go up the left
        # hand side to the top left. The top right is the last byte.
        pos=30*(col)+(30-row*5)-1
        val=levarray[pos]
        if tiles[val][0]=='U':
            hasUnknown=True
        #print("{:02X}  ".format(levarray[pos]),end="")
        outstr="{}".format(tiles[val])
        if(col!=7):
            outstr+=","
        print(outstr, end="")
        ofile.write(outstr)
    print()
    ofile.write("\n")
ofile.close

if hasUnknown:
    print("Warning: This conversion has unknown tiles")