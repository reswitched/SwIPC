import sys
sys.path.append('.')
import idparser
import CommonMark

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
		elif elem[0] == 'struct':
			ret = '<ul>'
			for field in elem[1]:
				ret += '\t<li class="text-muted">%s %s</li>' % (sub((None, field[1])), field[0])
			ret += '</ul>'
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
	for name, cmd in ifaces[ifname]['cmds'].items():
		if cmd['cmdId'] == id:
			return (name, cmd)
	return None

types, ifaces, services = idparser.getAll()
invServices = {svc : ifname for ifname, svcs in services.items() for svc in svcs}
returnedBy = {}
takenBy = {}

for name, iface in ifaces.items():
	cmds = iface['cmds']
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

ifaceCompleteness = dict(IUnknown=0, IPipe=100, NPort=100)
for name, iface in ifaces.items():
	cmds = iface['cmds']
	complete = 0
	count = 0
	for cname, cmd in cmds.items():
		count += 6
		if cmd['doc'] != "":
			complete += 6
		elif not cname.startswith('Unknown'):
			complete += 4
		elif len(cmd['inputs']) or len(cmd['outputs']):
			complete += 3
		else:
			complete += 1
	if count == 0:
		count = 1

	ifaceCompleteness[name] = int(complete * 100. / count)

ifaceTotalCompleteness = {}
for name, iface in ifaces.items():
	cmds = iface['cmds']
	deps = set([name])
	for cmd in cmds.values():
		for _, elem in cmd['outputs']:
			if elem[0] == 'object':
				deps.add(elem[1][0])
	ifaceTotalCompleteness[name] = int(sum(ifaceCompleteness[dep] for dep in deps) / float(len(deps)))

ifp = Indentable(file('docs/index.html', 'w'))
tfp = Indentable(file('docs/types.html', 'w'))
nfp = Indentable(file('docs/ifaces.html', 'w'))
afp = Multifile(ifp, tfp, nfp)

print >>afp, '<!doctype html><html>'
print >>afp, '\t<head>'
print >>afp, '\t\t<meta http-equiv="Content-Language" content="en">'
print >>afp, '\t\t<title>SwIPC</title>'
print >>afp, '\t\t<link rel="stylesheet" href="css/bootstrap.min.css" />'
print >>ifp, '\t\t<link rel="stylesheet" href="css/bootstrap-toc.min.css" />'
print >>afp, '\t\t<link rel="stylesheet" href="css/main.css" />'
print >>ifp, '\t\t<script type="text/javascript" src="js/jquery-3.2.1.min.js"></script>'
print >>ifp, '\t\t<script type="text/javascript" src="js/bootstrap.min.js"></script>'
print >>ifp, '\t\t<script type="text/javascript" src="js/bootstrap-toc.min.js"></script>'
print >>afp, '\t\t<script type="text/javascript" src="js/title.js"></script>'
print >>afp, '\t</head>'
print >>ifp, '\t<body data-spy="scroll" data-target="#toc">'
print >>tfp, '\t<body>'
print >>nfp, '\t<body>'
print >>afp, '\t\t<div class="container">'
afp += 3

print >>ifp, '<div class="row">'
print >>ifp, '\t<div class="col-11">'
print >>ifp, '\t\t<div class="jumbotron">'
print >>ifp, '\t\t\t<h1 class="display-3">SwIPC</h1>'
print >>ifp, '\t\t\t<p class="lead">Your one-stop-shop for Nintendo Switch IPC definitions.</p>'
print >>ifp, '\t\t</div>'
ifp += 2

print >>ifp, '<h2 id="services">Services</h2>'
print >>ifp, '<div class="list-group">'
ifp += 1
for service, iface in sorted(invServices.items(), key=lambda x: x[0]):
	print >>ifp, '<a class="list-group-item list-group-item-action" href="ifaces.html#%s">' % iface
	print >>ifp, '<div class="progress" style="width: 100px"><div class="progress-bar bg-success progress-bar-striped" role="progressbar" aria-valuenow="%i" aria-valuemin="0" aria-valuemax="100" style="width: %i%%"></div></div>' % (ifaceTotalCompleteness[iface], ifaceTotalCompleteness[iface])
	print >>ifp, '%s</a>' % service
ifp -= 1
print >>ifp, '</div>'
print >>ifp, '<br />'

print >>ifp, '<h2 id="interfaces">Interfaces</h2>'
print >>ifp, '<div class="list-group">'
ifp += 1
for iface in sorted(ifaces.keys()):
	print >>ifp, '<a class="list-group-item list-group-item-action" href="ifaces.html#%s">' % iface
	print >>ifp, '<div class="progress" style="width: 100px"><div class="progress-bar bg-success progress-bar-striped" role="progressbar" aria-valuenow="%i" aria-valuemin="0" aria-valuemax="100" style="width: %i%%"></div></div>' % (ifaceCompleteness[iface], ifaceCompleteness[iface])
	print >>ifp, '%s</a>' % iface
ifp -= 1
print >>ifp, '</div>'

print >>ifp, '<h2 id="types">Types</h2>'
print >>ifp, '<div class="list-group">'
ifp += 1
for elem in sorted(types.keys()):
	print >>ifp, '<a class="list-group-item list-group-item-action" href="types.html#%s">%s</a>' % (elem, elem)
