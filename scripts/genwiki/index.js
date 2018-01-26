var WikiTextParser = require('parse-wikitext');
//var R = require('ramda');
var fs = require('fs');
var util = require('util');
var pandoc = require('pdc');
var pandocfilter = require('pandoc-filter');

var wikiTextParser = new WikiTextParser("switchbrew.org");
var pro = util.promisify;

var parseWikiTable=require("./table_parser").parseWikiTable;
var getFirstTable=require("./table_parser").getFirstTable;
/*var tableToRows=require("./table_parser").tableToRows;
var toOldNames = require("./toOldNames").transformPacketName;
*/

var getArticle = pro(wikiTextParser.getArticle.bind(wikiTextParser));

module.exports = {
  retrieveServices
};

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function buildInterface([ifaceName, iface]) {
  var ret = "";
  var services = ""
  if (iface.services != null)
    services = iface.services.join(", ");
  if (services != "")
    services = " is " + services;
  //var interfaceName = 'I' + serviceName.split(",")[0].split(/[:-]/).map(v => capitalize(v)).join("");
  ret += `interface ${ifaceName}${services} {\n`
  for (var cmd of iface.cmdList.sort((a, b) => a.id - b.id)) {
    var name = cmd.name || `Unknown${cmd.id}`;
    if (cmd.doc) {
      for (var line of cmd.doc.split("\n")) {
        ret += `\t# ${line}\n`;
      }
    }
    if (cmd.version)
      ret += `\t@version(${cmd.version})\n`;
    ret += `\t[${cmd.id}] ${name}();\n`
  }
  ret += "}\n"
  return ret;
}

async function main() {
  var {services, interfaces} = await retrieveServices();
  for (let [serviceName, ifaceName] of Object.entries(services)) {
    if (interfaces[ifaceName].services == null)
      interfaces[ifaceName].services = [serviceName];
    else
      interfaces[ifaceName].services.push(serviceName);
  }
  var servicesInterface = Object.entries(interfaces).sort((a, b) =>
    a[0].localeCompare(b[0])).map(buildInterface).join("\n\n");
  return servicesInterface;
}

main().then(console.log).catch(function(err) {
  setImmediate(function() {
    throw err;
  });
});

async function retrievePage(serviceName)
{
  const data = await getArticle(serviceName);
  return wikiTextParser.pageToSectionObject(data);
}

function spliceStr(str, index, count, add) {
  var ar = str.split('');
  ar.splice(index, count, add);
  return ar.join('');
}

function iterate(obj, cb, depth = 0, toplevel = null) {
  var ret = [];
  var pad = ""
  for (var i = 0;i < depth; i++) {
    pad += " ";
  }
  if (toplevel == null)
    toplevel = obj;
  for ([name, value] of Object.entries(obj)) {
    if (typeof value == "object" && !Array.isArray(value)) {
      if (value['content'] != null)
        ret.push(cb(name, value['content'], toplevel));
      ret = ret.concat(iterate(value, cb, depth + 4, toplevel));
    }
  }
  return ret;
}

async function iter(ret, serviceName, content, services) {
  if (content == null) return;

  var serviceTable = getFirstTable(content);
  if (serviceTable.length == 0) {
    return;
  }

  var ifaceName = null;
  if (content[0].includes("This is \"")) {
    ifaceName = content[0].slice(content[0].indexOf('"') + 1);
    ifaceName = ifaceName.slice(0, ifaceName.indexOf('"'));
  } else {
    // TODO: Meh
    return;
  }

  // Normalize multi-service names
  serviceName = serviceName.replace(" and ", ", ").replace(" / ", ", ")

  // Parse the list of cmds
  serviceTable = parseWikiTable(serviceTable);
  var cmdList = [];
  for (let cmd of serviceTable) {
    // Probably not a service definition.
    if (cmd['Cmd'] == null)
      break;

    var name = cmd['Name'];
    var getDesc = false;
    // Name is a link. Clean it up, and remember to get description
    var cmdDocs = null;
    var cmdName = name;
    if (name.indexOf("[[") > -1) {
      getDesc = true;
      var cmdName = name.substring(name.indexOf("[[") + 2, name.indexOf("]]"));

      // Remove the link from the cmd, so we have an easier time finding the
      // version
      name = spliceStr(name, name.indexOf("[["), cmdName.length + 4);
      cmdName = cmdName.split("#").slice(-1)[0];
      cmdName = cmdName.split("|").slice(-1)[0];
    }

    // Recover the version.
    var idx = name.indexOf("[");
    var version = null;
    if (idx != -1) {
      version = name.slice(idx + 1, name.slice(idx).indexOf("]") + idx);
      // Remove from the name
      if (name == cmdName)
        cmdName = cmdName.slice(cmdName.slice(idx).indexOf("]") + idx + 1).trim().replace(/[\(\)]/, "");
    }

    cmdName = cmdName.split(" ").find(v => cmdName.trim().length != 0) || cmdName;
    if (cmdName.endsWith("?"))
      console.error("Might be wrong function name for", ifaceName, cmdName + "(" + cmd['Cmd'] + ")");
    cmdName = cmdName.replace("?", "").trim();

    if (idx > 0)
      console.error("Might be wrong version info for", ifaceName, cmdName + "(" + cmd['Cmd'] + ")");

    // Recover the description if name was a link
    if (getDesc) {
      function findRecurse(o, name) {
        if (Array.isArray(o)) return null;
        if (typeof o !== 'object') return null;
        for (var key of Object.keys(o)) {
          if (key === name) {
            return o[key];
          } else {
            var ret = findRecurse(o[key], name);
            if (ret !== null)
              return ret;
          }
        }
        return null;
      }
      cmdDocs = findRecurse(services, cmdName);
      if (cmdDocs != null) {
        cmdDocs = cmdDocs.content.join("\n");
      } else
        console.error("Docs not found", serviceName, cmdName);
    }

    if (cmdName == "?")
      cmdName = "";
    // BSD-specific hack
    if (cmdName == "RegisterClient (Initialize)")
      cmdName = "Initialize";
    // Fsp-Srv specific hack (this is me being lazy)
    if (cmdName == "GetRightsIdByPath2 (returns extra byte)")
      cmdName = "GetRightsIdByPath2";
    cmdList.push({ id: cmd['Cmd'], name: cmdName, version, doc: cmdDocs });
  }
  if (cmdList.length > 0) {
    if (serviceName.toLowerCase() == serviceName || serviceName.startsWith("applet"))
      ret['services'][serviceName] = ifaceName;
    ret['interfaces'][ifaceName] = { cmdList: cmdList };
  }
}

