import sys
sys.path.append('.')
import idparser

types, ifaces, services = idparser.getAll()
success = True

def getVersionIndex(v):
    if v is None:
        return len(idparser.versionInfo) - 1
    else:
        return idparser.versionInfo.index(v)

for ifaceName, iface in ifaces.items():
    # Verify unicity of cmd
    namesByVersion = [[] for i in idparser.versionInfo]
    for cmd in iface['cmds']:
        firstVersion = getVersionIndex(cmd['versionAdded'])
        lastVersion = getVersionIndex(cmd['lastVersion'])

        for i in range(firstVersion, lastVersion + 1):
            namesByVersion[i].append(cmd['name'])

    for version, cmdnames in enumerate(namesByVersion):
        seen = set()
        dups = []
        for x in cmdnames:
            if x in seen:
                dups.append(x)
            seen.add(x)

        for cmdName in dups:
            success = False
            print("Found duplicate cmd name in version %s: %s %s" % (idparser.versionInfo[version], ifaceName, cmdName))

if success == False:
    exit(1)
