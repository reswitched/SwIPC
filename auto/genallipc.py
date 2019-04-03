import hashlib, random, re
from info import info
from serverInfo import serverInfo
from clientInfo import clientInfo
from smapping import smapping

clsToInterface = {}
for x in smapping.values():
	for k, v in x.items():
		if v not in clsToInterface:
			clsToInterface[v] = []
		clsToInterface[v].append(k)

clses = {}
for cname, cmdid, name, io, params in info:
	if cname not in clses:
		clses[cname] = {}
	#if params != '':
	clses[cname][cmdid] = name, io, params

reformedServer = {}
reformedClient = {}

for cname, cmds in serverInfo.items():
	if cname not in reformedServer:
		reformedServer[cname] = {}
	for cmdid, cmd in cmds.items():
		cmdid = int(cmdid)
		reformedServer[cname][cmdid] = cmd['name'] if 'name' in cmd else '', '', cmd['args'] if 'args' in cmd else ''

for cname, cmdid, io in clientInfo:
	if cname not in reformedClient:
		reformedClient[cname] = {}
	reformedClient[cname][cmdid] = '', io, ''

mset = lambda x: set((cname, cmdid) for cname, cmds in x.items() for cmdid in cmds.keys())
allCmds = mset(reformedClient).union(mset(reformedServer))
for cname, cmdid in allCmds:
	cdef = reformedClient[cname][cmdid] if cname in reformedClient and cmdid in reformedClient[cname] else None
	sdef = reformedServer[cname][cmdid] if cname in reformedServer and cmdid in reformedServer[cname] else None

	if cdef is not None and sdef is None:
		idef = cdef
	elif cdef is None and sdef is not None:
		idef = sdef
	else:
		idef = sdef[0], cdef[1], sdef[2]

	if idef[1] == '':
		idef = idef[0], 'UNK bytes in - UNK bytes out', idef[2]

	if cname not in clses:
		clses[cname] = {}

	if cmdid in clses[cname]:
		cur = clses[cname][cmdid]
		if cur == idef:
			continue
		cur = list(cur)
		for i in xrange(3):
			if len(cur[i]) < len(idef[i]):
				cur[i] = idef[i]
		clses[cname][cmdid] = tuple(cur)
	else:
		clses[cname][cmdid] = idef

def parseAnyInt(x):
	return int(x[2:], 16) if x.startswith('0x') else int(x)

def emitInt(x):
	return '0x%x' % x if x > 9 else str(x)

def csplit(inp):
	def findMatch(i, ch):
		while i < len(inp):
			mch = inp[i]
			if mch == ch:
				return i
			elif mch == '<':
				i = findMatch(i + 1, '>')
			elif mch == '(':
				i = findMatch(i + 1, ')')
			elif mch == '[':
				i = findMatch(i + 1, ']')
			i += 1
	out = []
	i = 0
	last = 0
	while i < len(inp):
		mch = inp[i]
		if mch == ',':
			if i != last:
				out.append(inp[last:i].strip(' ,'))
				last = i
		elif mch == '<':
			i = findMatch(i + 1, '>')
		elif mch == '(':
			i = findMatch(i + 1, ')')
		elif mch == '[':
			i = findMatch(i + 1, ']')
		i += 1
	if last != i:
		out.append(inp[last:i].strip(' ,'))
	return out

def splitIOSpec(cs):
	ins, outs = [], []

	for elem in cs:
		if elem.startswith('InRaw<'):
			ins.append(elem)
		elif elem.startswith('OutRaw<'):
			outs.append(elem)
		elif elem.startswith('Buffer<'):
			btype = parseAnyInt(elem.split(',')[1])
			if btype & 1:
				ins.append(elem)
			else:
				assert btype & 2
				outs.append(elem)
		elif elem.startswith('InObject<'):
			ins.append(elem)
		elif elem.startswith('OutObject<'):
			outs.append(elem)
		elif elem.startswith('InHandle<'):
			ins.append(elem)
		elif elem.startswith('OutHandle<'):
			outs.append(elem)
		else:
			print elem
			assert False

	return ins, outs

def splitIOParams(params):
	ins, outs = [], []

	for elem in params:
		if elem.startswith('nn::sf::Out<nn::sf::SharedPointer<'):
			outs.append(elem)
		elif elem.startswith('nn::sf::Out<'):
			outs.append(elem)
		elif elem.startswith('nn::sf::OutBuffer'):
			outs.append(elem)
		elif elem.startswith('nn::sf::OutArray<'):
			outs.append(elem)
		elif elem.startswith('nn::sf::InBuffer'):
			ins.append(elem)
		elif elem.startswith('nn::sf::InArray<'):
			ins.append(elem)
		else:
			assert not elem.startswith('nn::sf::Out') and not elem.startswith('nn::sf::In')
			ins.append(elem)

	return [x.replace('  ', ' ').replace(' &', '&') for x in ins], [x.replace('  ', ' ').replace(' &', '&') for x in outs]

