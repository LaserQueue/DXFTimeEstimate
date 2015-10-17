#!/usr/bin/env python3

# proof of concept hack

speed = 10
initmove = 3

import ezdxf
import math
import inspect
# import sys

dxf = ezdxf.readfile("many shape types from rhino.dxf")
modelspace = dxf.modelspace()

totaldist = 0

# calculate distance between two XYZ coords
def dist(coord1, coord2):
	xdist = coord2[0] - coord1[0]
	ydist = coord2[1] - coord1[1]
	return math.sqrt(xdist**2 + ydist**2)

# for every element
for e in modelspace:
	# if element is a POLYLINE
	if e.dxftype() == "POLYLINE":
		newpoint = 0
		oldpoint = 0
		polyline = enumerate(list(e.vertices()))

		# for each point on POLYLINE
		for i, point in polyline:
			oldpoint = newpoint
			newpoint = point.dxf.location
			if oldpoint != 0:
				totaldist += dist(newpoint, oldpoint)
	elif e.dxftype() == "LINE":
		totaldist += dist(e.dxf.start, e.dxf.end)
	elif e.dxftype() == "CIRCLE":
		totaldist += 2 * math.pi * e.dxf.radius
	elif e.dxftype() == "ARC":
		circumference = 2 * math.pi * e.dxf.radius
		arcportion = abs(e.dxf.start_angle - e.dxf.end_angle) / 360
		totaldist += circumference * arcportion
	# elif e.dxftype() == "SPLINE":
	else:
		print("UNSUPPORTED ELEMENT OF TYPE " + e.dxftype() + " FOUND. OMITTING.")

time = totaldist / speed + initmove
print("Total cut time is " + str(time) + "s.")
