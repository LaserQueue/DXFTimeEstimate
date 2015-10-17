from QueueConfig import *
from jsonhandler import SocketCommand
import ezdxf, math

def dist(coord1, coord2):
	xdist = coord2[0] - coord1[0]
	ydist = coord2[1] - coord1[1]
	return math.sqrt(xdist**2 + ydist**2)

printer = PluginPrinterInstance()
printer.setname("DXFTimeEst")

def receive_dxf(**kwargs):
	printer.color_print("Estimate: {t}", t=parse_dxf["args"]["dxf_data"])

speed = 10
initmove = 3
def parse_dxf(data):
	fs = io.StringIO(data)
	dxf = ezdxf.read(fs)
	modelspace = dxf.modelspace()

	totaldist = 0
	for el in modelspace:
		if el.dxftype() == "POLYLINE":
			newpoint = 0
			oldpoint = 0

			# for each point on POLYLINE
			for point in el.vertices():
				oldpoint = newpoint
				newpoint = point.dxf.location
				if oldpoint != 0:
					totaldist += dist(newpoint, oldpoint)
		elif el.dxftype() == "LINE":
			totaldist += dist(el.dxf.start, el.dxf.end)
		elif el.dxftype() == "CIRCLE":
			totaldist += 2 * math.pi * el.dxf.radius
		elif el.dxftype() == "ARC":
			circumference = 2 * math.pi * el.dxf.radius
			arcportion = abs(el.dxf.start_angle - el.dxf.end_angle) / 360
			totaldist += circumference * arcportion
		# elif el.dxftype() == "SPLINE":
		else:
			printer.color_print("Unsupported object of type {type} found. Ommitting.", type=el.dxftype(), color=bcolors.RED)
	return totaldist / speed + initmove

socketCommands = [
	SocketCommand("send_dxf", receive_dxf, {"dxf_data": str})
]
