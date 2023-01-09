#!/usr/bin/env python3
"""This is the test harness for assessing the 2021-22 Vision assignment."""

#-------------------------------------------------------------------------------
# Boilerplate.
#-------------------------------------------------------------------------------

import sys, subprocess, os.path

#-------------------------------------------------------------------------------
# Routines.
#-------------------------------------------------------------------------------

def run_program (program, fn):
    """Run the program under test and scan its output for the lines that
    interest us."""
    # We'll fail unless we encounter valid inputs.
    xpos = None
    ypos = None
    dirn = None

    # Build up the command line and to run the program under test, then run it
    # and capture its standard output stream.
    result = subprocess.run (["python3", program, fn],
                             stdout=subprocess.PIPE)

    # Convert the program's output to UTF-8 and split it into lines.  Then
    # look for lines that start with the keywords of interest.
    result = result.stdout.decode('utf-8')
    for line in result.split ("\n"):
        line = line.rstrip ()                # remove trailing newlines
        words = line.split ()                # split the line into words
        if len (words) < 1: continue         # ignore blank lines
        if words[0] == "POSITION":
            if len (words) != 3: continue    # it's in the wrong format
            try:
                xpos = float (words[1])
                ypos = float (words[2])
            except:
                print ("Couldn't convert POSITION arguments: line ignored.",
                       file=sys.stderr)
        elif words[0] == "BEARING":
            if len (words) != 2: continue    # it's in the wrong format
            try:
                dirn = float (words[1])
            except:
                print ("Couldn't convert BEARING argument: line ignored.",
                       file=sys.stderr)

    # Return what we have extracted.
    return xpos, ypos, dirn

#-------------------------------------------------------------------------------
# Main program.
#-------------------------------------------------------------------------------

# The command line should contain the name of the program under test; if one
# was not supplied, use a default name.
nargs = len (sys.argv)
if nargs == 1:
    program = "mapreader.py"
elif nargs == 2:
    program = sys.argv[1]
else:
    print ("Usage: %s [program]" % sys.argv[0], file=sys.stderr)
    exit (1)

# Make sure the program exists.
if not os.path.isfile (program):
    print ("The program '%s' doesn't exist!" % program, file=sys.stderr)
    exit (2)

# Set up the ground truth for all the images we may use.
GT = [
    [0.441, 0.607, 264.0, "develop/develop-001.jpg"],
    [0.440, 0.604, 265.0, "develop/develop-002.jpg"],
    [0.451, 0.590, 263.0, "develop/develop-003.jpg"],
    [0.448, 0.596, 264.5, "develop/develop-004.jpg"],
    [0.647, 0.590,   3.0, "develop/develop-005.jpg"],
    [0.640, 0.584,  89.0, "develop/develop-006.jpg"],
    [0.651, 0.586, 179.0, "develop/develop-007.jpg"],
    [0.652, 0.588, 272.0, "develop/develop-008.jpg"],
    # MSc only.
    [0.652, 0.588, 272.0, "develop/develop-010.jpg"],
    [0.441, 0.607, 264.0, "develop/develop-011.jpg"],
    # Adrian's tests.
    [0.182, 0.500,  80.0, "test/test-001.jpg"],
    [0.270, 0.583, 354.0, "test/test-002.jpg"],
    [0.556, 0.606, 288.0, "test/test-003.jpg"],
    [0.557, 0.600, 288.5, "test/test-004.jpg"],
]

# The format we shall use to output things.
fmt = "%7.1f %7.1f %7.1f %7.2f %7.2f %7.2f  %s"

# Work through each entry in GT, running the program under test and collecting
# the results, printing out their discrepancy from hand measurements.
print ("   Xpos    Ypos    Dirn    Xerr    Yerr    Derr  filename")
for xtrue, ytrue, dtrue, fn in GT:
    if not os.path.exists (fn): continue    # tests only with images we have
    xpos, ypos, dirn = run_program (program, fn)
    if xpos is None or ypos is None or dirn is None:
        print ("%47s  %s" % ("failure", fn))
    else:
        xerr = abs (xpos - xtrue)
        yerr = abs (ypos - ytrue)
        derr = abs (dirn - dtrue)
        if derr > 270:
            derr = abs (derr - 360)
        print (fmt % (xpos, ypos, dirn, xerr, yerr, derr, fn))

#-------------------------------------------------------------------------------
# End of harness.py
#-------------------------------------------------------------------------------
