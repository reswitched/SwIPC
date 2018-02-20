import sys
sys.path.append('.')
import idparser

BUILTINS = {
	"bool": { "len": 1, "ctype": "int" },
	"u8": { "len": 1, "ctype": "uint8_t" },
	"i8": { "len": 4, "ctype": "int8_t" },
	"u16": { "len": 2, "ctype": "uint16_t" },
	"i16": { "len": 4, "ctype": "int16_t" },
	"u32": { "len": 4, "ctype": "uint32_t" },
	"i32": { "len": 4, "ctype": "int32_t" },
	"u64": { "len": 8, "ctype": "uint64_t" },
	"i64": { "len": 4, "ctype": "int64_t" },
	"u128": { "len": 16, "ctype": "uint128_t" }, # DERP
}

def camelToSnake(s):
	""" 
	Is it ironic that this function is written in camel case, yet it
	converts to snake case? hmm..
	"""
	import re
	_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
	_underscorer2 = re.compile('([a-z0-9])([A-Z])')
	subbed = _underscorer1.sub(r'\1_\2', s)
	return _underscorer2.sub(r'\1_\2', subbed).lower()

def ninty_to_c(s):
	return s.replace("-", "_").replace("::", "_").replace(":", "_")

def findCmd(ifname, id):
	for name, cmd in ifaces[ifname].items():
		if cmd['cmdId'] == id:
			return (name, cmd)
	return None

def emitInt(x):
	return '0x%x' % x if x > 9 else str(x)

def getType(output, t):
	if t[0] == 'array':
		pre, post = getType(output, t[1])
		return (pre, post + "[%s]" % emitInt(t[2]))
	elif t[0] == 'buffer':
		if t[1] == "unknown" and t[3] == 0:
			return [(("const " if not output else "") + "char *", None), ("size_t ", "_size")]
		elif t[1] == "unknown":
			return (("const " if not output else "") + "char ", "[" + emitInt(t[3]) + "]")
		else:
			# TODO: Ensure that t[3] == sizeof t[1]
			# TODO: output = false ? I mean this is handled right at
			# the start.
			pre, post = getType(False, t[1])
			return (("const " if not output else "") + pre + " *", post)
	elif t[0] == 'object':
				return ("ipc_object_t%s" % (" *" if output else ""), None)
		#it = t[1][0]
		#if it in ifaces:
		#	ret = 'object<%s>' % it
		#else:
				#		raise Exception("Unknown object %s" % it)
			#ret = it
	elif t[0] == 'KObject':
		return ('KObject', None)
	elif t[0] == 'align':
		return ('UNSUPPORTED', None)
	elif t[0] == 'bytes':
		return ("%suint8_t" % ("const " if not output else ""), "[%s]" % emitInt(t[1]))
	elif t[0] == 'pid':
		raise Exception("pid is not a valid type")
	elif t[0] in types:
		return (t[0], None)
	elif t[0] in BUILTINS:
		assert len(t) == 1
		return (BUILTINS[t[0]]['ctype'], None)
	else:
		raise Exception("Unknown Type")

def formatArgs(out_elems, in_elems, output=False):
	from functools import partial
	from itertools import chain
	if output and len(elems) > 1:
		return '(%s)' % format(elems)

	def sub(output, elem):
		idx, elem = elem
		name, elem = elem

		# pids aren't actual argument.
		if elem[0] == 'pid':
			return None

		if name is None and idx is not None:
			name = 'unk%s' % idx

		pre, post = getType(output, elem)

				# TODO: Check if elem is an array. If it is, it's actually
				# multiple arguments.
		assert pre is not None

		return '%s %s%s' % (ninty_to_c(pre), name, post if post is not None else "")

	return ', '.join(chain(filter(None, map(partial(sub, True), enumerate(out_elems))), filter(None, map(partial(sub, False), enumerate(in_elems)))))

