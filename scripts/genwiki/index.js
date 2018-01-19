var WikiTextParser = require('parse-wikitext');
//var R = require('ramda');
var fs = require('fs');
var util = require('util');
var pandoc = require('pdc');
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

function buildInterface([serviceName, cmds]) {
  var ret = "";
  var interfaceName = 'I' + serviceName.split(",")[0].split(/[:-]/).map(v => capitalize(v)).join("");
  ret += `interface ${interfaceName} is ${serviceName} {\n`
  for (var cmd of cmds) {
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
  var services = await retrieveServices();
  var servicesInterface = Object.entries(services).map(buildInterface).join("\n\n");
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

async function getServiceStuff(services) {
  var servicesRet = {};

  // Now we have only services
  for (var [serviceName, service] of Object.entries(services)) {
    // Skip over content that doesn't look like a service definition
    if (serviceName == 'content' || serviceName != serviceName.toLowerCase()) continue;
    if (service.content == null) continue;
    var serviceTable = getFirstTable(service.content);
    if (serviceTable.length == 0) {
      continue;
    }

    // Normalize multi-service names
    serviceName = serviceName.replace(" and ", ", ").replace(" / ", ", ")

    // Parse the list of cmds
    serviceTable = parseWikiTable(serviceTable);
    var cmdList = [];
    for (cmd of serviceTable) {
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
        version = name.slice(idx + 1, name.slice(idx).indexOf("]"));
        // Remove from the name
        if (name == cmdName)
          cmdName = cmdName.slice(cmdName.slice(idx).indexOf("]") + 1).trim();
      }

      cmdName = cmdName.trim();

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
        if (cmdDocs != null)
          cmdDocs = await pro(pandoc)(cmdDocs.content.join("\n"), 'mediawiki', 'gfm');
        else
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
    if (cmdList.length > 0)
      servicesRet[serviceName] = cmdList;
  }
  return servicesRet;
}

async function retrieveServices() {
  const services = await retrievePage("Services API");
  var content = services['content'];
  delete services['content'];
  var serviceList = services['Service List'];
  delete services['Service List'];

  var ret = {};
  ret = Object.assign({}, ret, await getServiceStuff(services));

  var servicePages = parseWikiTable(serviceList.content);
  for (var servicePage of servicePages) {
    for (var s of servicePage.Description.split("[[")) {
      var pageName = s.substring(0, s.indexOf("]]"));
      if (pageName == "") continue;
      let page = await retrievePage(pageName);
      ret = Object.assign({}, ret, await getServiceStuff(page));
    }
  }


  return ret;
}
