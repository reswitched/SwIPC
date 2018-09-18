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
arrayLength = '[' [ length:number ] ']' ;
structField = doc:{ comment }* type:type name:name ';' ;
enumField = doc:{ comment }* name:name '=' value:number ';' ;
type =
    | 'struct' template:[ template ] '{' structFields:{ structField }+ '}'
    | 'enum' template:template '{' enumFields:{ enumField }+ '}'
    | name:name template:[ template ] length:[ arrayLength ]
    ;

typeDef = doc:{ comment }* decorators:{ decorator }* 'type' name:type '=' type:type ';' ;

interface = doc:{ comment }* decorators:{ decorator }* 'interface' name:name [ 'is' serviceNames:serviceNameList ] '{' functions:{ funcDef }* '}' ;
namedTuple = '(' @:','.{ type [ name ] } ')' ;
namedType = type [ name ] ;
comment = '#' line:/[^\\n]*/;
range = [start:(number '.' number '.' number)] '-' [end:(number '.' number '.' number)] ;
decorator = '@' @:decoratorType ;
versionNumber = number '.' number '.' number ;
decoratorType
	=
	| type:'version' '(' startVersion:versionNumber postfix:[('+' | '-' endVersion:versionNumber)] ')'
	| type:'undocumented'
	;

funcDef = doc:{ comment }* decorators:{ decorator }* '[' cmdId:number ']' name:name inputs:namedTuple [ '->' outputs:( namedType | namedTuple ) ] ';' ;
'''

versionInfo = [ '1.0.0', '2.0.0', '2.1.0', '2.2.0', '2.3.0', '3.0.0', '3.0.1', '3.0.2', '4.0.0', '4.0.1', '4.1.0', '5.0.0', '5.0.1', '5.0.2', '5.1.0']

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
	if not isinstance(type, tatsu.ast.AST) or 'template' not in type or 'structFields' not in type or 'enumFields' not in type:
		return type
	assert(not(type['template'] is not None and type['structFields'] is not None and type['enumFields'] is not None))
	name, template, structFields, enumFields = type['name'], type['template'], type['structFields'], type['enumFields']
	if structFields is not None:
		return ["struct"] + [list(map(lambda x: [x['name'], parseType(x['type']), list(map(lambda x: x.line, x['doc']))], structFields))]
	elif enumFields is not None:
		return ["enum"] + [list(map(lambda x: [x['name'], x['value'], list(map(lambda x: x.line, x['doc']))], enumFields))] + [template[0]['name']]
	elif template is not None:
		return [name] + list(map(parseType, template))
	else:
		return [name]

def repack(x):
	if isinstance(x, list):
		if len(x) > 1:
			return '%s<%s>' % (x[0], ", ".join(map(repack, x[1:])))
		else:
			return str(x[0])
	else:
		return str(x)

def parse(data):
	ast = tatsu.parse(grammar, data, semantics=Semantics(), eol_comments_re=r'\/\/.*?$')

	types = {}
	for elem in ast:
		if 'type' not in elem:
			continue
		#assert elem['name'] not in types
		tdef = {}
		types[repack(parseType(elem['name']))] = parseType(elem['type'])

	ifaces = {}
	services = {}
	for elem in ast:
		if 'functions' not in elem:
			continue
		#assert elem['name'] not in ifaces
		ifaces[elem['name']] = iface = { "doc": "", "cmds": []}
		if elem['serviceNames']:
			services[elem['name']] = list(elem['serviceNames'])
		iface['doc'] = "\n".join(map(lambda x: x.line, elem['doc']))
		for func in elem['functions']:
			if func['name'] in iface:
				print >>sys.stderr, 'Duplicate function %s in %s' % (func['name'], elem['name'])
				sys.exit(1)

			assert func['name'] not in iface
			fdef = {}
			iface['cmds'].append(fdef)
			fdef['name'] = func['name']
			fdef['cmdId'] = func['cmdId']
			fdef['undocumented'] = False

			# Handle decorators
			for decorator in func['decorators']:
				if decorator['type'] == 'undocumented':
					fdef['undocumented'] = True
				elif decorator['type'] == 'version':
					fdef['versionAdded'] = "".join(map(str, decorator['startVersion']))
					if decorator['postfix'] is None:
						fdef['lastVersion'] = fdef['versionAdded']
					elif decorator['postfix'] == '+':
						fdef['versionRemoved'] = None
					else:
						fdef['lastVersion'] = "".join(map(str, decorator['endVersion']))

			# Set default values for "missing" decorators
			if 'versionAdded' not in fdef:
				fdef['versionAdded'] = "1.0.0"
			if 'lastVersion' not in fdef:
				fdef['lastVersion'] = None

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
	fns = [dir + 'ipcdefs/auto.id', dir + 'ipcdefs/switchbrew.id'] + [x for x in glob.glob(dir + 'ipcdefs/*.id') if x != dir + 'ipcdefs/auto.id' and x != dir + 'ipcdefs/switchbrew.id']

	if os.path.exists(dir + 'ipcdefs/cache') and all(os.path.getmtime(dir + 'ipcdefs/cache') > os.path.getmtime(x) for x in fns):
		res = json.load(file(dir + 'ipcdefs/cache'))
	else:
		res = parse('\n'.join(file(fn).read() for fn in fns))
		with file(dir + 'ipcdefs/cache', 'w') as fp:
			json.dump(res, fp)
	return res
