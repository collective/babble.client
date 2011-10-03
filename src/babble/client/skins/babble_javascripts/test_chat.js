/*
GNU General Public License (GPL)

This program is free software; you can redistribute it and/or
example/dexterity/tests/.svn/text-base/test_integration.py.svn-base:        addform = addview.form_instance
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
*/

var SUCCESS = 0;
var AUTH_FAIL = -1;
var TIMEOUT = 1;
var SERVER_FAULT = 2;

var blink_order = 0;
var doc_title;
var messages_found = 0;
var poll_count = 0;         // The amount of server polls that have been made
var poll_cycle = 10;        // The amount of polls to make in a cycle


// XXX: These are the DTML variables, which we now hardcode
var poll_max = 20000;
var poll_min = 5000;
var username = "johndoe";
var base_url = "http://localhost:8050/babble";
// XXX: Up until here

var timeout = 2000;
var poll_interval = poll_min;   // The initial polling period

var window_focus = true;
var chat_focus = new Array();
var new_chats = new Array();
var chats = new Array();    // Records new chat windows being opened. 

if (!log) {
    var log = {
        toggle: function() {},
        move:   function() {},
        resize: function() {},
        clear:  function() {},
        debug:  function() {},
        info:   function() {},
        warn:   function() {},
        error:  function() {},
        profile: function() {}
    };
}