def generate_input_code(name, ty, rawoffset, bufferlist):
	buf = ""
	if ty[0] == 'pid':
		buf += "\trq.send_pid = true;"
	elif ty[0] == 'buffer':
		buf += "\tipc_buffer_t %s_in_buf = {\n" % name
		buf += "\t\t.addr = %s,\n" % name
		buf += "\t\t.size = %s,\n" % (ty[3] if ty[3] != 0 else (name + "_size"))
		buf += "\t\t.type = %s,\n" % ty[2]
		buf += "\t};"
		bufferlist.append("%s_in_buf" % name)
	elif ty[0] == 'KObject':
		buf += "KObject %s NOTSUPPORTED" % name
	elif ty[0] == 'align':
		buf += "align %s NOTSUPPORTED" % name
	elif ty[0] == 'bytes':
		buf += "\tmemcpy(rq.raw_data + %d, %s, %d);" % (rawoffset, name, ty[1])
		rawoffset += ty[1]
	elif ty[0] in types:
		#print("\tmemcpy(raw + %d, %s, sizeof(%s));" % (rawoffset, name, ninty_to_c(ty[0])))
		return generate_input_code(name, types[ty[0]], rawoffset, bufferlist)
	elif ty[0] in BUILTINS:
		buf += "\t*(%s*)(rq.raw_data + %d) = %s;" % (BUILTINS[ty[0]]["ctype"], rawoffset, name)
		rawoffset += BUILTINS[ty[0]]["len"]
	else:
		raise Exception("Unknown type %s" % ty[0])
	return (buf, rawoffset)

def generate_output_code(name, ty, objectlen, rawoffset, objectoffset, bufferlist):
	buf_pre = ""
	buf_post = ""
	if ty[0] == 'buffer':
		buf_pre += "\tipc_buffer_t %s_out_buf = {\n" % name
		buf_pre += "\t\t.addr = %s,\n" % name
		buf_pre += "\t\t.size = %s,\n" % (ty[3] if ty[3] != 0 else (name + "_size"))
		buf_pre += "\t\t.type = %s,\n" % ty[2]
		buf_pre += "\t};"
		bufferlist.append("%s_out_buf" % name)
	elif ty[0] == 'object':
		if objectlen == 1 and objectoffset == 0:
			buf_pre += "\trs.objects = %s;\n" % name
			buf_pre += "\trs.num_objects = 1;"
		elif objectlen > 1:
			buf_post += "\t*%s = rs.objects[%d];" % (name, objectoffset)
		else:
			raise Exception("Weird bug happened !")
		objectoffset += 1
	elif ty[0] == 'KObject':
		buf_pre += "KObject %s NOTSUPPORTED" % name
	elif ty[0] == 'align':
		buf_pre += "align %s NOTSUPPORTED" % name
	elif ty[0] == 'array':
		buf_pre += "array %s NOTSUPPORTED" % name
	elif ty[0] == 'bytes':
		buf_pre += "\tmemcpy(%s, rs.raw_data + %d, %d);" % (name, rawoffset, ty[1])
		rawoffset += ty[1]
	elif ty[0] in types:
		#print("\tmemcpy(raw + %d, %s, sizeof(%s));" % (rawoffset, name, ninty_to_c(ty[0])))
		return generate_output_code(name, types[ty[0]], objectlen, rawoffset, objectoffset, bufferlist)
	elif ty[0] in BUILTINS:
		buf_pre += "\t*%s = (%s)(rs.raw_data + %d);" % (name, BUILTINS[ty[0]]["ctype"], rawoffset)
		rawoffset += BUILTINS[ty[0]]["len"]
	else:
		raise Exception("Unknown type %s" % ty[0])
	return (buf_pre, buf_post, rawoffset, objectoffset)

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

import argparse

parser = argparse.ArgumentParser(description='Generate libtransistor ipc functions')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', action='store', type=str, help='Name of the service to codegen. Example: nifm:u')
group.add_argument('-i', action='store', type=str, help='Name of the interface to codegen. Example: nn::fssrv::sf::IFileSystemProxy')

parser.add_argument('-n', action='store', type=str, help='Name of the prefix to use. Defaults to a c-ified version of the interface/service name.')
prog_args = parser.parse_args()

name = prog_args.i or prog_args.s
ifacename = name
c_ifacename = prog_args.n or ninty_to_c(ifacename)

if prog_args.s:
	iface = ifaces[invServices[prog_args.s]]
else:
	iface = ifaces[prog_args.i]

