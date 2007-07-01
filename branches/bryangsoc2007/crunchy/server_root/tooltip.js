/*------------------------------- tooltip -------------------------------- */

function display_help(uid, data) {
    var i = new XMLHttpRequest()
    i.open("POST", "/input?uid="+uid, true);
    //i.open("POST", "/help"+session_id, true);
    i.send(data + "\n");
}

function tooltip_display(event, interp_id) {
    switch(event.keyCode) {
        // BUG: pressing 'escape' breaks crunchy interpreter
        case 13:    // enter
        case 27:    // escape
        case 48:    // close )
        case 8:     // backspace
          hide_tipbar(interp_id);
          break;
      case 57:  // open paren "("
            tooltip_doc(interp_id);
            break;
        case 190:  // period "."
            tooltip_dir(interp_id);
            break;
            // attempting to solve problem on Mac
        case 0:
            switch(event.charCode) {
                case 40: // open paren "("
                    tooltip_doc_mac(interp_id);
                    break;
                case 41: // close )
                    hide_tipbar(interp_id);
                    break;
                case 46:  // period "."
                    tooltip_dir_mac(interp_id);
                    break;
                };
            break;
    };
};

function show_tipbar(interp_id) {
    tipbar = document.getElementById("tipbar_"+interp_id);
    tipbar.style.display = "block";
};

function hide_tipbar(interp_id) {
    tipbar = document.getElementById("tipbar_"+interp_id);
    tipbar.style.display = "none";
    tipbar.innerHTML = " ";
};

function tooltip_doc(interp_id) {
    input = document.getElementById("in_"+interp_id);
    end = input.selectionEnd;    
    data = input.value.substring(0, end);
    tipbar = document.getElementById("tipbar_"+interp_id);
    hide_tipbar(interp_id);
   
    h = new XMLHttpRequest();
    h.onreadystatechange = function() {
        if (h.readyState == 4) {
            try {
                var status = h.status;
            } catch(e) {
                var status = "NO HTTP RESPONSE";
            }
            switch (status) {
                case 200:
                    tipbar.appendChild(document.createTextNode(h.responseText));
                    //alert("tipping: "+h.responseText);
                    show_tipbar(interp_id);
                    input.focus();
                    break;
                // Internet Explorer might return 1223 for 204
                case 1223:
                case 204:
                    // No tips available
                    break;
                case 12029:
                    // Internet Explorer client could not connect to server
                    status = "NO HTTP RESPONSE";
                default:
                    alert(status + "\\n" + h.responseText, false);
            }
        }
    }
    h.open("POST", "/doc"+session_id+"?uid="+interp_id, true);
    h.send(encodeURIComponent(data));
};

function tooltip_doc_mac(interp_id) {
    input = document.getElementById("in_"+interp_id);
    data = input.value + "(";
    tipbar = document.getElementById("tipbar_"+interp_id);
    hide_tipbar(interp_id);
   
    h = new XMLHttpRequest();
    h.onreadystatechange = function() {
        if (h.readyState == 4) {
            try {
                var status = h.status;
            } catch(e) {
                var status = "NO HTTP RESPONSE";
            }
            switch (status) {
                case 200:
                    tipbar.appendChild(document.createTextNode(h.responseText));
                    show_tipbar(interp_id);
                    input.focus();
                    break;
                // Internet Explorer might return 1223 for 204
                case 1223:
                case 204:
                    // No tips available
                    break;
                case 12029:
                    // Internet Explorer client could not connect to server
                    status = "NO HTTP RESPONSE";
                default:
                    alert(status + "\\n" + h.responseText, false);
            }
        }
    }
    h.open("POST", "/doc"+session_id+"?uid="+interp_id, true);
    h.send(encodeURIComponent(data));
};

function tooltip_dir(interp_id) {
    input = document.getElementById("in_"+interp_id);
    end = input.selectionEnd;    
    data = input.value.substring(0, end);
    tipbar = document.getElementById("tipbar_"+interp_id);
    hide_tipbar(interp_id);
   
    h = new XMLHttpRequest();
    h.onreadystatechange = function() {
        if (h.readyState == 4) {
            try {
                var status = h.status;
            } catch(e) {
                var status = "NO HTTP RESPONSE";
            }
            switch (status) {
                case 200:
                    tipbar.appendChild(document.createTextNode(h.responseText));
                    show_tipbar(interp_id);
                    input.focus();
                    break;
                // Internet Explorer might return 1223 for 204
                case 1223:
                case 204:
                    // No tips available
                    break;
                case 12029:
                    // Internet Explorer client could not connect to server
                    status = "NO HTTP RESPONSE";
                default:
                    alert(status + "\\n" + h.responseText, false);
            }
        }
    }
    h.open("POST", "/dir"+session_id+"?uid="+interp_id, true);
    h.send(encodeURIComponent(data));
};

function tooltip_dir_mac(interp_id) {
    input = document.getElementById("in_"+interp_id);
    data = input.value + ".";
    tipbar = document.getElementById("tipbar_"+interp_id);
    hide_tipbar(interp_id);
   
    h = new XMLHttpRequest();
    h.onreadystatechange = function() {
        if (h.readyState == 4) {
            try {
                var status = h.status;
            } catch(e) {
                var status = "NO HTTP RESPONSE";
            }
            switch (status) {
                case 200:
                    tipbar.appendChild(document.createTextNode(h.responseText));
                    show_tipbar(interp_id);
                    input.focus();
                    break;
                // Internet Explorer might return 1223 for 204
                case 1223:
                case 204:
                    // No tips available
                    break;
                case 12029:
                    // Internet Explorer client could not connect to server
                    status = "NO HTTP RESPONSE";
                default:
                    alert(status + "\\n" + h.responseText, false);
            }
        }
    }
    h.open("POST", "/dir"+session_id+"?uid="+interp_id, true);
    h.send(encodeURIComponent(data));
};