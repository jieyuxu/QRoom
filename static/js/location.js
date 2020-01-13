window.onload = function () {
  try {
    navigator.permissions.query({name:'geolocation'}).then(function(result) {
      if (result.state == 'prompt') {
        $("#myModal").modal({
          backdrop: 'static',
          keyboard: false,
        });
        $('#modal-message').html('Please allow this application to use your location. If you are on a mobile device, please turn on your GPS. Closing this alert will refresh this page so that your location can be obtained.');
        $('#myModal').modal('show');
        // location.reload();
      } 
      if (result.state == 'granted') {
        navigator.geolocation.watchPosition(showPosition, error, options);
      }
    });
  }
  catch(e) {
    console.log('Browser not compatible with Permissions API, likely Safari');
  }

  if (navigator.geolocation) {
    navigator.geolocation.watchPosition(showPosition, error, options);
  } else {
    $("#myModal").modal({
      backdrop: 'static',
      keyboard: false,
    });
    $('#myModal button').attr('onclick', "window.location='/booking'");
    $('#modal-message').html('Geolocation is not supported for this Browser/OS.');
    $('#myModal').modal('show');    
  }
};

var options = {
  enableHighAccuracy: true,
  timeout: 5000,
  maximumAge: 600000,
};

function distance(lat1, lon1, lat2, lon2, unit) {
  if ((lat1 == lat2) && (lon1 == lon2)) {
    return 0;
  }
  else {
    var radlat1 = Math.PI * lat1 / 180;
    var radlat2 = Math.PI * lat2 / 180;
    var theta = lon1 - lon2;
    var radtheta = Math.PI * theta / 180;
    var dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta);
    if (dist > 1) {
      dist = 1;
    }
    dist = Math.acos(dist);
    dist = dist * 180 / Math.PI;
    dist = dist * 60 * 1.1515;
    if (unit == "K") { dist = dist * 1.609344; }
    if (unit == "N") { dist = dist * 0.8684; }
    return dist;
  }
}

function showPosition(position) {
  console.log('Calculating user position...');
  var building = $('.building').attr('building');
  var lat1 = position.coords.latitude;
  var long1 = position.coords.longitude;
  var lat2 = $('.lat').attr('latitude');
  var long2 = $('.long').attr('longitude');
  var dist = distance(lat1, long1, lat2, long2, "K");
  // console.log(dist);
  // for testing purposes
  // console.log(lat2);
  // console.log(long2);
  // console.log(building);
  // console.log(dist);

  if (dist > 0.2) {
    var timer;
    $("#myModal").modal({
      backdrop: 'static',
      keyboard: false,
    });
    $('#modal-message').html('You are too far away to book this room.');
    $('#myModal button').attr('onclick', "window.location='/booking'");
    $('#myModal').modal('show');

    // window.location = "/booking";
  }
}

function error(state) {
  $('.modal').modal('hide');

  console.log('An error has occurred.');
  console.log(state.code);
  if (state.code == 1) {
    var r = confirm("Please turn on location services and allow QRoom to access your location. Click 'OK' once you've done so or click 'CANCEL' to return to your bookings page.");
    if (r == true) {
      navigator.permissions.query({name:'geolocation'}).then(function(result) {
        if (result.state == 'prompt') {
          $("#myModal").modal({
            backdrop: 'static',
            keyboard: false,
          });
          $('#modal-message').html('Please allow this application to use your location. If you are on a mobile device, please turn on your GPS. Closing this alert will refresh this page so that your location can be obtained.');
          $('#myModal').modal('show');
        }
      }); 
      navigator.geolocation.watchPosition(showPosition, error, options);
    }
    else {
      window.location = '/booking'
    }
  }
  else {
    $("#myModal").modal({
      backdrop: 'static',
      keyboard: false,
    });
    alert('There was an error acquiring your location. Refreshing to your bookings in 10 seconds. If this problem persists, clear your cache and try again.');
    location.reload();
  }
}