def gen_init():
	cmd = iface.get('Initialize')
	args = "void" if cmd is None else formatArgs(cmd['outputs'], cmd['inputs'])

	print("result_t %s_init(%s) {" % (c_ifacename, args))
	print("\tif(%s_initializations++ > 0) {" % c_ifacename)
	print("\t\treturn RESULT_OK;")
	print("\t}")
	print("")
	print("\tresult_t res;")
	print("\tres = sm_init();")
	print("\tif (res != RESULT_OK) {")
	print("\t\tgoto fail;")
	print("\t}")
	print("")
	print("\tres = sm_get_service(&%s_object, \"%s\");" % (c_ifacename, ifacename))
	print("\tif (res != RESULT_OK) {")
	print("\t\tgoto fail_sm;")
	print("\t}")
	print("")
	print("\tsm_finalize();")
	if cmd is not None:
		print("")
		gen_ipc_method(cmd)
		print("\tif (res != RESULT_OK) {")
		print("\t\tgoto fail;")
		print("\t}")
	print("\treturn RESULT_OK;")
	print("fail_sm:")
	print("\tsm_finalize();")
	print("fail:")
	print("\t%s_initializations--;" % c_ifacename)
	print("\treturn res;")
	print("}")

def gen_finalize():
	# force_finalize
	print("static void %s_force_finalize() {" % c_ifacename)
	print("\tipc_close(%s_object);" % c_ifacename)
	print("\t%s_initializations = 0;" % c_ifacename)
	print("}")

	# finalize
	print("void %s_finalize() {" % c_ifacename)
	print("\tif(--%s_initializations == 0) {" % c_ifacename)
	print("\t\t%s_force_finalize();" % c_ifacename)
	print("\t}")
	print("}")

	# destructor
	print("static __attribute__((destructor)) void %s_destruct() {" % c_ifacename)
	print("\tif(%s_initializations > 0) {" % c_ifacename)
	print("\t\t%s_force_finalize();" % c_ifacename)
	print("\t}")
	print("}")


def gen_ipc_method(cmd):
	print("\tipc_request_t rq = ipc_default_request;")
	print("\tipc_response_fmt_t rs = ipc_default_response_fmt;")
	print("\trq.request_id = %d;" % cmd['cmdId'])

	print("")

	bufferlist = []
	rawoffset = 0
	buf = ""
	for (idx, (name, ty)) in enumerate(cmd['inputs']):
		if name is None:
			name = 'unk%s' % idx
		tmpbuf, rawoffset = generate_input_code(name, ty, rawoffset, bufferlist)
		buf += tmpbuf + "\n"

	if rawoffset != 0:
		print("\tuint8_t raw[%d];" % rawoffset)
		print("\trq.raw_data = raw;")
		print("\trq.raw_data_size = %d;" % rawoffset)
		print("")

	if buf != "":
		print(buf)
		print("")

	rawoffset = 0
	bufpre = ""
	bufpost = ""
	objectoffset = 0
	objectlen = 1
	for (idx, (name, ty)) in enumerate(cmd['outputs']):
		if name is None:
			name = 'unk%s' % (idx + len(cmd['inputs']))
		tmpbufpre, tmpbufpost, rawoffset, objectoffset = generate_output_code(name, ty, objectlen, rawoffset, objectoffset, bufferlist)
		bufpre += tmpbufpre + "\n"
		bufpost += tmpbufpost + "\n"

	if rawoffset != 0:
		print("\tuint8_t output_raw[%d];" % rawoffset)
		print("\trs.raw_data = output_raw;")
		print("\trs.raw_data_size = %d;" % rawoffset)

	if objectlen > 1:
		print("\tipc_object_t objects[%d];" % objectlen)
		print("\trs.objects = objects;")
		print("\trs.num_objects = %d;" % objectlen)

	if rawoffset != 0 or objectlen > 1 or len(bufferlist) > 0:
		print("")

	if bufpre != "":
		print(bufpre)
		print("")

	if len(bufferlist) > 0:
		print("\tipc_buffer_t *buffers[] = {")
		print(",\n".join(["\t\t&%s" % buf for buf in bufferlist]))
		print("\t};")
		print("\trq.num_buffers = %d;" % len(bufferlist))
		print("\trq.buffers = buffers;")

	print("\tres = ipc_send(%s_object, &rq, &rs);" % c_ifacename)

	if bufpost != "":
		print(bufpost)

print("static ipc_object_t %s_object;" % c_ifacename)
print("static int %s_initializations = 0;" % c_ifacename)
gen_init()
gen_finalize()
for cname, cmd in sorted(iface.items(), key=lambda x: x[1]['cmdId']):
	if cname == "Initialize":
		continue
	print("result_t %s_%s(%s) {" % (c_ifacename, camelToSnake(cname), formatArgs(cmd['outputs'], cmd['inputs'])))
	print("\tresult_t res;")
	gen_ipc_method(cmd)
	print("\treturn res;")
	print("}")
