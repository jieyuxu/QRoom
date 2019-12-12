window.onload = function(){
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition, error, options);
  } else { 
    alert("The application needs your current location to book a room.")
    window.location = '/profile';
  }
};

var options = {
  enableHighAccuracy: true,
  timeout: 5000,
  maximumAge: 0,
};

function error() {
  console.warn(`ERROR(${err.code}): ${err.message}`);
  alert("The application needs your current location to book a room.")
}

function showPosition(position) {
  var lat = position.coords.latitude;
  var long = position.coords.longitude;
  var building = $('.building').attr('building')
  // for testing purposes
  // console.log(lat);
  // console.log(long);
  // console.log(building);
  
  $.ajax({
    url: '/checkcoordinates',
    type: 'post',
    contentType: 'application/json',
    data: JSON.stringify({'latitude' : lat, 'longitude': long, 'building': building}),
    success: function(data) {      
       if (data != "") {
          alert(data)
          window.location = '/profile';
       }
    }
  });
}

