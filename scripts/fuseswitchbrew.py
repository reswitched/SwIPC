import sys, os, json, numbers
sys.path.append('.')
from idparser import parse

dir = os.path.dirname(os.path.realpath(__file__)) + '/'

def getFile(fname):
	if os.path.exists(fname + '.cache') and os.path.getmtime(fname + '.cache') > os.path.getmtime(fname):
		res = json.load(file(fname + '.cache'))
	else:
		res = parse(file(fname).read())
		with file(fname + '.cache', 'w') as fp:
			json.dump(res, fp)
	return res

auto = os.path.dirname(os.path.realpath(__file__)) + '/../ipcdefs/auto.id'
switchbrew = os.path.dirname(os.path.realpath(__file__)) + '/../ipcdefs/switchbrew_unfused.id'

autoTypes, autoIfaces, autoServices = getFile(auto)
switchbrewTypes, switchbrewIfaces, switchbrewServices = getFile(switchbrew)

# Invert services auto
autoServicesToIFace = {}
for ifaceName, services in autoServices.items():
	for service in services:
		autoServicesToIFace[service] = ifaceName

switchbrewServicesToIFace = {}
for ifaceName, services in switchbrewServices.items():
	for service in services:
		switchbrewServicesToIFace[service] = ifaceName


#print autoServicesToIFace
#print switchbrewServicesToIFace

fusedIFaces = {}

for ifaceName, iface in switchbrewIfaces.items():
	newIFace = fusedIFaces[ifaceName] = {"cmds": [], "doc": ""}
	autoIface = autoIfaces.get(ifaceName)
	for cmd in iface['cmds']:
		newCmd = {'doc': cmd['doc'], 'cmdId': cmd['cmdId'], 'name': cmd['name'], 'versionAdded': cmd['versionAdded'], 'lastVersion': cmd['lastVersion'], 'inputs': 'unknown', 'outputs': 'unknown', 'undocumented': True}
		autoCmdMaybe = ([autoCmd for autoCmd in autoIface['cmds'] if cmd['cmdId'] == autoCmd['cmdId']]) if autoIface != None else []
		if len(autoCmdMaybe) > 0:
			autoCmd = autoCmdMaybe.pop()
			if newCmd['name'].startswith("Unknown"):
				newCmd['name'] = autoCmd['name']
			elif (not autoCmd['name'].startswith("Unknown")) and (newCmd['name'] != autoCmd['name']):
				sys.stderr.write('warning: %s != %s\n' % (newCmd['name'], autoCmd['name']))
			newCmd['inputs'] = autoCmd['inputs']
			newCmd['outputs'] = autoCmd['outputs']
			newCmd['undocumented'] = autoCmd['undocumented']
			newIFace['cmds'].append(newCmd)
		else:
			newIFace['cmds'].append(newCmd)

def genVersion(added, last):
	if added == last:
		return added
	elif last is not None:
		return added + "-" + last
	else:
		return added + "+"

def fmt(x):
	if isinstance(x, numbers.Number):
		if x >= 10:
			return '0x%x' % x
		else:
			return str(x)
	else:
		return str(x)
        
def genArgs(elems, output=False):
#	sys.stderr.write(str(elems) + '\n')
	if elems == 'unknown':
		if output:
			return ' -> unknown'
		else:
			return 'unknown'
	if output and len(elems) > 1:
		return ' -> (%s)' % genArgs(elems)

	def sub(elem):
		name, elem = elem
		ret = elem[0]
		if len(elem) > 1:
			ret = ret + "<" + ",".join(map(lambda x: sub((None, x)) if type(x) is list else fmt(x), elem[1:])) + ">"
		if name is not None:
			return ret + " " + name
		else:
			return ret

	base = ""
	if output and len(elems) > 0:
		base = " -> "
	return base + ', '.join(map(sub, elems))

def printIFace(ifaceName, iface, services):
	isService = ""
	if services is not None and len(services) > 0:
		isService = "is " + ", ".join(services) + " "
	print "interface %s %s{" % (ifaceName, isService)
	for cmd in sorted(iface['cmds'], key=lambda x: x['cmdId']):
		if cmd['doc'] != "":
			for docLine in cmd['doc'].split("\n"):
				# kill weird non ascii
				print "\t#%s" % docLine.encode('utf-8')
		if cmd['versionAdded'] != "1.0.0" or cmd['lastVersion'] is not None:
			print "\t@version(%s)" % (genVersion(cmd['versionAdded'], cmd['lastVersion']))
		if cmd['undocumented']:
			print "\t@undocumented"
		print "\t[%d] %s(%s)%s;" % (cmd['cmdId'], cmd['name'], genArgs(cmd['inputs']), genArgs(cmd['outputs'], True))
	print "}"

for ifaceName, iface in sorted(fusedIFaces.items()):
        services = autoServices.get(ifaceName)
        if services is None:
                services = switchbrewServices.get(ifaceName)
	printIFace(ifaceName, iface, services)
	print ""