def parseSpecType(type):
	a, b = type[:-1].split('<')
	return [a] + [parseAnyInt(x.strip()) for x in b.split(',')]

intTypes = {
	'bool' : 'bool', 
	'unsigned char' : 'u8', 
	'char' : 'i8', 
	'signed char' : 'i8', 
	'int' : 'i32', 
	'unsigned int' : 'u32', 
	'long' : 'i64', 
	'unsigned long' : 'u64', 
	'float' : 'f32', 
}

def remapProtoType(type, stype):
	type = type.replace('const&', '')
	if type.startswith('nn::sf::Out<'):
		type = csplit(type.split('nn::sf::Out<', 1)[1])[0]
	elif type.startswith('nn::sf::OutArray<'):
		type = type.split('nn::sf::OutArray<', 1)[1].split('>', 1)[0] + '[]'
	elif type.startswith('nn::sf::InArray<'):
		type = type.split('nn::sf::InArray<', 1)[1].split('>', 1)[0] + '[]'
	elif type.startswith('nn::sf::InBuffer'):
		type = 'unknown'

	type = type.strip()

	if type.startswith('nn::sf::SharedPointer<'):
		type = type.split('nn::sf::SharedPointer<', 1)[1].split('>', 1)[0]
	elif type.startswith('nn::sf::NativeHandle'):
		type = 'KObject'
	elif type.startswith('nn::util::BitFlagSet<'):
		type = csplit(type.split('nn::util::BitFlagSet<', 1)[1][:-1])[1]

	type = type.strip()

	if type in intTypes:
		type = intTypes[type]
	elif type.endswith('[]') and type[:-2] in intTypes:
		type = intTypes[type[:-2]] + '[]'

	stype = parseSpecType(stype)
	
	if stype[0] == 'OutObject' or stype[0] == 'InObject':
		return 'object', type
	elif stype[0] == 'InRaw' or stype[0] == 'OutRaw':
		_, size, alignment, offset = stype
		return 'data', type, size, alignment, offset
	elif stype[0] == 'Buffer':
		if type.endswith('[]'):
			type = type[:-2]
			assert stype[3] == 0
			return 'array', type, stype[2]
		else:
			type = 'unknown' if type == 'nn::sf::OutBuffer' else type
			return 'buffer', type, stype[2], stype[3]
	elif stype[0] == 'InHandle' or stype[0] == 'OutHandle':
		assert type == 'KObject'
		return 'handle', 

defaultTypes = {
	-1: 'unknown', 
	1: 'u8', 
	2: 'u16', 
	4: 'u32', 
	8: 'u64', 
	16: 'u128'
}

def emitDefaultOrBytes(size):
	if size in defaultTypes:
		return defaultTypes[size]
	return 'bytes<%s>' % emitInt(size)

def generateType(stype):
	stype = parseSpecType(stype)

	if stype[0] == 'InHandle' or stype[0] == 'OutHandle':
		return 'handle', 
	elif stype[0] == 'InObject' or stype[0] == 'OutObject':
		return 'object', None
	elif stype[0] == 'InRaw' or stype[0] == 'OutRaw':
		_, size, alignment, offset = stype
		return 'data', emitDefaultOrBytes(size), size, alignment, offset
	elif stype[0] == 'Buffer':
		return 'buffer', None, stype[2], stype[3]

dataSizes = {}
bufferTypes = set()
def defineSizes(types):
	for elem in types:
		if (elem[0] == 'buffer' or elem[0] == 'array') and elem[1] is not None:
			bufferTypes.add(elem[1])
			continue
		elif elem[0] != 'data':
			continue
		elif elem[1] in dataSizes:
			assert dataSizes[elem[1]] == elem[2]
			continue
		dataSizes[elem[1]] = elem[2]

def sortTyped(typed):
	return sorted(typed, key=lambda x: dict(data=0, pid=1, handle=2, object=3, buffer=4, array=4)[x[0]])

def sortData(elems):
	data = [elem for elem in elems if elem[0] == 'data']
	data.sort(key=lambda x: x[4])

	return data + elems[len(data):]

