/**
 * ===================================================================
 * laundry-map.js
 * (주소 및 상품 토글 기능이 추가된 버전)
 * ===================================================================
 */

/*
import { animate, stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// (데이터 정의, DOM 요소 선택, 지도 설정 등 이전 코드는 동일)
const stores = [
    { id: 'a1', name: '클린워시 빨래방', rating: 4.6, openNow: true, coord: [37.5667, 126.9780], address: '서울 중구 세종대로 110', products: ['셀프 빨래방','운동화 세탁','이불세탁', '드라이클리닝'], phone: '02-123-4567' },
    { id: 'b2', name: '현대세탁소', rating: 4.4, openNow: false, coord: [37.5635, 126.9770], address: '서울 중구 태평로1가 31', products: ['드라이클리닝','수선'], phone: '02-111-2222' },
    { id: 'c3', name: '스피드런드리', rating: 4.8, openNow: true, coord: [37.5656, 126.9822], address: '서울 중구 명동길 14', products: ['셀프 빨래방','드라이클리닝','운동화 세탁'], phone: '02-987-6543' },
    { id: 'd4', name: '이불킹 세탁', rating: 4.2, openNow: true, coord: [37.5682, 126.9860], address: '서울 종로구 종로 19', products: ['이불세탁','드라이클리닝'], phone: '02-555-7777' }
];
const openBtn = document.getElementById('openNowBtn');
const productFilter = document.getElementById('productFilter');
const centerSel = document.getElementById('centerMode');
const sortSel = document.getElementById('sortMode');
const listEl = document.getElementById('storeList');
const sheet = document.getElementById('sheet');
const sheetTitle = document.getElementById('sheetTitle');
const sheetBody = document.getElementById('sheetBody');
const closeSheetBtn = document.querySelector('.close-sheet-btn');
const map = L.map('map', { zoomControl: false }).setView([37.5665, 126.9780], 15);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(map);
L.control.zoom({ position: 'bottomright' }).addTo(map);
const markers = new Map();
const state = { openOnly: false, product: '', centerMode: 'map', sortMode: 'distance', myCoord: null };

function renderMarkers(data) {
    markers.forEach(marker => map.removeLayer(marker));
    markers.clear();
    data.forEach(store => {
        const marker = L.marker(store.coord).addTo(map).bindPopup(`<b>${store.name}</b>`);
        markers.set(store.id, marker);
    });
}

// ==========================================================
// 👇 renderList 함수가 개선되었습니다.
// ==========================================================
function renderList(data) {
    listEl.innerHTML = '';
    data.forEach(store => {
        const el = document.createElement('article');
        el.className = 'store-card';
        
        // 주소에서 '동' 부분만 추출 (예: '세종대로' 또는 '화양동')
        const addressParts = store.address.split(' ');
        const neighborhood = addressParts.length > 2 ? addressParts[2] : addressParts[1];

        el.innerHTML = `
            <div class="thumb" aria-hidden="true"></div>
            <div>
                <div class="title-row">
                    <div class="title">${store.name}</div>
                    <div class="rating"><i class="fa-solid fa-star"></i> ${store.rating.toFixed(1)}</div>
                </div>

                <div class="meta">
                    <span>${store.openNow ? '영업중' : '영업종료'} · 연중무휴</span>
                    <div class="address-summary">
                        <span>${fmtMeters(store.distance)} · ${neighborhood}</span>
                        <button class="toggle-btn toggle-address" aria-label="주소 펼치기">▼</button>
                    </div>
                    <div class="address-full" style="display:none;">${store.address}</div>
                </div>

                <div class="chips">
                    ${store.products.slice(0, 2).map(p => `<span class="small-chip">${p}</span>`).join('')}
                    ${store.products.length > 2 ? '<button class="toggle-btn toggle-products" aria-label="상품 더보기">▼</button>' : ''}
                </div>
                <div class="product-list-full" style="display:none;">
                    ${store.products.map(p => `<span class="small-chip">${p}</span>`).join('')}
                </div>
                
                <div class="actions">
                    <a class="btn" href="tel:${store.phone}"><i class="fa-solid fa-phone"></i>전화</a>
                    <a class="btn primary" target="_blank" href="https://map.kakao.com/link/to/${store.name},${store.coord[0]},${store.coord[1]}">길찾기</a>
                </div>
            </div>`;
        
        el.addEventListener('click', (e) => {
            // 토글 버튼 클릭 시에는 지도 이동 방지
            if (e.target.classList.contains('toggle-btn')) return;

            const mk = markers.get(store.id);
            if (mk) {
                map.setView(store.coord, 16);
                mk.openPopup();
            }
        });
        listEl.appendChild(el);
    });
    animate('.store-card', { opacity: [0, 1], y: [10, 0] }, { delay: stagger(0.05) });
}
*/
/*
function refresh() { 
    const center = (state.centerMode === 'me' && state.myCoord) ? state.myCoord : map.getCenter();
    const centerArr = [center.lat ?? center[0], center.lng ?? center[1]];
    let data = stores
        .filter(s => !state.openOnly || s.openNow)
        .filter(s => !state.product || s.products.includes(s.product))
        .map(s => ({ ...s, distance: dist(s.coord, centerArr) }));
    data.sort((a, b) => state.sortMode === 'distance' ? a.distance - b.distance : b.rating - a.rating);
    renderMarkers(data);
    renderList(data);
}
function openSheet(store, act) {  }
function closeSheet() {  sheet.classList.remove('open'); sheet.setAttribute('aria-hidden', 'true'); }
async function locateMe() {
    if (!navigator.geolocation) return;
    return new Promise(resolve => {
        navigator.geolocation.getCurrentPosition(
            (pos) => { state.myCoord = [pos.coords.latitude, pos.coords.longitude]; map.setView(state.myCoord, 15); resolve(); },
            () => resolve(),
            { enableHighAccuracy: true, timeout: 5000 }
        );
    });
}


// ==========================================================
// 👇 이벤트 리스너가 개선되었습니다. (이벤트 위임)
// ==========================================================
openBtn.addEventListener('click', () => { 
    state.openOnly = !state.openOnly;
    openBtn.classList.toggle('active', state.openOnly);
    openBtn.setAttribute('aria-pressed', state.openOnly);
    refresh();
});
[productFilter, centerSel, sortSel].forEach(sel => { 
    sel.addEventListener('change', async () => {
        const key = sel.id.replace('Filter', '').replace('Mode', '');
        state[key] = sel.value;
        if (sel.id === 'centerMode' && sel.value === 'me') await locateMe();
        refresh();
    });
});
sheet.addEventListener('click', (e) => { if (e.target === sheet) closeSheet(); });
closeSheetBtn.addEventListener('click', closeSheet);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSheet(); });
map.on('moveend', () => { if (state.centerMode === 'map') refresh(); });

// 💡 새로운 토글 버튼들을 위한 이벤트 리스너 추가
listEl.addEventListener('click', function(e) {
    const target = e.target;
    if (!target.classList.contains('toggle-btn')) return;

    // 클릭된 버튼이 속한 카드 요소를 찾습니다.
    const card = target.closest('.store-card');
    if (!card) return;

    // 주소 토글 버튼 처리
    if (target.classList.contains('toggle-address')) {
        const fullAddress = card.querySelector('.address-full');
        const isHidden = fullAddress.style.display === 'none';
        fullAddress.style.display = isHidden ? 'block' : 'none';
        target.textContent = isHidden ? '▲' : '▼';
    }

    // 상품 토글 버튼 처리
    if (target.classList.contains('toggle-products')) {
        const fullProductList = card.querySelector('.product-list-full');
        const isHidden = fullProductList.style.display === 'none';
        fullProductList.style.display = isHidden ? 'flex' : 'none'; // flex로 설정하여 chip들이 가로로 나열되게 함
        target.textContent = isHidden ? '▲' : '▼';
    }
});

const R = 6371;
function toRad(d) { return d * Math.PI / 180; }
function dist(a, b) {
    const [lat1, lon1] = a, [lat2, lon2] = b;
    const dLat = toRad(lat2 - lat1), dLon = toRad(lon2 - lon1);
    const t = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 2 * R * 1000 * Math.asin(Math.sqrt(t));
}
function fmtMeters(m) { return m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(1)}km`; }

// (초기 로드 및 헬퍼 함수들은 이전과 동일)
animate('.map-page', { opacity: [0, 1] }, { duration: 0.5 });
refresh();
locateMe().then(() => { if (state.centerMode === 'me') refresh(); }); 
*/

