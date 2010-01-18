/*
GNU General Public License (GPL)

This program is free software; you can redistribute it and/or
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

var blink_order = 0;
var doc_title;
var messages_found = 0;
var poll_count = 0;         // The amount of server polls that have been made
var poll_max = 33000;       // The maximum polling period
var poll_min = 2000;        // The minimum polling period
var poll_time = poll_min;   // The initial polling period
var username;

var window_focus = true;
var chat_focus = new Array();
var has_messages = new Array();
var new_chats = new Array();
var chats = new Array();    // Records new chat windows being opened. 

function initialize(){  
    var cookie = jQuery.cookie('chats_open');
    jQuery.cookie('chats_open', '');
    if (cookie) {
        var cookie_chats = cookie.split('|');
        for (var i=0; i<cookie_chats.length; i++) {
            var user = cookie_chats[i];
            if (user) { 
                createChat(user);
            }
        }
    }
    jQuery.ajax({
        url: "@@start_session",
        cache: false,
        dataType: "json",
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            setTimeout('initialize();', 10000); // If an error occured, call initialize again after 10 seconds.
        },
        success: function(data) {
            username = data.username;
            jQuery.each(data.items, function(i,item) {
                if (item)	{ // IE bug
                    var user = item.user;
                    if (item.messages.length) {
                        messages_found += 1;
                        has_messages[user] = true;
                        new_chats[user] = true;
                        var chat = jQuery("#chatbox_"+user);
                        if (chat.length <= 0) {
                            createChat(user, 1);
                        }
                        if (chat.css('display') == 'none') {
                            chat.css('display','block');
                            reorderChats();
                        }
                        var chat_content = jQuery("#chatbox_"+user+" .chat-content");
                        for (var i=0; i<item.messages.length; i++) {
                            message = item.messages[i]
                            chat_content.append(
                                '<div class="chat-message">' + 
                                    '<span class="chat-message-them">'+user+' '+message[1]+':&nbsp;&nbsp;</span>' + 
                                    '<span class="chat-message-content">'+message[2]+'</span>' + 
                                '</div>'
                            );
                        }
                        chat_content.scrollTop(chat_content[0].scrollHeight);
                        setTimeout('chat_content.scrollTop(chat_content[0].scrollHeight);', 100); // IE bug
                    }
                }
            });
        }
    });
    setTimeout('poll();', poll_time);
}

function reorderChats() {
    index = 0;
    for (var i=0; i < chats.length; i++) {
        title = chats[i];
        if (jQuery("#chatbox_"+title).css('display') != 'none') {
            if (index == 0) {
                jQuery("#chatbox_"+title).css('right', '20px');
            } 
            else {
                width = (index)*(225+7)+20;
                jQuery("#chatbox_"+title).css('right', width+'px');
            }
            index++;
        }
    }
}

function closeChat(title) {
    jQuery('#chatbox_'+title).css('display','none');
    reorderChats();

    var open_chats = jQuery.cookie('chats_open').split('|');
    var new_chats = Array();
    for (var i=0; i < open_chats.length; i++) {
        if (open_chats[i] != title) {
            new_chats.push(open_chats[i]);
        }
    }
    jQuery.cookie('chats_open', new_chats.join('|'));
}

function startChat(contact) {
    createChat(contact);
    jQuery("#chatbox_"+contact+" .chat-textarea").focus();
}

function createChat(title, minimize) {
    var open_chats = jQuery.cookie('chats_open').split('|');
    open_chats.push(title);
    jQuery.cookie('chats_open', open_chats.join('|'));

    if (jQuery("#chatbox_"+title).length > 0) {
        if (jQuery("#chatbox_"+title).css('display') == 'none') {
            jQuery("#chatbox_"+title).css('display','block');
            reorderChats();
        }
        jQuery("#chatbox_"+title+" .chat-textarea").focus();
        return;
    }
    jQuery(" <div />" ).attr("id","chatbox_"+title)
    .addClass("chatbox")
    .html(
    '<div class="chat-head">' +
        '<div class="chat-title">'+title+'</div>' +
        '<div class="chat-options">' +
            '<a href="javascript:void(0)" onclick="javascript:toggleChat(\''+title+'\')">-</a>' +
            '<a href="javascript:void(0)" onclick="javascript:closeChat(\''+title+'\')">X</a>' +
        '</div>' + 
        '<br clear="all"/>' +
    '</div>' +
    '<div class="chat-content"></div>'+ 
    '<div class="chat-input">' +
        '<textarea class="chat-textarea"' + 
            'onkeydown="javascript:return keypressed(event, this,\''+title+'\', \''+username+'\');">' +
        '</textarea>' + 
    '</div>')
    .appendTo(jQuery( "body" ));
                
    chatbox = jQuery("#chatbox_"+title)
    chatbox.css('bottom', '0px');
    num_chats = 0;

    for (var i=0;i<chats.length;i++) {
        if (jQuery("#chatbox_"+chats[i]).css('display') != 'none') {
            num_chats++;
        }
    }

    if (num_chats == 0) {
        chatbox.css('right', '20px');
    } 
    else {
        width = (num_chats)*(225+7)+20;
        chatbox.css('right', width+'px');
    }
    chats.push(title);

    if (minimize == 1) {
        minimized_chats = new Array();
        if (jQuery.cookie('chats_minimized')) {
            minimized_chats = jQuery.cookie('chats_minimized').split(/\|/);
        }
        minimize = 0;
        for (var j=0; j < minimized_chats.length; j++) {
            if (minimized_chats[j] == title) {
                minimize = 1;
            }
        }
        if (minimize == 1) {
            jQuery('#chatbox_'+title+' .chat-content').css('display','none');
            jQuery('#chatbox_'+title+' .chat-input').css('display','none');
        }
    }
    chat_focus[title] = false;

    jQuery("#chatbox_"+title+" .chat-textarea").blur(function(){
        chat_focus[title] = false;
        jQuery("#chatbox_"+title+" .chat-textarea").removeClass('chat-textarea-selected');
    }).focus(function(){
        chat_focus[title] = true;
        has_messages[title] = false;
        jQuery('#chatbox_'+title+' .chat-head').removeClass('chat-blink');
        jQuery("#chatbox_"+title+" .chat-textarea").addClass('chat-textarea-selected');
    });

    jQuery("#chatbox_"+title).click(function() {
        if (jQuery('#chatbox_'+title+' .chat-content').css('display') != 'none') {
            jQuery("#chatbox_"+title+" .chat-textarea").focus();
        }
    });
    chatbox.show();
}

function poll(){
    if (window_focus == false) {
        var blink_number = 0;
        var title_changed = 0;
        for (var i = 0; i < new_chats.length; i++) {
            if (new_chats[i] == true) {
                ++blink_number;
                if (blink_number >= blink_order) {
                    document.title = i+' says...';
                    title_changed = 1;
                    break;	
                }
            }
        }
        if (title_changed == 0) {
            document.title = doc_title;
            blink_order = 0;
        } 
        else {
            ++blink_order;
        }
    } 
    else {
        for (var i = 0; i < new_chats.length; i++) {
            new_chats[i] = false;
        }
    }
    for (var i = 0; i < new_chats.length; i++) {
        if (has_messages[i] == true) {
            if (chat_focus[i] == false) {
                //FIXME: toggle all or none policy
                jQuery('#chatbox_'+ i +' .chat-head').toggleClass('chat-blink');
            }
        }
    }
    poll_server();

    poll_count++;
    if (messages_found > 0) {
        poll_time = poll_min;
        poll_count = 1;
        messages_found = 0;
    } 
    else if ((poll_count >= 10) && (poll_time < poll_max)) {
        poll_time *= 2;
        poll_count = 1;
        if (poll_time > poll_max) {
            poll_time = poll_max;
        }
    }
    setTimeout('poll();', poll_time);
}

function poll_server() {
    jQuery.ajax({
        url: "@@poll",
        cache: false,
        dataType: "json",
        data: {user: username},
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            for (var i=0; i<chats.length; i++) {
                user = chats[i]
                content = jQuery("#chatbox_"+user+" .chat-content");
                content.append(
                    '<div class="chat-message">' + 
                        '<span class="chat-message-error">Connection Error</span>' + 
                    '</div>'
                );
                content.scrollTop(content[0].scrollHeight);
                poll_count += 10; // Dramatically increase the poll count to prevent the screen filling up with errrors.
            }
        },
        success: function(data) {
            jQuery.each(data.items, function(i,item){
                if (item)	{ // fix IE bug
                    user = item.user;
                    if (item.messages.length) {
                        messages_found += 1;
                        has_messages[user] = true;
                        new_chats[user] = true;
                        var chat = jQuery("#chatbox_"+user);
                        if (chat.length <= 0) {
                            createChat(user);
                        }
                        if (chat.css('display') == 'none') {
                            chat.css('display','block');
                            reorderChats();
                        }
                        var chat_content = jQuery("#chatbox_"+user+" .chat-content");
                        for (var i=0; i<item.messages.length; i++) {
                            message = item.messages[i]
                            chat_content.append(
                                '<div class="chat-message">' + 
                                    '<span class="chat-message-them">'+user+' '+message[1]+':&nbsp;&nbsp;</span>' + 
                                    '<span class="chat-message-content">'+message[2]+'</span>' + 
                                '</div>'
                            );
                        }
                        chat_content.scrollTop(chat_content[0].scrollHeight);
                    }
                }
            });
        }
    });
}

function keypressed(event, textarea, title, username) {
	if(event.keyCode == 13 && event.shiftKey == 0)  {
		message = jQuery(textarea).val();
		message = message.replace(/^\s+|\s+jQuery/g,"");
		jQuery(textarea).val('');
		jQuery(textarea).focus();
		jQuery(textarea).css('height','44px');
		if (message != '') {
			jQuery.post("@@send_message", {user: username, to: title, message: message} , function() {
				message = message.replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;");
                var now = new Date();
                var time = now.getHours()+':'+now.getMinutes();
				jQuery("#chatbox_"+title+" .chat-content").append(
                    '<div class="chat-message">' + 
                        '<span class="chat-message-me">'+username+' '+time+':&nbsp;&nbsp;</span>' + 
                        '<span class="chat-message-content">'+message+'</span>' + 
                    '</div>');
				jQuery("#chatbox_"+title+" .chat-content").scrollTop(jQuery("#chatbox_"+title+" .chat-content")[0].scrollHeight);
			});
		}
		poll_time = poll_min;
		poll_count = 1;
		return false;
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
	if (jQuery('#chatbox_'+title+' .chat-content').css('display') == 'none') {  
		var minimized_chats = new Array();
		if (jQuery.cookie('chats_minimized')) {
			minimized_chats = jQuery.cookie('chats_minimized').split(/\|/);
		}
		var new_cookie = '';
		for (var i=0; i < minimized_chats.length; i++) {
			if (minimized_chats[i] != title) {
				new_cookie += title+'|';
			}
		}
		new_cookie = new_cookie.slice(0, -1)
		jQuery.cookie('chats_minimized', new_cookie);
		jQuery('#chatbox_'+title+' .chat-content').css('display','block');
		jQuery('#chatbox_'+title+' .chat-input').css('display','block');
		jQuery("#chatbox_"+title+" .chat-content").scrollTop(jQuery("#chatbox_"+title+" .chat-content")[0].scrollHeight);
	} 
    else {
		var new_cookie = title;
		if (jQuery.cookie('chats_minimized')) {
			new_cookie += '|'+jQuery.cookie('chats_minimized');
		}
		jQuery.cookie('chats_minimized', new_cookie);
		jQuery('#chatbox_'+title+' .chat-content').css('display','none');
		jQuery('#chatbox_'+title+' .chat-input').css('display','none');
	}
}

/* Copyright (c) 2006 Klaus Hartl (stilbuero.de) */
jQuery.cookie = function(name, value, options) {
    if (typeof value != 'undefined') { // name and value given, set cookie
        options = options || {};
        if (value === null) {
            value = '';
            options.expires = -1;
        }
        var expires = '';
        if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
            var date;
            if (typeof options.expires == 'number') {
                date = new Date();
                date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
            } else {
                date = options.expires;
            }
            expires = '; expires=' + date.toUTCString(); // use expires attribute, max-age is not supported by IE
        }
        // CAUTION: Needed to parenthesize options.path and options.domain
        // in the following expressions, otherwise they evaluate to undefined
        // in the packed version for some reason...
        var path = options.path ? '; path=' + (options.path) : '';
        var domain = options.domain ? '; domain=' + (options.domain) : '';
        var secure = options.secure ? '; secure' : '';
        document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
    } 
    else { // only name given, get cookie
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};

