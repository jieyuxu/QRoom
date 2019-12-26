var eventid = $('.eventid').attr('eventid');

window.onload = function() {
  setInterval(function(){

    $.ajax({
      url: '/checkTime',
      type: 'post',
      contentType: 'application/json',
      data: JSON.stringify({'eventid': eventid}),
      success: function(data) {
         if (data == "True") {
            $('#modal').modal('show');
         }
         else if (data == "Expired") {
           window.location = '/profile'
         }
      }
    });
  }, 300000)
};