/*
import { animate, stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// 1. Django View에서 전달한 데이터를 파싱하여 전역 변수 'stores'에 할당
// (기존 하드코딩된 stores 배열 대신 이 코드를 사용합니다.)
const stores = JSON.parse(document.getElementById('stores-data').textContent);

// 2. HTML에서 제어할 요소들을 가져옴 (기존과 동일)
const openBtn = document.getElementById('openNowBtn');
const productFilter = document.getElementById('productFilter');
const centerSel = document.getElementById('centerMode');
const sortSel = document.getElementById('sortMode');
const listEl = document.getElementById('storeList');
const sheet = document.getElementById('sheet');
const sheetTitle = document.getElementById('sheetTitle');
const sheetBody = document.getElementById('sheetBody');
const closeSheetBtn = document.querySelector('.close-sheet-btn');

// 3. 네이버 지도 초기화 (Leaflet.js -> Naver Maps)
const map = new naver.maps.Map('map', {
    center: new naver.maps.LatLng(37.5665, 126.9780), // 초기 중심 좌표 (서울 시청)
    zoom: 15,
    zoomControl: true,
    zoomControlOptions: {
        position: naver.maps.Position.BOTTOM_RIGHT
    }
});

// 4. 전역 변수 및 상태 관리 객체
const markers = new Map();
const infoWindows = new Map(); // 네이버 지도 InfoWindow 관리를 위해 추가
const state = { openOnly: false, product: '', centerMode: 'map', sortMode: 'distance', myCoord: null };


 //지도에 마커들을 렌더링하는 함수 (Leaflet.js -> Naver Maps)

function renderMarkers(data) {
    markers.forEach(marker => marker.setMap(null));
    markers.clear();
    infoWindows.clear();
    
    data.forEach(store => {
        const position = new naver.maps.LatLng(store.coord[0], store.coord[1]);
        
        const marker = new naver.maps.Marker({
            position: position,
            map: map,
            title: store.name
        });

        const infoWindow = new naver.maps.InfoWindow({
            content: `<div style="padding:5px 10px; font-weight:bold; font-size:14px; border: 1px solid #555;">${store.name}</div>`
        });

        markers.set(store.id, marker);
        infoWindows.set(store.id, infoWindow);

        naver.maps.Event.addListener(marker, 'click', () => {
            infoWindows.forEach(iw => iw.close());
            infoWindow.open(map, marker);
        });
    });
}


//사이드바에 가게 목록을 렌더링하는 함수 (기존과 거의 동일, 길찾기 링크만 수정)

function renderList(data) {
    listEl.innerHTML = '';
    data.forEach(store => {
        const el = document.createElement('article');
        el.className = 'store-card';
        const addressParts = store.address.split(' ');
        const neighborhood = addressParts.length > 2 ? addressParts[2] : addressParts[1];

        el.innerHTML = `
            <div class="thumb" aria-hidden="true"></div>
            <div>
                <div class="title-row">
                    <div class="title">${store.name}</div>
                    <div class="rating"><i class="fa-solid fa-star"></i> ${store.rating ? store.rating.toFixed(1) : '평점없음'}</div>
                </div>

                <div class="meta">
                    <span>${store.openNow ? '영업중' : '영업종료'} · 연중무휴</span>
                    <div class="address-summary">
                        <span>${fmtMeters(store.distance)} · ${neighborhood}</span>
                        <button class="toggle-btn toggle-address" aria-label="주소 펼치기">▼</button>
                    </div>
                    <div class="address-full" style="display:none;">${store.address}</div>
                </div>

                <div class="chips">
                    ${store.products.slice(0, 2).map(p => `<span class="small-chip">${p}</span>`).join('')}
                    ${store.products.length > 2 ? '<button class="toggle-btn toggle-products" aria-label="상품 더보기">▼</button>' : ''}
                </div>
                <div class="product-list-full" style="display:none;">
                    ${store.products.map(p => `<span class="small-chip">${p}</span>`).join('')}
                </div>
                
                <div class="actions">
                    <a class="btn" href="tel:${store.phone}"><i class="fa-solid fa-phone"></i>전화</a>
                    <a class="btn primary" target="_blank" href="https://map.naver.com/p/directions/-/,,,${store.name},,ADDRESS,${store.coord[1]},${store.coord[0]}">길찾기</a>
                </div>
            </div>`;
        
        el.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-btn')) return;

            const marker = markers.get(store.id);
            const infoWindow = infoWindows.get(store.id);
            if (marker && infoWindow) {
                map.setCenter(marker.getPosition());
                map.setZoom(17, true);
                infoWindows.forEach(iw => iw.close());
                infoWindow.open(map, marker);
            }
        });
        listEl.appendChild(el);
    });
    animate('.store-card', { opacity: [0, 1], y: [10, 0] }, { delay: stagger(0.05) });
}


//현재 상태에 따라 데이터를 필터링/정렬하고 화면을 다시 그리는 메인 함수

function refresh() {
    let center;
    if (state.centerMode === 'me' && state.myCoord) {
        center = new naver.maps.LatLng(state.myCoord[0], state.myCoord[1]);
    } else {
        center = map.getCenter();
    }
    
    // 네이버 지도 API의 lat(), lng() 메서드 사용
    const centerArr = [center.lat(), center.lng()];
    
    let data = stores
        .filter(s => !state.openOnly || s.openNow)
        .filter(s => !state.product || s.products.includes(state.product))
        .map(s => ({ ...s, distance: dist(s.coord, centerArr) }));

    data.sort((a, b) => state.sortMode === 'distance' ? a.distance - b.distance : b.rating - a.rating);
    
    renderMarkers(data);
    renderList(data);
}

// openSheet, closeSheet 함수는 필요 시 여기에 추가 (기존 코드와 동일)

//사용자의 현재 위치를 찾는 함수 (Leaflet.js -> Naver Maps)

async function locateMe() {
    if (!navigator.geolocation) {
        alert('이 브라우저에서는 위치 정보를 사용할 수 없습니다.');
        return;
    }
    
    return new Promise(resolve => {
        navigator.geolocation.getCurrentPosition(
            (pos) => { 
                state.myCoord = [pos.coords.latitude, pos.coords.longitude];
                const currentPosition = new naver.maps.LatLng(state.myCoord[0], state.myCoord[1]);
                map.setCenter(currentPosition);
                map.setZoom(15, true);
                resolve();
            },
            () => { alert('위치 정보를 가져오는 데 실패했습니다.'); resolve(); },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    });
}


 //두 좌표 간의 거리를 미터(m) 단위로 계산하는 함수 (자체 계산 -> Naver Maps API)

function dist(a, b) {
    const p1 = new naver.maps.LatLng(a[0], a[1]);
    const p2 = new naver.maps.LatLng(b[0], b[1]);
    return p1.distanceTo(p2); // 네이버 지도 내장 함수 사용
}


//미터(m)를 형식에 맞게 문자열로 변환하는 함수 (기존과 동일)

function fmtMeters(m) { return m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(1)}km`; }


// --- 이벤트 리스너 설정 (map.on('moveend') 부분만 수정) ---

openBtn.addEventListener('click', () => {
    state.openOnly = !state.openOnly;
    openBtn.classList.toggle('active', state.openOnly);
    openBtn.setAttribute('aria-pressed', state.openOnly);
    refresh();
});

[productFilter, centerSel, sortSel].forEach(sel => {
    sel.addEventListener('change', async () => {
        const key = sel.id.replace('Filter', '').replace('Mode', '');
        if (key === 'product') {
            state[key] = sel.options[sel.selectedIndex].text;
            if (state[key] === '모든 상품') state[key] = '';
        } else {
            state[key] = sel.value;
        }

        if (sel.id === 'centerMode' && sel.value === 'me') {
            await locateMe();
        }
        refresh();
    });
});

// 지도 드래그가 끝나면 지도 중심 기준으로 새로고침 (Leaflet.js -> Naver Maps)
map.addListener('dragend', () => { 
    if (state.centerMode === 'map') {
        refresh();
    }
});

// 이벤트 위임을 사용한 토글 버튼 리스너 (기존과 동일)
listEl.addEventListener('click', function(e) {
    const target = e.target;
    if (!target.classList.contains('toggle-btn')) return;
    const card = target.closest('.store-card');
    if (!card) return;

    if (target.classList.contains('toggle-address')) {
        const fullAddress = card.querySelector('.address-full');
        const isHidden = fullAddress.style.display === 'none';
        fullAddress.style.display = isHidden ? 'block' : 'none';
        target.textContent = isHidden ? '▲' : '▼';
    }

    if (target.classList.contains('toggle-products')) {
        const fullProductList = card.querySelector('.product-list-full');
        const isHidden = fullProductList.style.display === 'none';
        fullProductList.style.display = isHidden ? 'flex' : 'none';
        target.textContent = isHidden ? '▲' : '▼';
    }
});

// sheet, closeSheetBtn 관련 이벤트 리스너는 필요 시 여기에 추가 (기존 코드와 동일)

// --- 초기 실행 ---
animate('.map-page', { opacity: [0, 1] }, { duration: 0.5 });
refresh();
locateMe().then(() => { if (state.centerMode === 'me') refresh(); });
*/
// laundry_manager/static/laundry_manager/map-script.js

