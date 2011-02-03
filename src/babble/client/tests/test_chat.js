module('chat', {
    setup: function() {
    },
    teardown: function() {
    }
});

function oc(a) {
    // Helper function
    var o = {};
    for(var i=0; i<a.length; i++) {
        o[a[i]]='';
    }
    return o;
}

function get_minimized_chats() {
    // Helper function
    if (jQuery.cookie('chats_minimized'))
        return jQuery.cookie('chats_minimized').split(/\|/);
    return Array()
}
  
test('createChatBox()', function() {
    var username =  'patrick@mail.com';

    //First we test that the chatbox is not yet created
    equals(jQuery("#chatbox_"+prep4JQ(username)).length, 0, "The chatbox should not yet exist");

    // We then create it and make sure that it is there
    var returned_chatbox = createChatBox(username);
    var generated_checkbox = jQuery("#chatbox_"+prep4JQ(username));
    equals(generated_checkbox.length, 1, "The chatbox should now exist");
    
    equals(generated_checkbox.attr('id'), returned_chatbox.attr('id'), "The returned chatbox should be the same as the jqueried one");

    // var display = $('#chatbox_'+title+' .chat-content').css('display');
    // equals(display, 'block', "The chatbox's display should be 'block'");
})

/*
test('toggleChat()', function() {
    var title =  'chat-1';
    equals($('#chatbox_'+title).length, 1, "The chatbox should still exist");

    var min_chats = get_minimized_chats()
    equals(min_chats.length, 0, "The minimized_chats cookie should not have any entries");

    var display = $('#chatbox_'+title+' .chat-content').css('display');
    equals(display, 'block', "The chatbox's display should still be 'block'");

    toggleChat(title);
    
    var display = $('#chatbox_'+title+' .chat-content').css('display');
    equals(display, 'none', "The chatbox's display should now be 'none'");

    var min_chats = get_minimized_chats()
    ok(min_chats.length, "The minimized_chats cookie must now have an entry");
    ok(title in oc(min_chats), "The chatbox should be in the minimized_chats cookie'");

    toggleChat(title);
    var display = $('#chatbox_'+title+' .chat-content').css('display');
    equals(display, 'block', "The chatbox's display should now be 'block'");

    var min_chats = get_minimized_chats()
    equals(min_chats.length, 0, "The minimized_chats cookie should not have any entries");

})
*/

