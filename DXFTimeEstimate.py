from QueueConfig import *
from jsonhandler import SocketCommand
import ezdxf

printer = PluginPrinterInstance()
printer.setname("DXFTimeEst")

def receive_dxf(**kwargs):
	printer.color_print("DXF file received.")
	# print(kwargs["args"]["dxf_data"])

socketCommands = [
	SocketCommand("send_dxf", receive_dxf, {"dxf_data": str})
]
