// static/laundry_manager/dictionary-script.js

import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// --- 페이지 로드 애니메이션 ---
animate(".dictionary-page", { opacity: [0, 1] }, { duration: 0.5 });

// --- Swiper.js 캐러셀 초기화 ---
const swiper = new Swiper('.popular-swiper', {
    // 옵션
    slidesPerView: 1.1, // 한 번에 1.1개씩 보이게 해서 옆 슬라이드가 살짝 보이도록
    spaceBetween: 15,   // 슬라이드 간 간격
    centeredSlides: true, // 활성 슬라이드를 가운데로
    loop: true,           // 무한 루프
    
    // 자동 재생
    autoplay: {
      delay: 3000, // 3초마다 자동 재생
      disableOnInteraction: false, // 사용자가 조작한 후에도 자동 재생 유지
    },

    // 페이지네이션 (하단 점)
    pagination: {
      el: '.swiper-pagination',
      clickable: true, // 점을 클릭해서 이동 가능
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
likeButtons.forEach(button => {
    button.addEventListener('click', (event) => {
        event.preventDefault(); // Prevents default link behavior
        event.stopPropagation(); // Stops event from bubbling up to parent elements
        if (userIsAuthenticated !== 'true') {
            alert('비회원은 즐겨찾기를 사용하실 수 없습니다!');
            return; // 여기서 함수 실행을 중단합니다.
        }
        const icon = button.querySelector('i');
        const isFavorite = icon.classList.contains('fa-solid'); // Check current state
        const itemTitle = button.closest('.info-grid-item').querySelector('h4').textContent.trim();

        fetch('/dictionary/toggle_favorite/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                title: itemTitle,
                is_favorite: !isFavorite // Send the toggled state to the server
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Explicitly add or remove classes based on the new state
                if (!isFavorite) {
                    // Item was NOT a favorite, now it is.
                    icon.classList.remove('fa-regular');
                    icon.classList.add('fa-solid');
                } else {
                    // Item WAS a favorite, now it is not.
                    icon.classList.remove('fa-solid');
                    icon.classList.add('fa-regular');
                }
            } else {
                console.error('서버 오류:', data.message);
            }
        })
        .catch(error => {
            console.error('네트워크 오류:', error);
        });
    });
});

// CSRF 토큰을 가져오는 함수 (Django 보안에 필요)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}