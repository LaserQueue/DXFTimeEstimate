from QueueConfig import *
from ParseArgs import args
from jsonhandler import SocketCommand
import ezdxf, math, tempfile
from time import gmtime, strftime

# Initialize config
CONFIGPATH = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULTCONFIGPATH = os.path.join(os.path.dirname(__file__), "defaultconf.json")
config = MergerConfig(CONFIGPATH, DEFAULTCONFIGPATH)
if config.new:
	printer.color_print("Config file for {name} isn't valid. Falling back on default values.", name=__name__, color=ansi_colors.RED)

# Initialize printer
printer = Printer("DXFTimeEst")

# Initialize registry
registry = Registry()

# If plugin is enabled, register to send initial packet
if config["enable"]:
	registry.on('initialPacket', {
		"action": "dxfte_send_materials",
		"materials": config["materials"]
	})

# Calculate point-to-point distance for 2D or 3D coords
def dist(coord1, coord2):
	xdist = coord2[0] - coord1[0]
	ydist = coord2[1] - coord1[1]
	return math.sqrt(xdist**2 + ydist**2)

# Receive a DXF file
def receive_dxf(**kwargs):
	material = kwargs["args"]["material"]
	speed = 0
	if material in config["materials"]:
		speed = config["materials"][material]
	else:
		speed = config["defaultspeed"]
		printer.color_print("Invalid material code {code}. Falling back on the default speed.", code=material, color=ansi_colors.RED)
	parse_dxf(kwargs["args"]["dxf_data"], speed, kwargs["args"]["name"], kwargs["ws"])

def receive_dxf_customspeed(**kwargs):
	parse_dxf(kwargs["args"]["dxf_data"], kwargs["args"]["material_speed"], kwargs["args"]["name"], kwargs["ws"])

# Register parse_dxf which is passed to receive_dxf above
registry.on('socket',
	'parse_dxf',
	receive_dxf, {
		"dxf_data": str,
		"material": str,
		"name": str
	}
)

# Register parse_dxf_customspeed for handling custom DXF speeds
registry.on('socket',
	'parse_dxf_customspeed',
	receive_dxf_customspeed, {
		"dxf_data": str,
		"material_speed": int,
		"name": str
	})

# Actually parse DXF file
def parse_dxf(data, material_speed, name, ws):
	with tempfile.NamedTemporaryFile() as fs:
		fs.write(bytes(data, 'UTF-8'))
		dxf = ezdxf.readfile(fs.name)

	modelspace = dxf.modelspace()

	if config["save_dxf_to"]:
		try:
			dxf.saveas(os.path.join(config["save_dxf_to"], strftime(name + " %Y-%m-%d %H.%M.%S.dxf", gmtime())))
		except:
			printer.color_print(config["save_dxf_fail_message"], target=config["save_dxf_to"], color=ansi_colors.RED)
			if config["save_dxf_fail_user_message"]:
				serve_connection({
					"action": "notification",
					"title": "Failed to save file",
					"text": config["save_dxf_fail_user_message"]
				}, ws)

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
			printer.color_print("Unsupported object of type {type} found. Ommitting.", type=el.dxftype(), color=ansi_colors.RED)
	t = round(totaldist / material_speed + config["initmove"]) / 60
	if args.loud:
		printer.color_print("Estimate: {time}s", time=t*60)
	serve_connection({
		"action": "dxf_estimate",
		"time": t
	}, ws)
	return t
