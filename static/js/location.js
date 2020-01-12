window.onload = function () {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, error, options);
    // this.checkPermission();
  } 
  else {
    alert('Geolocation is not supported for this Browser/OS.');
  }
};

var options = {
  enableHighAccuracy: true,
  timeout: 3000,
  
};

function checkPermission() {
  navigator.permissions.query({name:'geolocation'}).then(function(result) {
    if (result.state == 'granted') {
      // report(result.state);
      geoBtn.style.display = 'none';
      navigator.geolocation.watchPosition(showPosition, error, options);
    } else if (result.state == 'prompt') {
      // report(result.state);
      geoBtn.style.display = 'inline';
    } else if (result.state == 'denied') {
      report(result.state);
      geoBtn.style.display = 'inline';
    }
    result.onchange = function() {
      report(result.state);
    }
  });
}

function error(state) {
  // checkPermission();
  if (state.code == 1) {
    var r = confirm("Please turn on location services and allow QRoom to access your location. Click 'OK' once you've done so or click 'CANCEL' to return to your bookings page.");
    if (r == true) {
      location.reload();
    }
    else {
      window.location = '/booking'
    }
  }
  else {
    alert('There was an error acquiring your location. Refreshing...if this problem persists, clear your cache and try again.');
    location.reload();
  }
}

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
    alert('You are too far away to book this room.');
    window.location = "/booking";
  }
}
