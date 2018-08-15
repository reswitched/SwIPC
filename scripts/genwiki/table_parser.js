module.exports={
  getFirstTable:getFirstTable,
  parseWikiTable:parseWikiTable,
  tableToRows:tableToRows
};

function getFirstTable(lines)
{
  var afterFirstTable=false;
  var inTable=false;
  return lines.filter(function(line){
    if(afterFirstTable) return false;
    if(line.includes('{| class="wikitable"'))
      inTable=true;

    if(inTable && line.endsWith('|}')) {
      inTable = false;
      afterFirstTable = true;
      return true;
    }

    return inTable;
  });
}

function tableToRows(lines)
{
  lines=lines.slice(1);
  if(lines[0].trim().startsWith("|-"))
    lines.shift();
  var rows=[];
  var currentRow=[];
  lines.forEach(function(line){
    if(line.trim().startsWith("|-") || line.endsWith("|}"))
    {
      if (!(line.endsWith("|}") && currentRow.length == 0))
        rows.push(currentRow);
      currentRow=[];
    }
    else currentRow.push(line);
  });
  if(currentRow.length!=0 && currentRow[0].trim()!="") rows.push(currentRow);
  return rows;
}

// output format : one object by line, repetition of the row in case of rowspan>1 (for example repetition of Packet Id)
// for colspan>1 : [first element,second element] or {colName:first element,...} if ! are given
// need to implement colspan
function rowsToSimpleRows(rows)
{
  // for recursive arrays ( / colspan ) : have a currentCols : no : rec
  var rawCols=rows[0];
  var colNames=[].concat.apply([], rawCols.map(function(rawCol){
    return rawCol.split("!")[1].split("||").map(v => v.split("|").slice(-1)[0].trim());
  }));

  // for rowspan
  var currentValues={};
  var values=[];
  return rows.slice(1).map(function(row)
  {
    var currentColValue="";
    var currentColRemaining=0;

    var colToAdd=colNames.length-row.length;
    var i;
    for(i=0;i<colToAdd;i++) if(currentValues[i]!==undefined && currentValues[i].n>0) row.unshift("");
    var fields=[];
    var curIdx = -1;
    for(i=0;i<row.length;i++)
    {
      var col=row[i];
      if (!col.startsWith("| ") && curIdx != -1) {
        fields[curIdx].value += "\n" + col;
        continue;
      }
      col=col.substring(2);
      var cols = col.split('||');
      for (col of cols) {
        var parts,value,n;
        if(col.indexOf("colspan")!=-1)
        {
          parts=col.split("|");
          value=parts[1].trim();
          n=parts[0].replace(/^.*colspan="([0-9]+)".*/,'$1');
          currentColValue=value;
          currentColRemaining=n;
        }
        else if(col.indexOf("rowspan")!=-1)
        {
          parts=col.split("|");
          value=parts[1].trim();
          n=parts[0].replace(/^.*rowspan="([0-9]+)".*/,'$1');
          currentValues[i]={n:n,value:value};
        }
        if(currentValues[i]!==undefined && currentValues[i].n>0)
        {
          currentValues[i].n--;
          curIdx = fields.push(currentValues[i].value) - 1;
        }
        else if(currentColRemaining!=0)
        {
          while(currentColRemaining>0)
          {
            curIdx = fields.push(currentColValue) - 1;
            currentColRemaining--;
          }
        }
        else curIdx = fields.push(col.trim()) - 1;
      }
    }
    return fields.reduce(function(values,value,i){
      values[colNames[i]]=value;
      return values;
    },{});
  });
}


function parseWikiTable(lines)
{
  var rows=tableToRows(lines);
  return rowsToSimpleRows(rows);
}
