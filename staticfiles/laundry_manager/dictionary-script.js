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
    button.addEventListener('click', () => {
        button.classList.toggle('active');
        // Font Awesome 아이콘 클래스 변경
        const icon = button.querySelector('i');
        if (button.classList.contains('active')) {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
        } else {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
        }
    });
});