/*
 *  Comet functions for eSEAT
 *  Copyright(c)  2015 Isao Hara, All Rights Reserved.
 */

(function( global, factory) {
  if ( typeof module === "object" && typeof module.exports === "object" ){
    module.exports = global.document ?
	factory( global, true) :
	function (w) {
	  if ( !w.document ){
		throw new Error("rtc requires a window with a document");
	  }
	  return factory( w );
	};
  } else {
	factory( global );
  }
}(typeof window !== "undefined" ? window : this, function( window, noGlobal){

var
  version = "0.1",
  strundefined = typeof undefined,

  RtcWs = function( parent ){
    this.parent = parent;
    this.genId();
    this.state="Generating"
    
    //return new RTC.fn.init( selector, context );
  };

RtcWs.prototype ={
  rtc: version,
  constructor: RtcWs,
  parent: null,
  showReply: false,
  webSocket: null,
  id: null,
  state: null,
  timer_id: null,
  debug_mode: false,
  seq_queue: [1,2,3,4,5,6,7,8,9,-1],
  next_seq:0,
  last_seq:9,
  reply_queue: [null, null, null, null, null, null, null, null, null, null],
  list_w:5,
  processEvents: strundefined,

  genId: function(){
     var i, random;
     this.id ="";
     for (i = 0; i < 32; i++){
         if (i == 8 || i == 12 || i == 16 || i == 20){
             this.id += "-";
         }else{
           random = Math.random() * 16 | 0;
           this.id += (i == 12 ? 4 : (i == 16 ? (random & 3 | 8) : random)).toString(16);
         }
     }
     if (this.debug_mode){ console.log(this.id); }
     return this.id
  },

  showId: function(){
     if( this.id == null) { this.genId(); }
     alert(this.id);
  },

  open: function(uri) {
    if (this.webSocket == null) {
        this.webSocket = new WebSocket(uri);

        this.webSocket.onopen = this.onOpen;
        this.webSocket.onmessage = this.onMessage;
        this.webSocket.onclose = this.onClose;
        this.webSocket.onerror = this.onError;
        this.webSocket.state="Opening";
        this.webSocket.rtc=this;
     }
     this.state = "Opening";
  },

  waitOpened: function(obj) {
    obj.count=0;
    obj.timer_id = setInterval( function(){
      if(this.debug_mode){ console.log("wait:"+obj.webSocket.state); }
      if (obj.webSocket.state=="onOpen" || obj.count>10 ){ 
          obj.count += 1;
          clearInterval(obj.timer_id);
          obj.send('{"ID": "'+obj.id+'", "Status":"Opening"}');
          obj.timer_id=null;
      }
    },500);
  },

  onOpen: function(event) {
    if(this.rtc.debug_mode){ console.log("Open webSocket"); }
    this.state='onOpen';
  },

  onMessage: function(event) {
    if (event && event.data) {
      data = event.data
      if (this.state == "onOpen"){
        try{
          data = JSON.parse(data);
          this.state = data['Status'];
          if(this.rtc.debug_mode){ console.log("WS Opened"); }
          return;
        }catch(e){
           ;
        }
      }else if (this.state == "Opened"){
        var res = this.rtc.func_exec(data);
        if (res){ this.rtc.send(res); }
        if(this.rtc.debug_mode){ console.log(res); }

      }else{
        console.log("State="+this.state+" Recv:"+data);
      }
    }
  },

  onError: function(event) {
    console.log("ERROR!");
    this.state = "Error";
  },

  onClose: function(event) {
     console.log("Close webSocket(" + event.code + ")");
     this.state = "Closed";
     this.webSocket = null;
  },

  send: function(message) {
     if (message && this.webSocket) {
       this.webSocket.send(message);
       if(this.debug_mode){ console.log("Send Message (" + message + ")"); }
     }
  },

  request_seq: function() {
     var seq = -1;
     if(this.seq_queue[this.next_seq] != -1 && this.reply_queue[this.next_seq] == null){
       seq = this.next_seq;
       this.next_seq = this.seq_queue[this.next_seq];
       this.seq_queue[seq] = -1;
     }
     return seq;
  },

  release_seq: function(seq) {
    if (this.seq_queue.indexOf(seq) == -1 && this.seq_queue[ this.last_seq ] == -1){
      this.reply_queue[seq]=null;
      this.seq_queue[ this.last_seq ] = seq;
      this.last_seq = seq;
    }
  },

  call: function(msg, rfunc=null) {
    if(this.webSocket.state != 'Opened') { return -2; }
    var id = this.request_seq();
    if (id < 0){
      console.log("Over requests...");
    }else{
      this.reply_queue[id]=rfunc;
      try{
        this.send(JSON.stringify({"request_seq": id, "args": msg}));
      }catch(e){
        console.log("Error in call, fail to send message");
        this.release_seq(id)
        return -2;
      }
    }
    return id;
  },

  call_reply: function(seq, args) {
    var func = this.reply_queue[seq];
    var res = null;
    if(func){
      res = func(args);
    }
    this.release_seq(seq);
    return null;
  },

  func_exec: function(msg) {
     try{
       var vals = JSON.parse(msg);
       var seq = vals.seq;
       var reply_seq = vals.reply_seq;
       var result = vals.result;

       if (self.func){
         var func = eval(vals.func);
         if (seq){
           var res = func.apply(null, vals.args);
           var result = { "seq": seq, "result":res };
           return  JSON.stringify(result);
         }else{
           var res = func.apply(null, vals.args);
         }
       }else{
         if (reply_seq >= 0){
           this.call_reply(reply_seq, result);
         }
       }
       return null;
     }catch(e){
       console.log(e);
       eval(msg);
     }
     return null;
  },

  broadcast: function(msg) {
    try{
      if( this.parent ){
        blk = this.parent.scripts.children[0];
        proc = new Process(blk);
        proc.doBroadcast(msg);
        delete proc;
      }

    }catch(e){
      console.log( "Error in broadcast" );
    }
    return null;
  },

  getProjectList: function(func, ms) {
    var res = this.call("projects", func);
    if(res == -2){
      setTimeout(function(){ this.getProjectList(func) }, ms);
    }
  },

  mkProjectList: function(lst) {
    if(!lst) { return ""; }
    var h = lst.length / this.list_w;
    var n;

    var lstview = '<table>';
    for(var i=0; i< h ; i++){
      n = i*this.list_w;
      lstview += '<tr>';
      for(var j=0; j < this.list_w && lst.length > n+j; j++){
        lstview += '<td>'+ this.mk_icon(lst[n+j]) +'</td>';
      }
      lstview += '</tr>';
    }
    lstview += '</table>';
    return lstview;
  },

  mk_icon: function(name){
    var icon;
    icon  = '<p style="position: relative;">';
    icon += '<a target="_new" href="/snap/snap.html#open:projects/'+name+'/project.xml">';
    icon += '<img src="images/Blue.png" alt="'+name+'" /><br />';
    icon += '</a>';
    icon += ' <span style="position: absolute; top: 15px; left: 15px; width: 70px;">'+name+'</span>';
    icon += '</p>';
    return icon;
  },


};


if ( typeof noGlobal === strundefined ){
  window.RtcWs = RtcWs;
}

  return RtcWs;
}));
