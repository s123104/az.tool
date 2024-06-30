function saveApiKey() {
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        alert('請輸入API密鑰');
        return;
    }
    document.cookie = `googleApiKey=${apiKey}; path=/`;
    alert('API密鑰已保存');
}

function getApiKeyFromCookie() {
    const name = 'googleApiKey=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return '';
}

function saveCompanyName(name) {
    let history = JSON.parse(localStorage.getItem('history')) || [];
    if (!history.includes(name)) {
        history.push(name);
        localStorage.setItem('history', JSON.stringify(history));
        updateHistoryList();
    }
}

function updateHistoryList() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '';
    let history = JSON.parse(localStorage.getItem('history')) || [];
    history.forEach(name => {
        const li = document.createElement('li');
        li.textContent = name;
        li.onclick = () => {
            document.getElementById('companyName').value = name;
            fetchReviews();
        };
        historyList.appendChild(li);
    });
}

async function fetchReviews() {
    const apiKey = getApiKeyFromCookie();
    if (!apiKey) {
        alert('請先輸入並保存API密鑰');
        return;
    }

    const companyName = document.getElementById('companyName').value;
    if (!companyName) {
        alert('請輸入公司名稱');
        return;
    }

    saveCompanyName(companyName);

    try {
        console.log(`使用的API密鑰: ${apiKey}`);
        console.log(`正在查找公司: ${companyName}`);

        const placeResponse = await fetch(`https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=${encodeURIComponent(companyName)}&inputtype=textquery&fields=place_id&key=${apiKey}`);
        if (!placeResponse.ok) {
            throw new Error(`Place API響應錯誤: ${placeResponse.statusText}`);
        }
        const placeData = await placeResponse.json();

        console.log('Place API響應數據:', placeData);

        if (placeData.status !== 'OK') {
            alert(`找不到公司名稱: ${placeData.status}`);
            return;
        }

        if (!placeData.candidates || placeData.candidates.length === 0) {
            alert('找不到公司名稱');
            return;
        }

        const placeId = placeData.candidates[0].place_id;
        console.log(`找到的Place ID: ${placeId}`);

        const reviewResponse = await fetch(`https://maps.googleapis.com/maps/api/place/details/json?place_id=${placeId}&fields=reviews,photos&key=${apiKey}`);
        if (!reviewResponse.ok) {
            throw new Error(`Review API響應錯誤: ${reviewResponse.statusText}`);
        }
        const reviewData = await reviewResponse.json();

        console.log('Review API響應數據:', reviewData);

        if (reviewData.status !== 'OK') {
            alert(`無法獲取評論: ${reviewData.status}`);
            return;
        }

        if (!reviewData.result || !reviewData.result.reviews) {
            alert('無法獲取評論');
            return;
        }

        const reviews = reviewData.result.reviews;
        const photos = reviewData.result.photos;

        const fiveStarReviews = reviews.filter(review => review.rating === 5).slice(0, 10);
        const oneStarReviews = reviews.filter(review => review.rating === 1).slice(0, 10);

        displayReviews(fiveStarReviews, oneStarReviews);
        displayPhotos(photos.slice(0, 5), apiKey);
    } catch (error) {
        console.error('請求失敗:', error);
        alert('請求失敗');
    }
}

function displayReviews(fiveStarReviews, oneStarReviews) {
    const fiveStarList = document.getElementById('fiveStarReviews');
    const oneStarList = document.getElementById('oneStarReviews');

    fiveStarList.innerHTML = '';
    oneStarList.innerHTML = '';

    fiveStarReviews.forEach(review => {
        const li = document.createElement('li');
        li.className = 'five-star';
        li.innerHTML = `<i class="fas fa-thumbs-up"></i><img src="https://via.placeholder.com/40" alt="avatar">${review.text}`;
        fiveStarList.appendChild(li);
    });

    oneStarReviews.forEach(review => {
        const li = document.createElement('li');
        li.className = 'one-star';
        li.innerHTML = `<i class="fas fa-thumbs-down"></i><img src="https://via.placeholder.com/40" alt="avatar">${review.text}`;
        oneStarList.appendChild(li);
    });
}

function displayPhotos(photos, apiKey) {
    const photoList = document.getElementById('photoList');
    photoList.innerHTML = '';

    photos.forEach(photo => {
        const img = document.createElement('img');
        const photoUrl = `https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=${photo.photo_reference}&key=${apiKey}`;
        img.src = photoUrl;
        photoList.appendChild(img);
    });
}

// 自動填充API密鑰輸入框和更新歷史搜索列表（如果已經存在於cookie和本地存儲中）
window.onload = function() {
    const apiKey = getApiKeyFromCookie();
    if (apiKey) {
        document.getElementById('apiKey').value = apiKey;
    }
    updateHistoryList();
};