def filterAlignment(elems):
	cur = 0
	for i, elem in enumerate(elems):
		if elem[0] != 'data':
			break

		_, type, size, alignment, offset = elem

		calcAlign = min(size, 8)

		before = cur
		while cur % calcAlign:
			cur += 1

		if offset != cur:
			cur = before
			while cur % alignment:
				cur += 1
			elems[i] = 'data', type, size, alignment
		else:
			elems[i] = 'data', type, size, None
		#assert offset == cur
		cur += size
	return elems

def parseFunc(cs, params, pid):
	cs, params = csplit(cs), csplit(params[1:-1]) if params else []

	assert not params or len(cs) == len(params)

	si, so = splitIOSpec(cs)
	if params:
		pi, po = splitIOParams(params)
		assert len(si) == len(pi) and len(so) == len(po)
		pi, po = [remapProtoType(x, si[i]) for i, x in enumerate(pi)], [remapProtoType(x, so[i]) for i, x in enumerate(po)]

		defineSizes(pi + po)
	else:
		pi, po = map(generateType, si), map(generateType, so)

	if pid:
		pi = [('pid', )] + pi

	return filterAlignment(sortData(sortTyped(pi))), filterAlignment(sortData(sortTyped(po)))

ifaces = {}
for cname, functions in clses.items():
	assert cname not in ifaces
	ifaces[cname] = iface = {}
	for cmdId, func in functions.items():
		fname, spec, params = func
		if fname == '':
			fname = 'Unknown%i' % cmdId
		spec = spec.split(' - ')
		if len(spec) == 2 and spec[0] == 'UNK bytes in' and spec[1] == 'UNK bytes out':
			iface[cmdId] = (fname, (), (), False)
		elif len(spec) == 2 or (len(spec) == 3 and spec[2] == 'takes pid'):
			assert spec[0] == '0 bytes in' and spec[1] == '0 bytes out'
			iface[cmdId] = (fname, (['pid'], ) if len(spec) == 3 else (), (), True)
		elif len(spec) == 3 or (len(spec) == 4 and spec[2] == 'takes pid'):
			if spec[2] == 'takes pid':
				pid = True
				cs = spec[3]
			else:
				pid = False
				cs = spec[2]

			ins, outs = parseFunc(cs, params, pid)
			iface[cmdId] = fname, ins, outs, True

for elem in bufferTypes:
	if elem not in dataSizes:
		dataSizes[elem] = -1

with file('ipcdefs/auto.id', 'w') as fp:
	lastNs = -1
	for name, size in sorted(dataSizes.items(), key=lambda x: x[0]):
		if name not in intTypes.values() and name != 'void' and name != 'unknown':
			ns = name.rsplit('::', 1)[0] if '::' in name else None
			if ns != lastNs and lastNs != -1:
				print >>fp
			print >>fp, 'type %s = %s;' % (name, emitDefaultOrBytes(size))
			lastNs = ns

	print >>fp
	print >>fp

	def emitType(type):
		if type[0] == 'data':
			if type[3] is not None:
				return 'align<%i, %s>' % (type[3], type[1])
			return type[1] # XXX: Add alignment setup
		elif type[0] == 'object':
			return 'object<%s>' % (type[1] if type[1] else 'IUnknown')
		elif type[0] == 'handle':
			return 'KObject'
		elif type[0] == 'array':
			return 'array<%s, %s>' % (type[1], emitInt(type[2]))
		elif type[0] == 'buffer':
			return 'buffer<%s, %s, %s>' % (type[1] or 'unknown', emitInt(type[2]), emitInt(type[3]))
		elif type[0] == 'pid':
			return 'pid'
		else:
			print 'wtf?', type

	def emitFunction(cmdId, fname, ins, outs, documented):
		outstr = ''
		if documented:
			if len(outs) == 1:
				outstr = ' -> %s' % emitType(outs[0])
			elif len(outs):
				outstr = ' -> (%s)' % ', '.join(emitType(x) for x in outs)
			return '[%i] %s(%s)%s;' % (cmdId, fname, ', '.join(emitType(x) for x in ins), outstr)
		else:
			return '@undocumented\n\t[%i] %s();' % (cmdId, fname)

	for cname, cmds in sorted(ifaces.items(), key=lambda x: x[0]):
		print >>fp, 'interface %s%s {' % (cname, ' is ' + ', '.join(clsToInterface[cname]) if cname in clsToInterface else '')
		for cmdId, (fname, ins, outs, documented) in sorted(cmds.items(), key=lambda x: x[0]):
			print >>fp, '\t' + emitFunction(cmdId, fname, ins, outs, documented)
		print >>fp, '}'
		print >>fp
