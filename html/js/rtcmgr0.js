/*
  rtcmgr.js (?)
  I lost original rtcmgr.js...
*/

var rtc = new RtcWs();
var selectedRtc = "";
var selectedRtcItm = null;

function init() {
  selectDataTypeHide();
  rtc.open('rtmgr');
  rtc.waitOpened(rtc);
  getRtcList();
}

function getRtcList() {
  rtc.getRtcList(updateRtcList, 250);
}

function updateRtcList(lst) {
  lstview = mkRtcList(lst);
  $("[data-name='rtc-list']").html(lstview);
  if( selectedRtcItm ){
    selectedRtcItm = document.getElementById(selectedRtc);
    selectedRtcItm.style.backgroundColor='black';
    selectedRtcItm.style.color='white';
  }
}

function mkRtcList(lst){
  if(!lst) { return ""; }
  var h = lst.length;
  var n;
  var lstview = '<table>';

  for(var i=0; i< h ; i++){
    n=i+1
    lstview += '<tr>';
    lstview += '<td>['+n+']:'+ mk_rtc_item(lst[i]) +'</td>';
    lstview += '</tr>';
  }
  lstview += '</table>';
  return lstview;
}

function mk_rtc_item(prof){
  var itm;

  itm="";
  itm += '<span id="'+prof.name+'" onClick="selectRtc(\''+prof.name+'\', this);">';
  itm += prof.name
  itm += '</span>';
  console.log(prof);

  for(p in  prof.in_port){
    itm += "<br>&nbsp;&nbsp;-> "+prof.in_port[p].name +"("+prof.in_port[p].data_type+")";
  }

  for(p in  prof.out_port){
    itm += "<br>&nbsp;&nbsp;&nbsp;&nbsp; "+prof.out_port[p].name +"("+prof.out_port[p].data_type+") ->";
  }

  return itm;
}

function selectRtc(name, itm){
  if (selectedRtcItm){
    selectedRtcItm.style.backgroundColor='white';
    selectedRtcItm.style.color='black';
  }
 
  selectedRtc = name;
  rtc.setCurrentRtc(name);
  document.getElementById('SelectedRtcName').value=name;
  selectedRtcItm = itm;
  selectedRtcItm.style.backgroundColor='black';
  selectedRtcItm.style.color='white';
}

function addDataPort(tid, nid, dtid){
  var typ,name, dtype;
  typ = document.getElementById(tid).value;
  name = document.getElementById(nid).value;
  dtype = document.getElementById(dtid).value;

  if (selectedRtcItm == null || typ == "" || name == "" ){
    alert("Error in addDataPort");
    return;
  }

  rtc.addDataPort(typ, name, dtype);
  getRtcList();
}

function deleteDataPort( nid ){
  var name;
  name = document.getElementById(nid).value;
  if (selectedRtcItm == null || name == "" ){
    alert("Error in deleteDataPort");
    return;
  }
  rtc.deleteDataPort(name);
  getRtcList();
}


function selectDataType(){
  document.getElementById('DataType').value = document.getElementById('DataTypeSel').value;
   document.getElementById('DataTypeSel').style.display='none';
}

function selectDataTypeShow(){
  document.getElementById('DataTypeSel').style.display='block';
}

function selectDataTypeHide(){
  document.getElementById('DataTypeSel').style.display='none';
}

/*
*/
function activateRtc(){
  if (selectedRtcItm == null){
    alert("Error in activateRtc");
    return;
  }
  rtc.activateRtc();
}

function deactivateRtc(){
  if (selectedRtcItm == null){
    alert("Error in activateRtc");
    return;
  }
  rtc.deactivateRtc();
}

function open_snap(){
  if( selectedRtcItm ){
    window.open("snap/snap.html#open:projects/rtc/project.xml");
  }
}

/*
$(function() { $('nav#menu').mmenu(); })
$(init_rtcmgr);
*/
