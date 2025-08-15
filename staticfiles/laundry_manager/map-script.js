/**
 * ===================================================================
 * laundry-map.js
 * (주소 및 상품 토글 기능이 추가된 버전)
 * ===================================================================
 */

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

function refresh() { /* 이전과 동일 */ 
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
function openSheet(store, act) { /* 이전과 동일 */ }
function closeSheet() { /* 이전과 동일 */ sheet.classList.remove('open'); sheet.setAttribute('aria-hidden', 'true'); }
async function locateMe() { /* 이전과 동일 */ 
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
openBtn.addEventListener('click', () => { /* 이전과 동일 */ 
    state.openOnly = !state.openOnly;
    openBtn.classList.toggle('active', state.openOnly);
    openBtn.setAttribute('aria-pressed', state.openOnly);
    refresh();
});
[productFilter, centerSel, sortSel].forEach(sel => { /* 이전과 동일 */
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