async function getServiceStuff(serviceName, services) {
  var ret = {services: {}, interfaces: {}};

  var promises = iterate(services, iter.bind(null, ret));
  await Promise.all(promises)

  // Fix up the documentation links ! Find all doc links
  await Promise.all(Object.entries(ret.interfaces).map(function([ifaceName, iface]) {
    return Promise.all(iface.cmdList.map(async function(cmd) {
      if (cmd.doc != null) {
        // Turn it into json to do filtering
        var jsonCmdDocs = await pro(pandoc)(cmd.doc, 'mediawiki', 'json');
        jsonCmdDocs = pandocfilter.filter(JSON.parse(jsonCmdDocs), function(type, content, format, meta) {
          if (type == 'Link') {
            let [attrs, inlines, target] = content;
            var newLink = null;
            // If the link is relative, try to find a function or interface
            // named by it first, and do a relative link within SwIPC instead.
            if (target[0].startsWith("#")) {
              outerloop:
              for (let [otherIfaceName, otherIface] of Object.entries(ret.interfaces)) {
                // Is the name the same ? Maybe just the last part of the name ?
                if (target[0].slice(1) == otherIfaceName ||
                    target[0].slice(1) == otherIfaceName.split("::").slice(-1)[0]) {
                  newLink = `#${otherIfaceName}`;
                  break outerloop;
                }
                // Let's look for a cmd with the same name then !
                for (let otherCmd of otherIface.cmdList) {
                  if (otherCmd.name == target[0].slice(1)) {
                    newLink = `#${otherIfaceName}(${otherCmd.id})`;
                    break outerloop;
                  }
                }
              }
              if (newLink == null) {
                // Let's just redirect to switchbrew then
                newLink = "http://switchbrew.org/index.php?title=" + serviceName + target[0];
              }
            } else {
              // If the link is not relative, let's just link to switchbrew.
              newLink = "http://switchbrew.org/index.php?title=" + target[0];
            }
            return pandocfilter.Link(attrs, inlines, [newLink, target[1]]);
          }
        }, "");
        // And finally, turn it into Github-Flavored Markdown (For the ASCII
        // tables)
        cmd.doc = await pro(pandoc)(JSON.stringify(jsonCmdDocs), 'json', 'gfm');
      }
    }));
  }));

  return ret;
}

async function retrieveServices() {
  const services = await retrievePage("Services API");
  var content = services['content'];
  delete services['content'];
  var serviceList = services['Service List'];
  delete services['Service List'];

  var ret = {services: {}, interfaces: {}};
  ret = Object.assign({}, ret, await getServiceStuff("Services API", services));

  var servicePages = parseWikiTable(serviceList.content);
  for (var servicePage of servicePages) {
    for (var s of servicePage.Description.split("[[")) {
      var pageName = s.substring(0, s.indexOf("]]"));
      if (pageName == "") continue;
      let page = await retrievePage(pageName);
      let { services, interfaces } = await getServiceStuff(pageName, page)
      ret.services = Object.assign({}, ret.services, services);
      ret.interfaces = Object.assign({}, ret.interfaces, interfaces);
    }
  }


  return ret;
}