function prep4JQ(str) {
    /* From JQUERY selector docs: 
    * If you wish to use any of the meta-characters 
    * (#;&,.+*~':"!^$[]()=>|/@ ) as a literal part of a name, 
    * you must escape the character with two backslashes: \\.
    */
    str = str.replace(/\#/g, '\\#');
    str = str.replace(/\;/g, '\\;');
    str = str.replace(/\&/g, '\\&');
    str = str.replace(/\,/g, '\\,');
    str = str.replace(/\./g, '\\.');
    str = str.replace(/\+/g, '\\+');
    str = str.replace(/\*/g, '\\*');
    str = str.replace(/\~/g, '\\~');
    str = str.replace(/\'/g, "\\'");
    str = str.replace(/\:/g, '\\:');
    str = str.replace(/\"/g, '\\"');
    str = str.replace(/\!/g, '\\!');
    str = str.replace(/\^/g, '\\^');
    str = str.replace(/\$/g, '\\$');
    str = str.replace(/\[/g, '\\[');
    str = str.replace(/\]/g, '\\]');
    str = str.replace(/\(/g, '\\(');
    str = str.replace(/\)/g, '\\)');
    str = str.replace(/\=/g, '\\=');
    str = str.replace(/\>/g, '\\>');
    str = str.replace(/\|/g, '\\|');
    str = str.replace(/\//g, '\\/');
    str = str.replace(/\@/g, '\\@');
    return str;
}

function getMinimizedChats() {
    var cookie = jQuery.cookie('chats_minimized_'+username);
    if (cookie)
        return cookie.split(/\|/);
    return Array();
}

function sanitizePath(call) {
    return base_url + call;
}

function oc(a) {
    // Thanks to Jonathan Snook: http://snook.ca
    var o = {};
    for(var i=0; i<a.length; i++) {
        o[a[i]]='';
    }
    return o;
}

jQuery(document).ready(function() {
    if (initialize()) { 
        jQuery.doTimeout(poll_max, function() {
            initialize();
        });
    }
});


function initialize() {  
    if (!username)
        return true; // This will let doTimout continue, i.e initialize will be called again.

    var open_chats = Array();
    var cookie = jQuery.cookie('chats-open-'+username);
    log.info('initialize: cookie = ' + cookie + '\n');
    jQuery.cookie('chats-open-'+username, null, {path: '/'});
    if (cookie) {
        open_chats = cookie.split('|');
        for (var i=0; i<open_chats.length; i++) {
            var user = open_chats[i];
            if (user) { 
                createChat(user, 1);
            }
        }
    }
    path = sanitizePath('/@@babblechat/initialize');
    jQuery.ajax({
        url: path,
        cache: false,
        dataType: "json",
        timeout: timeout,
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            log.error(textStatus);
            log.error(errorThrown);
            // This will let doTimout continue, i.e initialize will be called again.
            return true; 
        },
        success: function(data) {
            if (Number(data.status) == TIMEOUT) {
                // This will let doTimout continue, i.e initialize will be called again.
                return true; 
            }
            else if (Number(data.status) == AUTH_FAIL) {
                return false;
            }
            poll_interval = poll_min;
            poll_count = 0;
            poll();
        }
    });
}

function appendMessages(username, fullname, messages, minimized, clear_and_replace) {
    /* username: The username of the conversation *partner*
       fullname: The fullname of the conversation partner
       minimized: Should the chatbox be minmized?
       clear_and_replace: Clear and replace all messages that might be in the chatbox (if it exists).
    */
    messages_found += 1;
    if (!new_chats)
        new_chats = Array();

    new_chats[username] = true;
    var chat = jQuery('#chatbox_'+prep4JQ(username));
    if (chat.length <= 0) {
        createChat(username, minimized);
        // createChat will fetch all uncleared messages (including the new ones
        // we have here), therefore we can just return here
        return;
    }
    if (chat.css('display') == 'none') {
        chat.css('display','block');
        reorderChats();
    }
    var chat_content = chat.find(".chat-content");
    if (clear_and_replace) {
        chat_content.empty();
    }
    for (var i=0; i<messages.length; i++) {
        message = messages[i];
        var text = message[3].replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
        var year = message[1].substring(0,4);
        var month = message[1].substring(5,7);
        var day = message[1].substring(8,10);
        var hour = message[2].substring(0,2);
        var minute = message[2].substring(3,5);
        var timeob = new Date(new Date(year, month, day, hour, minute) - new Date().getTimezoneOffset() * 60000);
        var localtime = timeob.toLocaleTimeString().substring(0,5);
        if (message[0] == username) {
            message_html = '<div class="chat-message">' + 
                                '<span class="chat-message-them">'+fullname+' '+localtime+':&nbsp;&nbsp;</span>' + 
                                '<span class="chat-message-content">'+text+'</span>' + 
                            '</div>';
        }
        else {
            message_html = '<div class="chat-message">' + 
                                '<span class="chat-message-me">me '+localtime+':&nbsp;&nbsp;</span>' + 
                                '<span class="chat-message-content">'+text+'</span>' + 
                            '</div>';
        }
        chat_content.append(message_html);
    }
    chat_content.scrollTop(chat_content[0].scrollHeight);
}

function reorderChats() {
    var index = 0;
    for (var i=0; i < chats.length; i++) {
        title = chats[i];
        var chatbox =  jQuery("#chatbox_"+prep4JQ(title));
        if (chatbox.css('display') != 'none') {
            if (index === 0) {
                chatbox.css('right', '20px');
            } 
            else {
                width = (index)*(225+7)+20;
                chatbox.css('right', width+'px');
            }
            index++;
        }
    }
}

function positionNewChat(chatbox) {
    var num_chats = 0;
    for (var i=0; i<chats.length; i++) {
        if (jQuery("#chatbox_"+prep4JQ(chats[i])).css('display') != 'none') {
            num_chats++;
        }
    }
    if (num_chats === 0) {
        chatbox.css('right', '20px');
    } 
    else {
        width = (num_chats)*(225+7)+20;
        chatbox.css('right', width+'px');
    }
}

function closeChat(title) {
    jQuery('#chatbox_'+prep4JQ(title)).css('display','none');
    reorderChats();
    var cookie = jQuery.cookie('chats-open-'+username);
    var open_chats = Array();
    if (cookie)
        open_chats = cookie.split('|');

    new_chats = Array();
    for (var i=0; i < open_chats.length; i++) {
        if (open_chats[i] != title) {
            new_chats.push(open_chats[i]);
        }
    }
    log.info('closeChat: cookie \n');
    if (new_chats.length) {
        jQuery.cookie('chats-open-'+username, new_chats.join('|'), {path: '/'});
    }
    else {
        jQuery.cookie('chats-open-'+username, null, {path: '/'});
    }
    path = sanitizePath('/@@babblechat/clear_messages');
    jQuery.ajax({
        url: path,
        cache: false,
        data: {contact: title},
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            log.error(textStatus);
            log.error(errorThrown);
        },
        success: function() {
            log.info(title + "'s messages succesfully cleared. \n");
        }
    });
}

function startChat(contact) {
    createChat(contact);
    jQuery("#chatbox_"+prep4JQ(contact)+" .chat-textarea").focus();

    // Reset the polling
    messages_found = 0;
    poll_count = 0;
    poll_interval = poll_min;
    poll();
}

function createChat(title, minimize) {
    var cookie = jQuery.cookie('chats-open-'+username);
    if (cookie)
        var open_chats = cookie.split('|');
    else
        var open_chats = Array();

    if (!(title in oc(open_chats))) {
        // Update the cookie if this new chat is not yet in it.
        open_chats.push(title);
        var new_cookie = open_chats.join('|');
        jQuery.cookie('chats-open-'+username, new_cookie, {path: '/'});
        log.info('createChat: updated cookie = ' + new_cookie + '\n');
    }

    var chatbox = jQuery("#chatbox_"+prep4JQ(title));
    if (chatbox.length > 0) {
        // The chatbox exists, merely hidden
        if (chatbox.css('display') == 'none') {
            chatbox.css('display','block');
            reorderChats();
        }
        chatbox.find(".chat-textarea").focus();
        return;
    }
    chatbox = createChatBox(title);
    positionNewChat(chatbox);
    chats.push(title);
    if (minimize == 1) {
        // Minimize the chat if it's in the minimized_chats cookie
        var minimized_chats = getMinimizedChats();
        if (title in oc(minimized_chats)) {
            chatbox.find('.chat-content').css('display','none');
            chatbox.find('.chat-input').css('display','none');
        }
    }
    handleChatEvents(title);
    chatbox.show();
    var chat_content = chatbox.find('.chat-content');
    chat_content.scrollTop(chat_content[0].scrollHeight);
}

function createChatBox(title) {
    path = sanitizePath('/@@render_chat_box');
    jQuery.ajax({
        url: path,
        cache: false,
        async: false,
        data: {
            box_id: "chatbox_"+title,
            contact: title
            },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            log.error(textStatus);
            log.error(errorThrown);
            return;
        },
        success: function(data) {
            jQuery('body').append(data).find('.chat-message .time').each(function (){
                jthis = jQuery(this);
                var time = jthis.text().split(':');
                var hour = time[0];
                var minutes = time[1];
                var date = new Date();
                date.setHours(hour - date.getTimezoneOffset() / 60);
                date.setMinutes(minutes);
                jthis.replaceWith(date.toLocaleTimeString().substring(0,5));
            });

        }
    });
    return jQuery('#chatbox_'+prep4JQ(title));
}

function handleChatEvents(title) {
    chat_focus[title] = false;
    var chat_area = jQuery("#chatbox_"+prep4JQ(title)+" .chat-textarea");
    chat_area.blur(function(){
        chat_focus[title] = false;
        chat_area.removeClass('chat-textarea-selected');
    }).focus(function(){
        chat_focus[title] = true;
        chat_area.addClass('chat-textarea-selected');
    });

    var chatbox = jQuery("#chatbox_"+prep4JQ(title));
    chatbox.click(function() {
        if (chatbox.find('.chat-content').css('display') != 'none') {
            chatbox.find('.chat-textarea').focus();
        }
    });
}

function poll() {
    /* The way doTimout works, it will execute the code in the callback
    * function *after* poll_interval has passed.
    */
    jQuery.doTimeout('message_poll', poll_interval, function(){
        poll_server();
        if (messages_found > 0) {
            // Reset the poll
            log.info('resetting the poll');
            messages_found = 0;
            poll_count = 0;
            poll_interval = poll_min;
            poll();
            return;
        } 
        poll_count++;
        if (poll_count >= poll_cycle) { 
            if (poll_interval < poll_max)
                poll_interval *= 2;
                
            if (poll_interval > poll_max)
                poll_interval = poll_max;

            // Reset the poll
            poll_count = 0;
            poll();
            return;
        }
        return true;
    });
}

function poll_server() {
    path = sanitizePath('/@@babblechat/poll');
    jQuery.ajax({
        url: path,
        cache: false,
        async: true,
        timeout: timeout,
        dataType: "json",
        data: {username: username}, 
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            log.error(textStatus);
            log.error(errorThrown);
            // XXX: Don't output 'connection error' to the portlet
            /*
            for (var i=0; i<chats.length; i++) {
                var user = chats[i];
                content = jQuery("#chatbox_"+prep4JQ(user)+" .chat-content");
                content.append(
                    '<div class="chat-message">' + 
                        '<span class="chat-message-error">Connection Error</span>' + 
                    '</div>'
                );
                content.scrollTop(content[0].scrollHeight);
                poll_interval = poll_max; 
            }
            */
        },
        success: function(data) {
            if (Number(data.status)  == TIMEOUT) {
                // When the server times out while fetching messages, we have
                // to call initialize again, to get all uncleared_messages,
                // otherwise we might lose some messages that might have been
                // marked as read by the timed out process!

                // First, we have to cancel the existing poll, without
                // executing it's callback
                jQuery.doTimeout('message_poll');

                // No we start a poll calling getUnclearedMessages
                // getUnclearedMessages will determine wether this poll will
                // call again, or whether it will be replaced with the default
                // message_poll.
                jQuery.doTimeout('message_recovery_poll', poll_interval, function() {
                    getUnclearedMessages();
                });
            }
            for (var user in data.messages) {
                var messages = data.messages[user][1];
                if (!messages.length) 
                    continue
                var fullname = data.messages[user][0];
                log.info('We received messages for ' + fullname);
                appendMessages(user, fullname, messages, 0);
            };
        }
    });
}


