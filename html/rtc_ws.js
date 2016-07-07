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
  results: [],
  debug_mode: false,
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
      console.log(data);
      if (this.state == "onOpen"){
        /// 
        /// Nagotiate open..
        /// 
        try{
          data = JSON.parse(data);
          this.state = data['Status'];
          if(this.rtc.debug_mode){ console.log("WS Opened"); }
          return;
        }catch(e){
           ;
        }
      }else if (this.state == "Opened"){
        /// 
        /// Communicate with client...
        /// Call function 
        /// 
        var res = this.rtc.func_exec(data);
        if (res !== null){ this.rtc.send(res); }
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
     console.log(message);
     if (message && this.webSocket) {
       this.webSocket.send(message);
       if(this.debug_mode){ console.log("Send Message (" + message + ")"); }
     }
  },


  ///
  ///
  set_result: function(msg) {
    console.log(msg);
    this.results.push(msg);
    return;
  },

  get_result: function() {
    if( this.results.length > 0){
      var res=this.results[0];
      this.results.shift();
      return res;
    }else{
     return null;
    }
  },

  ///
  /// Execute function
  func_exec: function(msg) {
     var res = null;
     try{
       /// parse JSON message 
       /// from Server side request,
       ///   sync  -> msg={'func': 'f', 'seq': n, 'args': 'ARG'}
       ///   async -> msg={'func': 'f',  'args': 'ARG'}
       var vals = JSON.parse(msg);
       var seq = vals.seq;
       var func = eval(vals.func);
       var result = vals.result;

       if (seq && func){ /// synchronize request
         res = func.apply(null, vals.args);
         return  JSON.stringify( { "seq": seq, "result":res } );
       }else if (result){ 
         this.set_result(result);
         return null;
       }else{           /// asynchronize requset
         res = func.apply(null, vals.args);
         return  JSON.stringify(res);
       }

     }catch(e){
       ///  'msg' isn't JSON format
       eval(msg);
     }

     return res;
  },

  ///
  ///  for Snap! function...
  ///
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

};


if ( typeof noGlobal === strundefined ){
  window.RtcWs = RtcWs;
}

  return RtcWs;
}));