ifp -= 1
print >>ifp, '</div>'
ifp -= 1
print >>ifp, '</div>'

print >>ifp, '<div class="col-1">'
print >>ifp, '\t<nav id="toc" data-toggle="toc"></nav>'
print >>ifp, '</div>'
ifp -= 1
print >>ifp, '</div>'

print >>nfp, '<h1 class="display-3">SwIPC Interfaces</h1>'
print >>nfp, '<br />'
for name, iface in sorted(ifaces.items(), key=lambda x: x[0]):
	cmds = iface['cmds']
	print >>nfp, '<div class="card">'
	nfp += 1

	print >>nfp, '<div class="card-header">'
	print >>nfp, '\t<a href="#%s"><h2 id="%s">%s</h2></a>' % (name, name, name)
	print >>nfp, '</div>'
	print >>nfp, '<ul class="list-group list-group-flush">'
	nfp += 1

	print >>nfp, '<li class="list-group-item">'
	print >>nfp, '\t<div class="progress" style="width: 100px"><div class="progress-bar bg-success progress-bar-striped" role="progressbar" aria-valuenow="%i" aria-valuemin="0" aria-valuemax="100" style="width: %i%%"></div></div>' % (ifaceTotalCompleteness[name], ifaceTotalCompleteness[name])
	print >>nfp, '</li>'

	if name in services:
		print >>nfp, '<li class="list-group-item">'
		print >>nfp, '\t<h3>Provides:</h3>'
		print >>nfp, '\t<ul>'
		nfp += 2
		for x in sorted(services[name]):
			print >>nfp, '<li>%s</li>' % x
		nfp -= 2
		print >>nfp, '\t</ul>'
		print >>nfp, '</li>'
	if name in returnedBy:
		print >>nfp, '<li class="list-group-item">'
		print >>nfp, '\t<h3>Returned by:</h3>'
		print >>nfp, '\t<ul>'
		nfp += 2
		for x in sorted(returnedBy[name]):
			print >>nfp, '<li><a href="ifaces.html#%s(%i)">%s</a></li>' % (x[0], x[1], '%s::%s [%i]' % (x[0], findCmd(x[0], x[1])[0], x[1]))
		nfp -= 2
		print >>nfp, '\t</ul>'
		print >>nfp, '</li>'
	if name in takenBy:
		print >>nfp, '<li class="list-group-item">'
		print >>nfp, '\t<h3>Taken by:</h3>'
		print >>nfp, '\t<ul>'
		nfp += 2
		for x in sorted(takenBy[name]):
			print >>nfp, '<li><a href="ifaces.html#%s(%i)">%s</a></li>' % (x[0], x[1], '%s::%s [%i]' % (x[0], findCmd(x[0], x[1])[0], x[1]))
		nfp -= 2
		print >>nfp, '\t</ul>'
		print >>nfp, '</li>'

	if len(iface['doc']):
		print >>nfp, '<li class="list-group-item">'
		print >>nfp, '\t<div class="docs">%s</div>' % CommonMark.commonmark(iface['doc'])
		print >>nfp, '</li>'
	if len(iface['cmds']):
		print >>nfp, '<li class="list-group-item">'
		print >>nfp, '\t<h3>Commands:</h3>'
		print >>nfp, '\t<ol>'
		nfp += 2
		for cname, cmd in sorted(cmds.items(), key=lambda x: x[1]['cmdId']):
			urlId = "%s(%i)" % (name, cmd['cmdId'])
			cdef = '<a href="#%s">%s</a>(%s)%s' % (urlId, cname, format(cmd['inputs']), ' -&gt; %s' % format(cmd['outputs'], output=True) if len(cmd['outputs']) != 0 else '')
			print >>nfp,  '<li class="command" value="%i" id="%s">' % (cmd['cmdId'], urlId)
			print >>nfp, ('  <input type="checkbox" class="showDocs" id="showDocs(%s)"></input>' % (urlId)) if cmd['doc'] != "" else ""
			print >>nfp, ('  <label for="showDocs(%s)" class="showDocsLabel"></label>' % (urlId)) if cmd['doc'] != "" else ""
			print >>nfp,  '  <code class="signature">[%i] %s</code>' % (cmd['cmdId'], cdef)
			print >>nfp, ('  <div class="docs">%s</div>' % CommonMark.commonmark(cmd['doc'])) if cmd['doc'] != "" else ""
			print >>nfp,  '</li>'
		nfp -= 2
		print >>nfp, '\t</ol>'
		print >>nfp, '</li>'

	nfp -= 2
	print >>nfp, '\t</ul>'
	print >>nfp, '</div>'
	print >>nfp, '<br />'

print >>tfp, '<h1 class="display-3">SwIPC Types</h1>'
print >>tfp, '<br />'
print >>tfp, '<ul class="list-group">'
tfp += 1
for name, type in sorted(types.items(), key=lambda x: x[0]):
	print >>tfp, '<li class="list-group-item" id="%s">' % name
	print >>tfp, '\t<a href="#%s">+</a> %s <small class="text-muted">%s</small>' % (name, name, format([(None, type)]))
	print >>tfp, '</li>'
tfp -= 1
print >>tfp, '</ul>'

afp -= 3
print >>afp, '\t\t</div>'
print >>afp, '\t</body>'
print >>afp, '</html>'
