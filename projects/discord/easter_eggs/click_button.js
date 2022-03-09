var observeDOM = (function(){
  var MutationObserver = window.MutationObserver || window.WebKitMutationObserver;

  return function( obj, callback ){
    if( !obj || obj.nodeType !== 1 ) return;

    if( MutationObserver ){
      // define a new observer
      var mutationObserver = new MutationObserver(callback)

      // have the observer observe foo for changes in children
      mutationObserver.observe( obj, { childList:true, subtree:true })
      return mutationObserver
    }

    // browser support fallback
    else if( window.addEventListener ){
      obj.addEventListener('DOMNodeInserted', callback, false)
      obj.addEventListener('DOMNodeRemoved', callback, false)
    }
  }
})();


// div - messagesWrapper - contains all messages
// li  - messageListItem - contains list containing message
// need to search inside li for button


var messagesWrapper = document.querySelector('div[class^="messagesWrapper"]');

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function clickButton(button) {
    await sleep(1000);
    button.click();
}

function isCorrectGroup() {
    var correct = false;
    var headings = document.querySelectorAll('h1')
    for (i = 0; i < headings.length; i++) {
        if (headings[i].innerHTML == 'TESTTT') {
            correct = true;
            break;
        }
    }
        
    return correct;
}

var messagesWrapper = document.querySelector('div[class^="messagesWrapper"]');

observeDOM(messagesWrapper, function(m){
  if (!isCorrectGroup()) {
      console.log("wrong group")
      return null;
  }
    
  var messageList = messagesWrapper.querySelectorAll('li');

  if (messageList.length >= 1) {
    var message = messageList[messageList.length - 1];
    var buttons = message.querySelectorAll('button');

    if (buttons.length >= 1) {
        clickButton(buttons[0]);
    }
  }
});