function getUnclearedMessages() {
    /* If poll() times out, then we will have to call this method instead to
       get all uncleared messages, to avoid losing messages that were marked as
       read during the timed out process. 
    */
    path = sanitizePath('/@@babblechat/get_uncleared_messages');
    jQuery.ajax({
        url: path,
        cache: false,
        async: true,
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            log.error(textStatus);
            log.error(errorThrown);
            // This will let doTimout continue, i.e get_uncleared_messages will be called again.
            return true; 
        },
        success: function(data) {
            if (Number(data.status) == TIMEOUT) {
                // This will let doTimout continue, i.e get_uncleared_messages will be called again.
                return true; 
            }
            for(var username in data.messages) {
                var messages = data.messages[username][1];
                if (!messages.length) 
                    continue
                var tuple = data.messages[username]
                var fullname = data.messages[username][0];
                appendMessages(username, fullname, messages, 0, 1);
            };
            // Cancel the current poll
            jQuery.doTimeout('message_recovery_poll');
            // Now call the normal poll again
            poll_interval = poll_min;
            poll_count = 0
            poll();
        }
    });
}

function keypressed(event, textarea, title) {
	if(event.keyCode == 13 && event.shiftKey == 0) {
        var textbox = jQuery(textarea);
		var message = textbox.val();
		message = message.replace(/^\s+|\s+jQuery/g,"");
		textbox.val('').focus().css('height','44px');
		if (message != '') {
            path = sanitizePath('/@@babblechat/send_message');
            jQuery.ajax({
                url: path,
                cache: false,
                async: true,
                data: {to: title, message: message}, 
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    log.error(textStatus);
                    if (errorThrown)
                        log.error(errorThrown)

                    var chat_content = jQuery('#chatbox_'+prep4JQ(title)+' .chat-content');
                    chat_content.append(
                        '<div class="chat-message">' + 
                            '<span class="chat-message-error">Connection Error</span>' + 
                        '</div>');
                    chat_content.scrollTop(chat_content[0].scrollHeight);
                },
                success: function(data) { 
                    log.info("Message succesfully sent. \n");

                    message = message.replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;");
                    var now = new Date();
                    var minutes = now.getMinutes().toString();
                    if (minutes.length==1) {minutes = '0'+minutes;}
                    var time = now.toLocaleTimeString().substring(0,5);
                    var chat_content = jQuery('#chatbox_'+prep4JQ(title)+' .chat-content');
                    chat_content.append(
                        '<div class="chat-message">' + 
                            '<span class="chat-message-me">me '+time+':&nbsp;&nbsp;</span>' + 
                            '<span class="chat-message-content">'+message+'</span>' + 
                        '</div>');
                    chat_content.scrollTop(chat_content[0].scrollHeight);

                    poll_interval = poll_min;
                    poll_count = 0
                    poll(); // Calling poll, cancels the existing poll and replaces it with a new one 
                            // (with the updated poll values)
                }
            });
		}
	}
	var adjustedHeight = textarea.clientHeight;
	var maxHeight = 94;
	if (maxHeight > adjustedHeight) {
		adjustedHeight = Math.max(textarea.scrollHeight, adjustedHeight);
		if (maxHeight)
			adjustedHeight = Math.min(maxHeight, adjustedHeight);
		if (adjustedHeight > textarea.clientHeight)
			jQuery(textarea).css('height',adjustedHeight+8 +'px');
	} 
    else {
		jQuery(textarea).css('overflow','auto');
	}
}

function toggleChat(title) {
    var minimized_chats = getMinimizedChats();
    if (jQuery('#chatbox_'+prep4JQ(title)+' .chat-content').css('display') == 'none') {  
        // Chat will be maximized
        var new_cookie = Array();
        for (var i=0; i < minimized_chats.length; i++) {
            if (minimized_chats[i] != title) {
                new_cookie.push(minimized_chats[i]);
            }
        }
        jQuery.cookie('chats_minimized_'+username, new_cookie.join('|'));
        var chat_content = jQuery('#chatbox_'+prep4JQ(title)+' .chat-content');
        chat_content.css('display','block');
        chat_content.scrollTop(chat_content[0].scrollHeight);
        jQuery('#chatbox_'+prep4JQ(title)+' .chat-input').css('display','block');
    } 
    else {
        // Chat will be minimized
        if (!(title in oc(minimized_chats))) {
            var new_cookie = title;
            new_cookie += '|'+minimized_chats.join('|');
            jQuery.cookie('chats_minimized_'+username, new_cookie);
        }
        jQuery('#chatbox_'+prep4JQ(title)+' .chat-content').css('display','none');
        jQuery('#chatbox_'+prep4JQ(title)+' .chat-input').css('display','none');
    }
}

