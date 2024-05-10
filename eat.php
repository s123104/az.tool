<!DOCTYPE html>
<html>

<head>
  <title>今天想吃什麼？</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="img/eat.ico" type="image/x-icon" />
  <?php
  $cssFile = array(
    'sass/eat.css'
  );

  for ($i = 0; $i < count($cssFile); $i++) {
    echo "<link rel='stylesheet' href='{$cssFile[$i]}'>";
  }
  ?>

</head>

<body>

  <div class="container">
    <h1>今天想吃什麼？</h1>
    <div class="control-container">
      <div>
        <p>選一個類別：</p>
        <select id="category-select">
          <option value="食物">食物</option>
          <option value="便當">便當</option>
          <option value="飯">飯</option>
          <option value="麵">麵</option>
          <option value="早餐">早餐</option>
          <option value="午餐">午餐</option>
          <option value="晚餐">晚餐</option>
          <option value="速食">速食</option>
          <option value="蔥抓餅">蔥抓餅</option>
          <option value="燒臘">燒臘</option>
          <option value="烤鴨">烤鴨</option>
          <option value="焗烤">焗烤</option>
          <option value="牛排">牛排</option>
          <option value="韓國料理">韓國料理</option>
          <option value="日本料理">日本料理</option>
          <option value="熱炒">熱炒</option>
          <option value="咖哩">咖哩</option>
          <option value="越南麵包">越南麵包</option>

        </select>
      </div>
      <div>
        <label for="range-input">搜尋範圍（公尺）：</label>
        <input type="range" id="range-input" min="100" max="5000" step="100" value="1000">
        <div id="range-value">1000</div>
      </div>
      <button onclick="getRandomRestaurant()">給我一個建議</button>
    </div>
    <div id="map"></div>
    <div id="restaurant-container"></div>
  </div>

  <script src="https://maps.googleapis.com/maps/api/js?key=<?php echo $_SERVER['GOOGLE_MAPS_API_KEY']; ?>&libraries=places"></script>

  <script>
    const rangeInput = document.getElementById('range-input');
    const rangeValue = document.getElementById('range-value');

    rangeInput.addEventListener('input', () => {
      rangeValue.textContent = rangeInput.value;
    });
  </script>
  <script>
    function getRandomRestaurant() {
      // 將環境變量中的 API 密鑰保存到變量中
      var apiKey = "<?php echo $_SERVER['GOOGLE_MAPS_API_KEY']; ?>";
      var category = document.getElementById("category-select").value;
      var request = {
        location: new google.maps.LatLng(24.117942576346717, 120.49402721328477),
        radius: rangeValue.textContent,
        query: category,
        fields: ['formatted_address', 'name', 'rating', 'url', 'place_id', 'photos']
      };

      // 將 API 密鑰添加到請求中
      if (apiKey) {
        request.key = apiKey;
      }

      var service = new google.maps.places.PlacesService(document.createElement('div'));
      service.textSearch(request, function(results, status) {
        if (status === google.maps.places.PlacesServiceStatus.OK) {
          var randomIndex = Math.floor(Math.random() * results.length);
          var place = results[randomIndex];
          var restaurantContainer = document.getElementById('restaurant-container');
          restaurantContainer.innerHTML = '';
          var restaurantDiv = document.createElement('div');
          restaurantDiv.classList.add('restaurant');
          var image = place.photos && place.photos.length > 0 ? '<img src="' + place.photos[0].getUrl({
            maxHeight: 150
          }) + '">' : '<img src="https://via.placeholder.com/150">';
          var name = '<a  href="https://www.google.com/maps/search/' + place.name + '" target="_blank" rel="noopener noreferrer">' + place.name + '</a>';
          var rating = place.rating ? '<div>評分：' + place.rating + '</div>' : '';
          var address = '<div>地址：<a href="https://www.google.com/maps/place/' + encodeURIComponent(place.formatted_address) + '"target="_blank" rel="noopener noreferrer">' + place.formatted_address + '</a></div>';
          restaurantDiv.innerHTML = image + '<div class="restaurant-info">' + name + rating + address + '</div>';
          restaurantContainer.appendChild(restaurantDiv);
          // Add marker to the map
          showResults([place]);

          // Get additional information with Place Details
          var placeDetailsRequest = {
            placeId: place.place_id,
            fields: ['photos']
          };
          service.getDetails(placeDetailsRequest, function(placeDetails, status) {
            if (status === google.maps.places.PlacesServiceStatus.OK && placeDetails && placeDetails.photos && placeDetails.photos.length > 0) {
              // Add photos to the restaurant element
              var photoContainer = document.createElement('div');
              photoContainer.classList.add('restaurant-photos');
              for (var i = 0; i < placeDetails.photos.length; i++) {
                var photoUrl = placeDetails.photos[i].getUrl({
                  maxWidth: 400
                });
                var photoElement = document.createElement('img');
                photoElement.src = photoUrl;
                photoContainer.appendChild(photoElement);
              }
              restaurantDiv.appendChild(photoContainer);
            }
          });
        }
      });
    }


    function showResults(results) {
      var map = new google.maps.Map(document.getElementById('map'), {
        center: results[0].geometry.location,
        zoom: 15,
      });
      for (var i = 0; i < results.length; i++) {
        var marker = new google.maps.Marker({
          position: results[i].geometry.location,
          map: map,
        });
      }
    }
  </script>
</body>

</html>