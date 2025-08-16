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
    const favorites = JSON.parse(localStorage.getItem('favorites')) || [];
    
    // Check if the favorites container exists on the current page
    if (!favoritesContainer) {
        return;
    }

    favoritesContainer.innerHTML = ''; // Clear the existing list

    if (favorites.length === 0) {
        favoritesContainer.innerHTML = '<p id="no-favorites-message">아직 즐겨찾기한 항목이 없습니다.</p>';
    } else {
        favorites.forEach(title => {
            // Dynamically create a favorite item from local storage data
            const favoriteItem = document.createElement('div');
            favoriteItem.classList.add('info-grid-item', 'favorite-item');
            favoriteItem.innerHTML = `
                <div class="item-content">
                    <h4>${title}</h4>
                    </div>
            `;
            favoritesContainer.appendChild(favoriteItem);
        });
    }
}

// Like button click event listener
likeButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        event.preventDefault(); 
        event.stopPropagation();
        
        const infoGridItem = button.closest('.info-grid-item');
        const itemTitle = infoGridItem.querySelector('h4').textContent.trim();

        let favorites = JSON.parse(localStorage.getItem('favorites')) || [];

        // Add or remove data from local storage based on the favorite state
        if (button.classList.contains('active')) {
            favorites = favorites.filter(title => title !== itemTitle);
        } else {
            if (!favorites.includes(itemTitle)) {
                favorites.push(itemTitle);
            }
        }

        // Update local storage
        localStorage.setItem('favorites', JSON.stringify(favorites));

        // Toggle like button UI (existing code)
        button.classList.toggle('active');
        const icon = button.querySelector('i');
        if (button.classList.contains('active')) {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
        } else {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
        }

        // If the favorites tab is active, update the UI
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