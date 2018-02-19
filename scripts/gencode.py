import sys
sys.path.append('.')
import idparser

BUILTINS = {
    "u8": { "len": 1, "ctype": "uint8_t" },
    "u16": { "len": 2, "ctype": "uint16_t" },
    "u32": { "len": 4, "ctype": "uint32_t" },
    "u64": { "len": 8, "ctype": "uint64_t" },
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

def formatArgs(out_elems, in_elems, output=False):
        from functools import partial
	if output and len(elems) > 1:
		return '(%s)' % format(elems)

	def sub(output, elem):
		idx, elem = elem
		name, elem = elem
		ret = None

                if name is None and idx is not None:
                    name = 'unk%s' % idx

		if elem[0] == 'array':
			ret = 'array<%s, %s>' % (sub(output, (idx, (None, elem[1]))), emitInt(elem[2]))
		elif elem[0] == 'buffer':
                        if elem[3] == 0:
                                return sub(True, (None, (name, elem[1]))) + ", " + sub(output, (None, (name + "_size", ["u64"])))
                        else:
			        ret = 'buffer<%s, %s, %s>' % (sub(output, (None, (None, elem[1]))), emitInt(elem[2]), emitInt(elem[3]))
		elif elem[0] == 'object':
                        ret = "ipc_object_t"
			#it = elem[1][0]
			#if it in ifaces:
			#	ret = 'object<%s>' % it
			#else:
                        #        raise Exception("Unknown object %s" % it)
				#ret = it
		elif elem[0] == 'KObject':
			ret = 'KObject'
		elif elem[0] == 'align':
			ret = 'align<%s, %s>' % (emitInt(elem[1]), sub(output, (None, (None, elem[2]))))
		elif elem[0] == 'bytes':
			ret = '%suint8_t %s[%s]' % ("const " if not output else "", name, emitInt(elem[1]))
                        name = None
                elif elem[0] == 'pid':
                        return ''
		elif elem[0] in types:
			ret = elem[0]
                elif elem[0] in BUILTINS:
			assert len(elem) == 1
			ret = BUILTINS[elem[0]]['ctype']
                else:
			assert len(elem) == 1
			ret = elem[0]

		assert ret is not None

		if name:
			return '%s %s%s' % (ninty_to_c(ret), "*" if output else "", name)
		else:
			return ret

	return ', '.join(filter(None, map(partial(sub, True), enumerate(out_elems))) + filter(None, map(partial(sub, False), enumerate(in_elems))))

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
        #print "\tmemcpy(raw + %d, %s, sizeof(%s));" % (rawoffset, name, ninty_to_c(ty[0]))
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
            buf_pre += "\trs.objects = %s;" % name
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
    elif ty[0] == 'bytes':
        buf_pre += "\tmemcpy(%s, rs.raw_data + %d, %d);" % (name, rawoffset, ty[1])
        rawoffset += ty[1]
    elif ty[0] in types:
        #print "\tmemcpy(raw + %d, %s, sizeof(%s));" % (rawoffset, name, ninty_to_c(ty[0]))
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

if len(sys.argv) < 2:
    print "Usage: %s <servicename>" % sys.argv[0]
    exit()

ifacename = sys.argv[1]
c_ifacename = ninty_to_c(ifacename)
iface = ifaces[invServices[ifacename]]

def gen_init():
    cmd = iface.get('Initialize')
    args = "void" if cmd is None else formatArgs(cmd['outputs'], cmd['inputs'])

    print "result_t %s_init(%s) {" % (c_ifacename, args)
    print "\tif(%s_initializations++ > 0) {" % c_ifacename
    print "\t\treturn RESULT_OK;"
    print "\t}"
    print ""
    print "\tresult_t res;"
    print "\tres = sm_init();"
    print "\tif (res != RESULT_OK) {"
    print "\t\tgoto fail;"
    print "\t}"
    print ""
    print "\tres = sm_get_service(&%s_object, \"%s\");" % (c_ifacename, ifacename)
    print "\tif (res != RESULT_OK) {"
    print "\t\tgoto fail_sm;"
    print "\t}"
    print ""
    print "\tsm_finalize();"
    if cmd is not None:
        print ""
        gen_ipc_method(cmd)
        print "\tif (res != RESULT_OK) {"
        print "\t\tgoto fail;"
        print "\t}"
    print "\treturn RESULT_OK;"
    print "fail_sm:"
    print "\tsm_finalize();"
    print "fail:"
    print "\t%s_initializations--;" % c_ifacename
    print "\treturn res;"
    print "}"

def gen_finalize():
    # force_finalize
    print "static void %s_force_finalize() {" % c_ifacename
    print "\tipc_close(%s_object);" % c_ifacename
    print "\t%s_initializations = 0;" % c_ifacename
    print "}"

    # finalize
    print "void %s_finalize() {" % c_ifacename
    print "\tif(--%s_initializations == 0) {" % c_ifacename
    print "\t\t%s_force_finalize();" % c_ifacename
    print "\t}"
    print "}"

    # destructor
    print "static __attribute__((destructor)) void %s_destruct() {" % c_ifacename
    print "\tif(%s_initializations > 0) {" % c_ifacename
    print "\t\t%s_force_finalize();" % c_ifacename
    print "\t}"
    print "}"


def gen_ipc_method(cmd):
    print "\tipc_request_t rq = ipc_default_request;"
    print "\tipc_response_fmt_t rs = ipc_default_response_fmt;"
    print "\trq.request_id = %d;" % cmd['cmdId']

    print ""

    bufferlist = []
    rawoffset = 0
    buf = ""
    for (idx, (name, ty)) in enumerate(cmd['inputs']):
        if name is None:
            name = 'unk%s' % idx
        tmpbuf, rawoffset = generate_input_code(name, ty, rawoffset, bufferlist)
        buf += tmpbuf + "\n"

    if rawoffset != 0:
        print "\tuint8_t raw[%d];" % rawoffset
        print "\trq.raw_data = raw;"
        print "\trq.raw_data_size = %d;" % rawoffset
        print ""

    if buf != "":
        print buf
        print ""

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
        print "\tuint8_t output_raw[%d];" % rawoffset
        print "\trs.raw_data = output_raw;"
        print "\trs.raw_data_size = %d;" % rawoffset

    if objectlen > 1:
        print "\tipc_object_t objects[%d];" % objectlen
        print "\trs.objects = objects;"
        print "\trs.num_objects = %d;" % objectlen

    if rawoffset != 0 or objectlen > 1 or len(bufferlist) > 0:
        print ""

    if bufpre != "":
        print bufpre
        print ""

    if len(bufferlist) > 0:
        print "\tipc_buffer_t *buffers[] = {"
        print ",\n".join(["\t\t&%s" % buf for buf in bufferlist])
        print "\t};"
        print "\trq.num_buffers = %d;" % len(bufferlist)
        print "\trq.buffers = buffers;"

    print "\tres = ipc_send(%s_object, &rq, &rs);" % c_ifacename

    if bufpost != "":
        print bufpost

print "static ipc_object_t %s_object;" % c_ifacename
print "static int %s_initializations = 0;" % c_ifacename
gen_init()
gen_finalize()
for cname, cmd in sorted(iface.items(), key=lambda x: x[1]['cmdId']):
    if cname == "Initialize":
        continue
    print "result_t %s_%s(%s) {" % (c_ifacename, camelToSnake(cname), formatArgs(cmd['outputs'], cmd['inputs']))
    print "\tresult_t res;"
    gen_ipc_method(cmd)
    print "\treturn res;"
    print "}"
