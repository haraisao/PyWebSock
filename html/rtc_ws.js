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

  RtcWs = function( selector, context ){
    //return new RTC.fn.init( selector, context );
  };

RtcWs.prototype ={
  rtc: version,
  constructor: RtcWs,
  selector: "",
  showReply: false,
  webSocket: null,
  processEvents: strundefined,

  getMySeatKey: function(){
     return "My_eSEAT_Key";
  },

  showKey: function(){
     alert(this.getMySeatKey());
  },

  open: function() {
    if (this.webSocket == null) {
        this.webSocket = new WebSocket(uri);

        this.webSocket.onopen = this.onOpen;
        this.webSocket.onmessage = this.onMessage;
        this.webSocket.onclose = this.onClose;
        this.webSocket.onerror = this.onError;
     }
  },

  onOpen: function(event) {
    console.log("Open webSocket");
  },

  onMessage: function(event) {
    if (event && event.data) {
      console.log("Rec:"+event.data);
/*
      var res = this.func_exec(event.data);
      this.send(JSON.stringify(res));
      console.log(res);
*/
    }
  },

  onError: function(event) {
    console.log("ERROR!");
  },

  onClose: function(event) {
     console.log("Close webSocket(" + event.code + ")");
     this.webSocket = null;
  },

  send: function(message) {
     if (message && this.webSocket) {
       this.webSocket.send(message);
       console.log("Send Message (" + message + ")");
     }
  },

  func_exec: function(msg) {
     var vals = JSON.parse(msg);
     try{
       var func = eval(vals.func);
       return func.apply(null, vals.args);
     }catch(e){
       console.log("ERROR in func_exec");
     }
     return null;
  },


};


if ( typeof noGlobal === strundefined ){
  window.RtcWs = RtcWs;
}

  return RtcWs;
}));