// laundry_manager/static/laundry_manager/map-script.js

import { animate, stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// 지도 API가 모두 로드된 후 실행되도록 전체 코드를 감쌉니다.
naver.maps.onJSContentLoaded = function() {
    
    const rawStoresData = JSON.parse(document.getElementById('stores-data').textContent);
    let stores = [];

    // HTML 요소 선택
    const openBtn = document.getElementById('openNowBtn');
    const productFilter = document.getElementById('productFilter');
    const centerSel = document.getElementById('centerMode');
    const sortSel = document.getElementById('sortMode');
    const listEl = document.getElementById('storeList');

    let map; 
    const markers = new Map();
    const infoWindows = new Map();
    const state = { openOnly: false, product: '', centerMode: 'map', sortMode: 'distance', myCoord: null };

    // --- 함수 정의 ---

    function geocode(address) {
        return new Promise((resolve) => {
            naver.maps.Service.geocode({ query: address }, (status, response) => {
                if (status === naver.maps.Service.Status.OK && response.v2.addresses.length > 0) {
                    const lat = parseFloat(response.v2.addresses[0].y);
                    const lng = parseFloat(response.v2.addresses[0].x);
                    resolve([lat, lng]);
                } else {
                    console.error(`Geocoding 실패: ${address}`);
                    resolve(null);
                }
            });
        });
    }

    async function initializeMapAndStores() {
        state.myCoord = await locateMe();
        
        const startCoord = state.myCoord ? new naver.maps.LatLng(state.myCoord[0], state.myCoord[1]) : new naver.maps.LatLng(37.5665, 126.9780);
        map = new naver.maps.Map('map', {
            center: startCoord,
            zoom: 15,
            zoomControl: false,
            zoomControlOptions: { position: naver.maps.Position.BOTTOM_RIGHT }
        });

        const geocodingPromises = rawStoresData.map(async (store) => {
            const coordinates = await geocode(store.address);
            return { ...store, coord: coordinates };
        });

        stores = await Promise.all(geocodingPromises);

        refresh();
        
        // ▼▼▼ 여기가 핵심입니다. map 객체가 생성된 후에 이벤트 리스너를 추가합니다. ▼▼▼
        map.addListener('dragend', () => { 
            if (state.centerMode === 'map') {
                refresh(); 
            }
        });
    }

    function renderMarkers(data) {
        markers.forEach(marker => marker.setMap(null));
        markers.clear();
        infoWindows.clear();
        data.forEach(store => {
            const position = new naver.maps.LatLng(store.coord[0], store.coord[1]);
            const marker = new naver.maps.Marker({ position, map, title: store.name });
            const infoWindow = new naver.maps.InfoWindow({ content: `<div style="padding:5px 10px; font-weight:bold; font-size:14px; border: 1px solid #555;">${store.name}</div>` });
            markers.set(store.id, marker);
            infoWindows.set(store.id, infoWindow);
            naver.maps.Event.addListener(marker, 'click', () => {
                infoWindows.forEach(iw => iw.close());
                infoWindow.open(map, marker);
            });
        });
    }

    function renderList(data) {
        listEl.innerHTML = '';
        data.forEach(store => {
            const el = document.createElement('article');
            el.className = 'store-card';
            const addressParts = store.address.split(' ');
            const neighborhood = addressParts.length > 2 ? addressParts[2] : addressParts[1];
            el.innerHTML = `
                <div class="thumb" aria-hidden="true"></div>
                <div>
                    <div class="title-row">
                        <div class="title">${store.name}</div>
                        <div class="rating"><i class="fa-solid fa-star"></i> ${store.rating ? store.rating.toFixed(1) : '평점없음'}</div>
                    </div>
                    <div class="meta">
                        <span>${store.openNow ? '영업중' : '영업종료'} · 연중무휴</span>
                        <div class="address-summary">
                            <span>${fmtMeters(store.distance)} · ${neighborhood}</span>
                            <button class="toggle-btn toggle-address" aria-label="주소 펼치기">▼</button>
                        </div>
                        <div class="address-full" style="display:none;">${store.address}</div>
                    </div>
                    <div class="chips">
                        ${store.products.slice(0, 2).map(p => `<span class="small-chip">${p}</span>`).join('')}
                        ${store.products.length > 2 ? '<button class="toggle-btn toggle-products" aria-label="상품 더보기">▼</button>' : ''}
                    </div>
                    <div class="product-list-full" style="display:none;">
                        ${store.products.map(p => `<span class="small-chip">${p}</span>`).join('')}
                    </div>
                    <div class="actions">
                        <a class="btn" href="tel:${store.phone}"><i class="fa-solid fa-phone"></i>전화</a>
                        <a class="btn primary" target="_blank" href="https://map.naver.com/p/directions/-/,,,${store.name},,ADDRESS,${store.coord[1]},${store.coord[0]}">길찾기</a>
                    </div>
                </div>`;
            el.addEventListener('click', (e) => {
                if (e.target.classList.contains('toggle-btn')) return;
                const marker = markers.get(store.id);
                const infoWindow = infoWindows.get(store.id);
                if (marker && infoWindow) {
                    map.setCenter(marker.getPosition());
                    map.setZoom(17, true);
                    infoWindows.forEach(iw => iw.close());
                    infoWindow.open(map, marker);
                }
            });
            listEl.appendChild(el);
        });
        animate('.store-card', { opacity: [0, 1], y: [10, 0] }, { delay: stagger(0.05) });
    }

    function refresh() {
        if (!map) return;
        let center = (state.centerMode === 'me' && state.myCoord) ? new naver.maps.LatLng(state.myCoord[0], state.myCoord[1]) : map.getCenter();
        const centerArr = [center.lat(), center.lng()];
        
        let data = stores
            .filter(s => s && s.coord)
            .filter(s => !state.openOnly || s.openNow)
            .filter(s => !state.product || s.products.includes(state.product))
            .map(s => ({ ...s, distance: dist(s.coord, centerArr) }));
        
            
        data.sort((a, b) => state.sortMode === 'distance' ? a.distance - b.distance : b.rating - a.rating);
        renderMarkers(data);
        renderList(data);
    }

    function locateMe() {
        return new Promise(resolve => {
            if (!navigator.geolocation) {
                alert('이 브라우저에서는 위치 정보를 사용할 수 없습니다.');
                return resolve(null);
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => { 
                    const coords = [pos.coords.latitude, pos.coords.longitude];
                    resolve(coords);
                },
                () => { alert('위치 정보를 가져오는 데 실패했습니다.'); resolve(null); },
                { enableHighAccuracy: true, timeout: 5000 }
            );
        });
    }

// 기존 dist 함수를 아래 코드로 교체하세요.

    function toRad(d) {
        return d * Math.PI / 180;
    }

    function dist(a, b) {
        if (!a || !b) return Infinity;

        const R = 6371e3; // 지구 반지름 (미터 단위)
        const [lat1, lon1] = a;
        const [lat2, lon2] = b;

        const dLat = toRad(lat2 - lat1);
        const dLon = toRad(lon2 - lon1);

        const t = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);

        const c = 2 * Math.atan2(Math.sqrt(t), Math.sqrt(1 - t));

        return R * c; // 최종 거리 (미터)
}

    function fmtMeters(m) { return m < 1000 ? `${Math.round(m)}m` : `${(m / 1000).toFixed(1)}km`; }

    // --- 이벤트 리스너 설정 ---
    openBtn.addEventListener('click', () => {
        state.openOnly = !state.openOnly;
        openBtn.classList.toggle('active', state.openOnly);
        openBtn.setAttribute('aria-pressed', state.openOnly);
        refresh();
    });
    [productFilter, centerSel, sortSel].forEach(sel => {
        sel.addEventListener('change', async () => {
            // state 객체의 키는 'product', 'centerMode', 'sortMode' 입니다.
            // sel.id가 'centerMode' 또는 'sortMode' 이므로 그대로 키로 사용합니다.
            const key = sel.id === 'productFilter' ? 'product' : sel.id;

            if (key === 'product') {
                state[key] = sel.options[sel.selectedIndex].text;
                if (state[key] === '모든 상품') state[key] = '';
            } else {
                // key는 'centerMode' 또는 'sortMode'가 됩니다.
                state[key] = sel.value;
            }

            if (key === 'centerMode' && sel.value === 'me') {
                state.myCoord = await locateMe();
                if(state.myCoord && map) {
                    map.setCenter(new naver.maps.LatLng(state.myCoord[0], state.myCoord[1]));
                }
            }
            refresh();
        });
    });
    listEl.addEventListener('click', function(e) {
        const target = e.target;
        if (!target.classList.contains('toggle-btn')) return;
        const card = target.closest('.store-card');
        if (!card) return;
        if (target.classList.contains('toggle-address')) {
            const fullAddress = card.querySelector('.address-full');
            const isHidden = fullAddress.style.display === 'none';
            fullAddress.style.display = isHidden ? 'block' : 'none';
            target.textContent = isHidden ? '▲' : '▼';
        }
        if (target.classList.contains('toggle-products')) {
            const fullProductList = card.querySelector('.product-list-full');
            const isHidden = fullProductList.style.display === 'none';
            fullProductList.style.display = isHidden ? 'flex' : 'none';
            target.textContent = isHidden ? '▲' : '▼';
        }
    });

    // --- 초기 실행 ---
    animate('.map-page', { opacity: [0, 1] }, { duration: 0.5 });
    initializeMapAndStores();
};