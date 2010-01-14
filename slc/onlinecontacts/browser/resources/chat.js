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
var poll_count = 0;         // The amount of server polls that have been made
var poll_max = 30001;       // The maximum polling period
var poll_min = 5000;        // The minimum polling period
var poll_time = poll_min;   // The initial polling period
var username;
var window_focus = true;
var chat_focus = new Array();
var has_messages = new Array();
var new_chats = new Array();
var chats = new Array();

function initialize(){  
	jQuery.ajax({
	  url: "@@start_session",
	  cache: false,
	  dataType: "json",
	  success: function(data) {
		username = data.username;
		jQuery.each(data.items, function(i,item) {
			if (item)	{ // fix strange ie bug
                title = item.f;
                if (jQuery("#chatbox_"+title).length <= 0) {
                    createChat(title, 1);
                }
                if (item.s == 1) {
                    item.f = username;
                }
                if (item.s == 2) {
                    jQuery("#chatbox_"+title+" .chat-content").append(
                        '<div class="chat-message">' + 
                            '<span class="chat-info">'+item.m+'</span>' +
                        '</div>');
                } 
                else {
                    jQuery("#chatbox_"+title+" .chat-content").append(
                        '<div class="chat-message">' + 
                            '<span class="chat-message-from">'+item.f+':&nbsp;&nbsp;</span>' + 
                            '<span class="chat-message-content">'+item.m+'</span>' + 
                        '</div>');
                }
            }
		});
		for (i=0; i<chats.length; i++) {
			title = chats[i];
			jQuery("#chatbox_"+title+" .chat-content").scrollTop(jQuery("#chatbox_"+title+" .chat-content")[0].scrollHeight);
            // yet another strange ie bug
			setTimeout('jQuery("#chatbox_"+title+" .chat-content").scrollTop(jQuery("#chatbox_"+title+" .chat-content")[0].scrollHeight);', 100); 
		}
	setTimeout('poll();', poll_time);
	}});
}

function reorderChats() {
	index = 0;
    for (i=0; i < chats.length; i++) {
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
}

function startChat(contact) {
	createChat(contact);
	jQuery("#chatbox_"+contact+" .chat-textarea").focus();
}

function createChat(title, minimize) {
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
            '<a href="javascript:void(0)" onclick="javascript:toggleChatGrowth(\''+title+'\')">-</a>' +
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

    for (i=0;i<chats.length;i++) {
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

		if (jQuery.cookie('chatbox_minimized')) {
			minimized_chats = jQuery.cookie('chatbox_minimized').split(/\|/);
		}
		minimize = 0;
		for (j=0; j < minimized_chats.length; j++) {
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
    var chats_found = 0;
    if (window_focus == false) {
        var blink_number = 0;
        var title_changed = 0;
        for (i = 0; i < new_chats.length; i++) {
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
        for (i = 0; i < new_chats.length; i++) {
            new_chats[i] = false;
        }
    }
    for (i = 0; i < new_chats.length; i++) {
        if (has_messages[i] == true) {
            if (chat_focus[i] == false) {
                //FIXME: toggle all or none policy
                jQuery('#chatbox_'+ i +' .chat-head').toggleClass('chat-blink');
            }
        }
    }
    jQuery.ajax({
        url: "@@poll",
        cache: false,
        dataType: "json",
        success: function(data) {
            jQuery.each(data.items, function(i,item){
                if (item)	{ // fix IE bug
                    title = item.f;
                    if (jQuery("#chatbox_"+title).length <= 0) {
                        createChat(title);
                    }
                    if (jQuery("#chatbox_"+title).css('display') == 'none') {
                        jQuery("#chatbox_"+title).css('display','block');
                        reorderChats();
                    }
                    if (item.s == 1) {
                        item.f = username;
                    }
                    if (item.s == 2) {
                        jQuery("#chatbox_"+title+" .chat-content")
                        .append('<div class="chat-message"><span class="chat-info">'+item.m+'</span></div>');
                    } else {
                        has_messages[title] = true;
                        new_chats[title] = true;
                        jQuery("#chatbox_"+title+" .chat-content")
                        .append(
                            '<div class="chat-message">' + 
                                '<span class="chat-message-from">'+item.f+':&nbsp;&nbsp;</span>' + 
                                '<span class="chat-message-content">'+item.m+'</span>' + 
                            '</div>'
                        );
                    }
                    jQuery("#chatbox_"+title+" .chat-content").scrollTop(jQuery("#chatbox_"+title+" .chat-content")[0].scrollHeight);
                    chats_found += 1;
                }
            });
            poll_count++;

            if (chats_found > 0) {
                poll_time = poll_min;
                poll_count = 1;
            } 
            else if (poll_count >= 10) {
                poll_time *= 2;
                poll_count = 1;
                if (poll_time > poll_max) {
                    poll_time = poll_max;
                }
            }
            setTimeout('poll();', poll_time);
        }
    });
}

function toggleChatGrowth(title) {
	if (jQuery('#chatbox_'+title+' .chat-content').css('display') == 'none') {  
		var minimized_chats = new Array();
		if (jQuery.cookie('chatbox_minimized')) {
			minimized_chats = jQuery.cookie('chatbox_minimized').split(/\|/);
		}
		var new_cookie = '';
		for (i=0; i < minimized_chats.length; i++) {
			if (minimized_chats[i] != title) {
				new_cookie += title+'|';
			}
		}
		new_cookie = new_cookie.slice(0, -1)
		jQuery.cookie('chatbox_minimized', new_cookie);
		jQuery('#chatbox_'+title+' .chat-content').css('display','block');
		jQuery('#chatbox_'+title+' .chat-input').css('display','block');
		jQuery("#chatbox_"+title+" .chat-content").scrollTop(jQuery("#chatbox_"+title+" .chat-content")[0].scrollHeight);
	} 
    else {
		var new_cookie = title;
		if (jQuery.cookie('chatbox_minimized')) {
			new_cookie += '|'+jQuery.cookie('chatbox_minimized');
		}
		jQuery.cookie('chatbox_minimized', new_cookie);
		jQuery('#chatbox_'+title+' .chat-content').css('display','none');
		jQuery('#chatbox_'+title+' .chat-input').css('display','none');
	}
}

function keypressed(event, textarea, title, username) {
	if(event.keyCode == 13 && event.shiftKey == 0)  {
		message = jQuery(textarea).val();
		message = message.replace(/^\s+|\s+jQuery/g,"");
		jQuery(textarea).val('');
		jQuery(textarea).focus();
		jQuery(textarea).css('height','44px');
		if (message != '') {
			jQuery.post("@@send_chat", {to: title, message: message} , function() {
				message = message.replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;");
				jQuery("#chatbox_"+title+" .chat-content").append(
                    '<div class="chat-message">' + 
                        '<span class="chat-message-from">'+username+':&nbsp;&nbsp;</span>' + 
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
