window.onload = function(){
  if (navigator.geolocation) {
    navigator.geolocation.watchPosition(showPosition, error, options);
  } else {
    alert("The application needs your current location to book a room.")
    window.location = '/profile';
  }
};

var options = {
  enableHighAccuracy: true,
  timeout: 5000,
  // maximumAge: 1000,
};

function error() {
  console.log("there is an error");
  // console.warn(`ERROR(${err.code}): ${err.message}`);
  alert("The application needs your current location to book a room.")
  window.location = '/profile';
}

function distance(lat1, lon1, lat2, lon2, unit) {
	if ((lat1 == lat2) && (lon1 == lon2)) {
		  return 0;
	}
	else {
  		var radlat1 = Math.PI * lat1/180;
  		var radlat2 = Math.PI * lat2/180;
  		var theta = lon1-lon2;
  		var radtheta = Math.PI * theta/180;
  		var dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta);
  		if (dist > 1) {
  			dist = 1;
  		}
  		dist = Math.acos(dist);
  		dist = dist * 180/Math.PI;
  		dist = dist * 60 * 1.1515;
  		if (unit=="K") { dist = dist * 1.609344; }
  		if (unit=="N") { dist = dist * 0.8684; }
  		return dist;
	}
}

function showPosition(position) {
  console.log("hi");
  var building = $('.building').attr('building');
  var lat1 = position.coords.latitude;
  var long1 = position.coords.longitude;
  var lat2 = $('.lat').attr('latitude');
  var long2 = $('.long').attr('longitude');
  var dist = distance(lat1, long1, lat2, long2, "K");
  // for testing purposes
  // console.log(lat2);
  // console.log(long2);
  // console.log(building);
  // console.log(dist);
  if (dist > 0.1) {
    alert('You are too far away to book this room.');
    window.location = "/profile";
  }
}
