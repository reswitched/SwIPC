import sys
sys.path.append('.')
import idparser

class Multifile(object):
	def __init__(self, *backing):
		self.backing = backing

	def __add__(self, x):
		for elem in self.backing:
			elem += x
		return self

	def __sub__(self, x):
		for elem in self.backing:
			elem -= x
		return self

	def write(self, data):
		for x in self.backing:
			x.write(data)

class Indentable(object):
	def __init__(self, fp):
		self.fp = fp
		self.indent = 0

	def __add__(self, x):
		self.indent += x
		return self

	def __sub__(self, x):
		self.indent -= x
		return self

	def write(self, data):
		if data == '\n':
			self.fp.write(data)
			return
		self.fp.write('\n'.join('\t' * self.indent + x for x in data.split('\n')))
		self.fp.flush()

def emitInt(x):
	return '0x%x' % x if x > 9 else str(x)

def S(x):
	return x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def format(elems, output=False):
	if output and len(elems) > 1:
		return '(%s)' % format(elems)

	def sub(elem):
		name, elem = elem
		ret = None
		if elem[0] == 'array':
			ret = 'array&lt;%s, %s&gt;' % (sub((None, elem[1])), emitInt(elem[2]))
		elif elem[0] == 'buffer':
			ret = 'buffer&lt;%s, %s, %s&gt;' % (sub((None, elem[1])), emitInt(elem[2]), emitInt(elem[3]))
		elif elem[0] == 'object':
			it = elem[1][0]
			if it in ifaces:
				ret = 'object&lt;<a href="ifaces.html#%s">%s</a>&gt;' % (S(it), S(it))
			else:
				ret = S(it)
		elif elem[0] == 'KObject':
			ret = 'KObject'
		elif elem[0] == 'align':
			ret = 'align&lt;%s, %s&gt;' % (emitInt(elem[1]), sub((None, elem[2])))
		elif elem[0] == 'bytes':
			ret = S('bytes<%s>' % emitInt(elem[1]))
		elif elem[0] in types:
			ret = '<a href="types.html#%s">%s</a>' % (S(elem[0]), S(elem[0]))
		else:
			assert len(elem) == 1
			ret = S(elem[0])

		assert ret is not None

		if name:
			return '%s %s' % (ret, S(name))
		else:
			return ret

	return ', '.join(map(sub, elems))

def findCmd(ifname, id):
	for name, cmd in ifaces[ifname].items():
		if cmd['cmdId'] == id:
			return (name, cmd)
	return None

types, ifaces, services = idparser.getAll()
invServices = {svc : ifname for ifname, svcs in services.items() for svc in svcs}
returnedBy = {}
takenBy = {}

for name, cmds in ifaces.items():
	for cmd in cmds.values():
		for _, elem in cmd['inputs']:
			if elem[0] == 'object':
				c = elem[1][0]
				if c not in takenBy:
					takenBy[c] = []
				takenBy[c].append((name, cmd['cmdId']))
		for _, elem in cmd['outputs']:
			if elem[0] == 'object':
				c = elem[1][0]
				if c not in returnedBy:
					returnedBy[c] = []
				returnedBy[c].append((name, cmd['cmdId']))

ifp = Indentable(file('docs/index.html', 'w'))
tfp = Indentable(file('docs/types.html', 'w'))
nfp = Indentable(file('docs/ifaces.html', 'w'))
afp = Multifile(ifp, tfp, nfp)

print >>afp, '<!doctype html><html>'
print >>afp, '\t<head>'
print >>afp, '\t<meta http-equiv="Content-Language" content="en">'
print >>afp, '\t\t<title>SwIPC</title>'
print >>afp, '\t</head>'
print >>afp, '\t<body>'
afp += 2

print >>ifp, '<h1>SwIPC</h1>'

print >>ifp, '<h2>Services</h2>'
print >>ifp, '<ul>'
ifp += 1
for service, iface in sorted(invServices.items(), key=lambda x: x[0]):
	print >>ifp, '<li><a href="ifaces.html#%s">%s</a></li>' % (iface, service)
ifp -= 1
print >>ifp, '</ul>'

print >>ifp, '<h1>Interfaces</h1>'
print >>ifp, '<ul>'
ifp += 1
for iface in sorted(ifaces.keys()):
	print >>ifp, '<li><a href="ifaces.html#%s">%s</a></li>' % (iface, iface)
ifp -= 1
print >>ifp, '</ul>'

print >>ifp, '<h2>Types</h2>'
print >>ifp, '<ul>'
ifp += 1
for elem in types:
	print >>ifp, '<li><a href="types.html#%s">%s</a></li>' % (elem, elem)
ifp -= 1
print >>ifp, '</ul>'

print >>nfp, '<h1>SwIPC Interfaces</h1>'
for name, cmds in ifaces.items():
	print >>nfp, '<a name="%s"><h2>%s</h2></a>' % (name, name)
	if name in services:
		print >>nfp, '<h3>Provides:</h3>'
		print >>nfp, '<ul>'
		nfp += 1
		for x in sorted(services[name]):
			print >>nfp, '<li>%s</li>' % x
		nfp -= 1
		print >>nfp, '</ul>'
	if name in returnedBy:
		print >>nfp, '<h3>Returned by:</h3>'
		print >>nfp, '<ul>'
		nfp += 1
		for x in sorted(returnedBy[name]):
			print >>nfp, '<li><a href="ifaces.html#%s(%i)">%s</a></li>' % (x[0], x[1], '%s::%s [%i]' % (x[0], findCmd(x[0], x[1])[0], x[1]))
		nfp -= 1
		print >>nfp, '</ul>'
	if name in takenBy:
		print >>nfp, '<h3>Taken by:</h3>'
		print >>nfp, '<ul>'
		nfp += 1
		for x in sorted(takenBy[name]):
			print >>nfp, '<li><a href="ifaces.html#%s(%i)">%s</a></li>' % (x[0], x[1], '%s::%s [%i]' % (x[0], findCmd(x[0], x[1])[0], x[1]))
		nfp -= 1
		print >>nfp, '</ul>'

	if len(cmds):
		print >>nfp, '<h3>Commands:</h3>'
		print >>nfp, '<ol>'
		nfp += 1
		for cname, cmd in sorted(cmds.items(), key=lambda x: x[1]['cmdId']):
			cdef = '%s(%s)%s' % (cname, format(cmd['inputs']), ' -&gt; %s' % format(cmd['outputs'], output=True) if len(cmd['outputs']) != 0 else '')
			print >>nfp, '<li value="%i"><a name="%s">%s</a></li>' % (cmd['cmdId'], '%s(%i)' % (name, cmd['cmdId']), cdef)
		nfp -= 1
		print >>nfp, '</ol>'

print >>tfp, '<h1>SwIPC Types</h1>'
print >>tfp, '<ul>'
tfp += 1
for name, type in types.items():
	print >>tfp, '<li><a name="%s">%s = %s</a></li>' % (name, name, format([(None, type)]))
tfp -= 1
print >>tfp, '</ul>'

afp -= 2
print >>afp, '\t</body>'
print >>afp, '</html>'
