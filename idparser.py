import sys, tatsu
import glob, json, os.path

grammar = '''
start = { def }+ $ ;

number
	=
	| /0x[0-9a-fA-F]+/
	| /[0-9]+/
	;

def
	=
	| typeDef
	| interface
	;

expression
	=
	| type
	| number
	;

name = /[a-zA-Z_][a-zA-Z0-9_:]*/ ;
sname = /[a-zA-Z_][a-zA-Z0-9_:\-]*/ ;
serviceNameList = @:','.{ sname } ;
template = '<' @:','.{ expression } '>' ;
structField = type [ name ] ';' ;
type =
    | 'struct' '{' structFields:{ structField }+ '}'
    | name:name template:[ template ]
    ;

typeDef = 'type' name:name '=' type:type ';' ;

interface = doc:{ comment }* 'interface' name:name [ 'is' serviceNames:serviceNameList ] '{' functions:{ funcDef }* '}' ;
namedTuple = '(' @:','.{ type [ name ] } ')' ;
namedType = type [ name ] ;
comment = '#' line:/[^\\n]*/;
funcDef = doc:{ comment }* '[' cmdId:number ']' name:name inputs:namedTuple [ '->' outputs:( namedType | namedTuple ) ] ';' ;
'''

class Semantics(object):
	def number(self, ast):
		if ast.startswith('0x'):
			return int(ast[2:], 16)
		return int(ast)

	def namedTuple(self, ast):
		return [elem if isinstance(elem, list) else [elem, None] for elem in ast]

	def namedType(self, ast):
		return [ast if isinstance(ast, list) else [ast, None]]

def parseType(type):
	if not isinstance(type, tatsu.ast.AST) or 'template' not in type or 'structFields' not in type:
		return type
	assert(not(type['template'] is not None and type['structFields'] is not None))
	name, template, structFields = type['name'], type['template'], type['structFields']
	if template is not None:
		return [name] + map(parseType, template)
	elif structFields is not None:
		return ["struct"] + map(lambda x: [x[1], parseType(x[0])], structFields)
	else:
		return [name]

def parse(data):
	ast = tatsu.parse(grammar, data, semantics=Semantics(), eol_comments_re=r'\/\/.*?$')

	types = {}
	for elem in ast:
		if 'type' not in elem:
			continue
		#assert elem['name'] not in types
		types[elem['name']] = parseType(elem['type'])

	ifaces = {}
	services = {}
	for elem in ast:
		if 'functions' not in elem:
			continue
		#assert elem['name'] not in ifaces
		ifaces[elem['name']] = iface = { "doc": "", "cmds": {}}
		if elem['serviceNames']:
			services[elem['name']] = list(elem['serviceNames'])
		iface['doc'] = "\n".join(map(lambda x: x.line, elem['doc']))
		for func in elem['functions']:
			if func['name'] in iface:
				print >>sys.stderr, 'Duplicate function %s in %s' % (func['name'], elem['name'])
				sys.exit(1)

			assert func['name'] not in iface
			iface['cmds'][func['name']] = fdef = {}
			fdef['cmdId'] = func['cmdId']
			fdef['doc'] = "\n".join(map(lambda x: x.line, func['doc']))
			fdef['inputs'] = [(name, parseType(type)) for type, name in func['inputs']]
			if func['outputs'] is None:
				fdef['outputs'] = []
			elif isinstance(func['outputs'], tatsu.ast.AST):
				fdef['outputs'] = [(None, parseType(func['outputs']))]
			else:
				fdef['outputs'] = [(name, parseType(type)) for type, name in func['outputs']]

	return types, ifaces, services

def getAll():
	dir = os.path.dirname(os.path.realpath(__file__)) + '/'
	fns = [dir + 'ipcdefs/auto.id'] + [x for x in glob.glob(dir + 'ipcdefs/*.id') if x != dir + 'ipcdefs/auto.id']

	if os.path.exists(dir + 'ipcdefs/cache') and all(os.path.getmtime(dir + 'ipcdefs/cache') > os.path.getmtime(x) for x in fns):
		res = json.load(file(dir + 'ipcdefs/cache'))
	else:
		res = parse('\n'.join(file(fn).read() for fn in fns))
		with file(dir + 'ipcdefs/cache', 'w') as fp:
			json.dump(res, fp)
	return res
