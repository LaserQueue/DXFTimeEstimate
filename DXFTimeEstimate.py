from QueueConfig import *
from ParseArgs import args
from jsonhandler import SocketCommand
import ezdxf, math, tempfile

CONFIGDIR = os.path.join(os.path.dirname(__file__), "config.json")

def dist(coord1, coord2):
	xdist = coord2[0] - coord1[0]
	ydist = coord2[1] - coord1[1]
	return math.sqrt(xdist**2 + ydist**2)

printer = PluginPrinterInstance()
printer.setname("DXFTimeEst")

def receive_dxf(**kwargs):
	t = parse_dxf(kwargs["args"]["dxf_data"])
	if args.loud:
		printer.color_print("Estimate: {time}", time=t)
	serve_connection({
		"action": "dxf_estimate",
		"time": t
	}, kwargs["ws"])

try:
	config = Config(CONFIGDIR)
except:
	config = {}
speed = config.get("defaultspeed", 10)
initmove = config.get("initmove", 3)
materials = config.get("materials", {})

def parse_dxf(data):
	with tempfile.NamedTemporaryFile() as fs:
		fs.write(bytes(data, 'UTF-8'))
		dxf = ezdxf.readfile(fs.name)

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
