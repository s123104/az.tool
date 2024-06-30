
function saveApiKey() {
    const apiKey = document.getElementById('apiKey').value;
    if (!apiKey) {
        console.error('請輸入API密鑰');
        return;
    }
    document.cookie = `googleApiKey=${apiKey}; path=/`;
    console.log('API密鑰已保存');
    document.getElementById('apiSection').style.display = 'none';
}

function saveApiKeyModal() {
    const apiKey = document.getElementById('apiKeyModal').value;
    if (!apiKey) {
        console.error('請輸入API密鑰');
        return;
    }
    document.cookie = `googleApiKey=${apiKey}; path=/`;
    console.log('API密鑰已保存');
    document.getElementById('apiSectionModal').style.display = 'none';
}

function showApiKeyInput() {
    document.getElementById('apiSectionModal').style.display = 'block';
    document.getElementById('changeApiKeyButtonModal').style.display = 'none';
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
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.textContent = name;
        td.onclick = () => {
            document.getElementById('companyName').value = name;
            fetchReviews();
            toggleUtilityModal();
        };
        tr.appendChild(td);
        historyList.appendChild(tr);
    });
}

function toggleUtilityModal() {
    const modal = document.getElementById('utilityModal');
    modal.style.display = modal.style.display === "block" ? "none" : "block";
}

async function fetchReviews() {
    const apiKey = getApiKeyFromCookie();
    if (!apiKey) {
        console.error('請先輸入並保存API密鑰');
        return;
    }

    const companyName = document.getElementById('companyName').value;
    if (!companyName) {
        console.error('請輸入公司名稱');
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
            console.error(`找不到公司名稱: ${placeData.status}`);
            return;
        }

        if (!placeData.candidates || placeData.candidates.length === 0) {
            console.error('找不到公司名稱');
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
            console.error(`無法獲取評論: ${reviewData.status}`);
            return;
        }

        if (!reviewData.result || !reviewData.result.reviews) {
            console.error('無法獲取評論');
            return;
        }

        const reviews = reviewData.result.reviews;
        const photos = reviewData.result.photos;

        const goodReviews = reviews.filter(review => review.rating >= 4).slice(0, 20);
        const badReviews = reviews.filter(review => review.rating <= 3).slice(0, 20);

        displayReviews(goodReviews, 'goodReviews', 'good-review', '查無好評');
        displayReviews(badReviews, 'badReviews', 'bad-review', '查無差評');
        displayPhotos(photos.slice(0, 6), apiKey);
        await fetchPttLinks(companyName);

        document.getElementById('companyTitle').textContent = companyName;
    } catch (error) {
        console.error('請求失敗:', error);
    }
}

function displayReviews(reviews, elementId, className, emptyMessage) {
    const reviewList = document.getElementById(elementId);
    if (!reviewList) {
        console.error(`元素未找到: ${elementId}`);
        return;
    }
    reviewList.innerHTML = '';

    if (reviews.length === 0) {
        const li = document.createElement('li');
        li.textContent = emptyMessage;
        reviewList.appendChild(li);
        return;
    }

    reviews.forEach((review, index) => {
        const li = document.createElement('li');
        li.className = className;
        li.innerHTML = `${className === 'good-review' ? '<i class="fas fa-thumbs-up"></i>' : '<i class="fas fa-thumbs-down"></i>'}${review.rating} 星 - ${review.text}`;
        if (index >= 5) {
            li.style.display = 'none';
        }
        reviewList.appendChild(li);
    });

    if (reviews.length > 5) {
        const showMore = document.createElement('button');
        showMore.className = 'show-more';
        showMore.textContent = '顯示更多';
        showMore.onclick = () => {
            reviewList.querySelectorAll('li').forEach((li, index) => {
                if (index >= 5) {
                    li.style.display = 'flex';
                }
            });
            showMore.style.display = 'none';
        };
        reviewList.appendChild(showMore);
    }
}

function displayPhotos(photos, apiKey) {
    const photoList = document.getElementById('photoList');
    if (!photoList) {
        console.error('元素未找到: photoList');
        return;
    }
    photoList.innerHTML = '';

    photos.forEach(photo => {
        const img = document.createElement('img');
        const photoUrl = `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${photo.photo_reference}&key=${apiKey}`;
        img.src = photoUrl;
        photoList.appendChild(img);
    });
}

async function fetchPttLinks(companyName) {
    try {
        const response = await fetch(`https://www.ptt.cc/bbs/search?q=${encodeURIComponent(companyName)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'text/html',
            }
        });
        if (!response.ok) {
            throw new Error(`PTT API響應錯誤: ${response.statusText}`);
        }
        const data = await response.text();
        console.log('PTT 搜索結果:', data);

        const parser = new DOMParser();
        const doc = parser.parseFromString(data, 'text/html');
        const links = Array.from(doc.querySelectorAll('.title a')).slice(0, 5);

        const pttLinks = document.getElementById('pttLinks');
        if (!pttLinks) {
            console.error('元素未找到: pttLinks');
            return;
        }
        pttLinks.innerHTML = '';

        if (links.length === 0) {
            document.getElementById('pttTitle').style.display = 'none';
            return;
        }

        links.forEach(link => {
            const li = document.createElement('li');
            li.innerHTML = `<a href="https://www.ptt.cc${link.getAttribute('href')}" target="_blank">${link.textContent}</a>`;
            pttLinks.appendChild(li);
        });
    } catch (error) {
        console.error('PTT連結請求失敗:', error);
        document.getElementById('pttTitle').style.display = 'none';
    }
}

// 自動填充API密鑰輸入框和更新歷史搜索列表（如果已經存在於cookie和本地存儲中）
window.onload = function() {
    const apiKey = getApiKeyFromCookie();
    if (apiKey) {
        document.getElementById('apiKey').value = apiKey;
        document.getElementById('apiSection').style.display = 'none';
    }
    updateHistoryList();
    };