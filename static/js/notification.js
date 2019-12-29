var eventid = $('.eventid').attr('eventid');
console.log(eventid);

window.onload = function() {
  setInterval(function(){
    $.ajax({
      url: '/checkTime',
      type: 'post',
      contentType: 'application/json',
      data: JSON.stringify({'eventid': eventid}),
      success: function(data) {
        console.log(data);
         if (data == "True" && !$('#myModal').is(':visible')) {
            $('#modal').modal('show');
         }
         else if (data == "Expired") {
           window.location = '/profile';
         }
      }
    });
  }, 6000)
};

document.getElementById("extend-button").onclick = function(){
  console.log('sending request to extend stay');
  $.ajax({
    url: '/extendStay',
    type: 'post',
    contentType: 'application/json',
    data: JSON.stringify({'eventid': eventid}),
    success: function(data) {
      console.log(data);
      window.location = data;
    }
  });
};
