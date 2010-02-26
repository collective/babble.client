jQuery(document).ready(function() {

    jQuery("#chatpanel").adjustPanel(); 

    //Each time the viewport is adjusted/resized, execute the function
    jQuery(window).resize(function () {
        jQuery("#chatpanel").adjustPanel();
    });

    //Click event outside of subpanel
    jQuery(document).click(function() { 
        jQuery(".subpanel").hide(); 
        jQuery("#footpanel li a").removeClass('active'); //remove active class on subpanel trigger
    });
    jQuery('.subpanel ul').click(function(e) {
        e.stopPropagation(); //Prevents the subpanel ul from closing on click
    });

    //Click event on Chat Panel
    jQuery("#chatpanel a:first").click(function() { 
        if(jQuery(this).next(".subpanel").is(':visible')){ 
            jQuery(this).next(".subpanel").hide(); 
            jQuery("#footpanel li a").removeClass('active'); 
        }
        else { 
            //if subpanel is not active...
            jQuery(this).next(".subpanel").toggle(); 
            jQuery("#footpanel li a").removeClass('active'); 
            jQuery(this).toggleClass('active'); 
        }
        return false; //Prevent browser jump to link anchor
    });

    //Show/Hide delete icons on Alert Panel
    jQuery("#alertpanel li").hover(function() {
        jQuery(this).find("a.delete").css({'visibility': 'visible'}); //Show delete icon on hover
    },function() {
        jQuery(this).find("a.delete").css({'visibility': 'hidden'}); //Hide delete icon on hover out
    });
});

