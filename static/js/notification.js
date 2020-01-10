var eventid = $('.eventid').attr('eventid');
console.log(eventid);

window.onload = function () {
  setInterval(function () {
    $.ajax({
      url: '/checkTime',
      type: 'post',
      contentType: 'application/json',
      data: JSON.stringify({ 'eventid': eventid }),
      success: function (data) {
        console.log(data);
        if (data == "True" && !$('#myModal').is(':visible')) {
          $('#modal').modal('show');
        }
        else if (data == "Expired") {
          window.location = '/booking';
        }
      }
    });
  }, 240000)
};
