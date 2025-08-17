// static/laundry_manager/dictionary-script.js

import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// --- 페이지 로드 애니메이션 ---
animate(".dictionary-page", { opacity: [0, 1] }, { duration: 0.5 });

// --- Swiper.js 캐러셀 초기화 ---
const swiper = new Swiper('.popular-swiper', {
    // 옵션
    slidesPerView: 1.1, 
    spaceBetween: 15,    
    centeredSlides: true, // 이 옵션이 슬라이드 위치를 안정화합니다.
    loop: true,          
    
    // 자동 재생
    autoplay: {
        delay: 3000,
        disableOnInteraction: false,
    },

    // 페이지네이션 (하단 점)
    pagination: {
        el: '.swiper-pagination',
        clickable: true,
    },
});

// --- 필터 칩 상호작용 ---
const chips = document.querySelectorAll('.filter-chips .chip');
chips.forEach(chip => {
    chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
    });
});

// --- 좋아요 버튼 상호작용 ---
const likeButtons = document.querySelectorAll('.like-btn');
const favoritesContainer = document.getElementById('favorites-container');

// 페이지 로드 시 기존 즐겨찾기 상태를 버튼에 반영하는 함수
function applyInitialFavoriteState() {
    const favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    const allItems = document.querySelectorAll('.info-grid-item');
    
    allItems.forEach(item => {
        const titleElement = item.querySelector('h4');
        if (!titleElement) return;

        const title = titleElement.textContent.trim();
        const likeButton = item.querySelector('.like-btn');
        const icon = likeButton.querySelector('i');
        
        if (favorites.includes(title)) {
            likeButton.classList.add('active');
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
        }
    });
}

// 즐겨찾기 탭의 내용을 업데이트하는 함수
function updateFavoritesTab() {
    let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

    if (!favoritesContainer) {
        return;
    }

    favoritesContainer.innerHTML = ''; // 기존 목록 초기화

    if (favorites.length === 0) {
        favoritesContainer.innerHTML = '<p id="no-favorites-message">즐겨찾기 없음</p>';
    } else {
        favorites.forEach(item => {
            let title, imageUrl, url;

            // 데이터가 객체인지, 문자열인지 확인하여 처리
            if (typeof item === 'string') {
                title = item;
                imageUrl = '';
                
                // ★★★ 이 부분을 수정하세요 ★★★
                // Django URL로 변환하기 위해 제목을 인코딩합니다.
                // 이 부분을 서버 측에서 처리하는 것이 더 안전하지만, 클라이언트 측에서 처리하는 방법입니다.
                const encodedTitle = encodeURIComponent(title);
                url = `/dictionary/${encodedTitle}`; 

            } else {
                // 새로운 방식 (객체)
                title = item.title;
                imageUrl = item.image_url;
                url = item.url;
            }

            const favoriteItem = document.createElement('a');
            favoriteItem.classList.add('info-grid-item', 'favorite-item');
            favoriteItem.href = url;

            favoriteItem.innerHTML = `
                ${imageUrl ? `<img src="${imageUrl}" alt="${title}">` : ''}
                <div class="item-content">
                    <h4>${title}</h4>
                    <button class="like-btn active"><i class="fa-solid fa-heart"></i></button>
                </div>
            `;
            favoritesContainer.appendChild(favoriteItem);
        });
    }
}

// Like button click event listener
// 좋아요 버튼 클릭 이벤트 리스너
likeButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        event.preventDefault(); 
        event.stopPropagation();
        
        const infoGridItem = button.closest('.info-grid-item');
        const itemTitle = infoGridItem.querySelector('h4').textContent.trim();
        
        // **새로 추가된 부분: 이미지 URL과 상세 페이지 URL 가져오기**
        const itemImage = infoGridItem.querySelector('img');
        const itemImageUrl = itemImage ? itemImage.src : '';
        const itemUrl = infoGridItem.getAttribute('href');

        let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

        // 즐겨찾기 목록에서 이미 존재하는지 확인
        const existingIndex = favorites.findIndex(fav => fav.title === itemTitle);

        if (existingIndex !== -1) {
            // 이미 즐겨찾기되어 있다면 제거
            favorites.splice(existingIndex, 1);
        } else {
            // 즐겨찾기 목록에 추가 (객체 형태로 저장)
            favorites.push({
                title: itemTitle,
                image_url: itemImageUrl,
                url: itemUrl
            });
        }

        // localStorage 업데이트
        localStorage.setItem('favorites', JSON.stringify(favorites));

        // ... 기존 버튼 UI 토글 로직 ...
        button.classList.toggle('active');
        const icon = button.querySelector('i');
        if (button.classList.contains('active')) {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
        } else {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
        }

        // 즐겨찾기 탭이 활성화되어 있다면 UI 업데이트
        if (favoritesContainer) {
            updateFavoritesTab();
        }
    });
});

// Apply initial favorite state and update the tab on page load
document.addEventListener('DOMContentLoaded', () => {
    applyInitialFavoriteState();
    updateFavoritesTab();
});

document.addEventListener('DOMContentLoaded', function() {
    const categories = document.querySelectorAll('.all-items');

    categories.forEach(category => {
        const items = category.querySelectorAll('.info-grid-item');
        const showMoreBtn = category.parentElement.querySelector('.show-more-btn');
        const showLessBtn = category.parentElement.querySelector('.show-less-btn');

        if (items.length > 3) {
            // 초기 상태: 4번째 아이템부터 숨기고 '더보기' 버튼만 보이게 함
            for (let i = 3; i < items.length; i++) {
                items[i].classList.add('hidden');
            }
            showMoreBtn.style.display = 'block';

            // 더보기 버튼 클릭 시
            showMoreBtn.addEventListener('click', function() {
                // 숨겨진 아이템을 모두 보여주고
                items.forEach(item => item.classList.remove('hidden'));
                // '더보기' 버튼 숨기기
                showMoreBtn.style.display = 'none';
                // '닫기' 버튼 보이기
                showLessBtn.style.display = 'block';
            });

            // 닫기 버튼 클릭 시
            showLessBtn.addEventListener('click', function() {
                // 4번째 아이템부터 다시 숨기고
                for (let i = 3; i < items.length; i++) {
                    items[i].classList.add('hidden');
                }
                // '닫기' 버튼 숨기기
                showLessBtn.style.display = 'none';
                // '더보기' 버튼 보이기
                showMoreBtn.style.display = 'block';
            });
        }
    });
});