// static/laundry_manager/main-script.js


import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

animate(
    ".mobile-container",
    { opacity: [0, 1] },
    { duration: 0.5, easing: "ease-out" }
);

// --- Swiper.js 캐러셀 초기화 (새로 추가) ---


const swiper = new Swiper('.main-swiper', {
    slidesPerView: 1, // 한 번에 보이는 슬라이드 개수 (CSS 너비에 따라 자동)
    spaceBetween: 12,
  
// 활성 슬라이드를 가운데로
    loop: true,            // 무한 루프
    
    // 자동 재생
    autoplay: {
      delay: 3000, // 3초마다 자동 재생
      disableOnInteraction: false, // 사용자가 조작한 후에도 자동 재생 유지
    },

    // 페이지네이션 (하단 점)
    pagination: {
      el: '.swiper-pagination',
      clickable: true,
    },
    
});
function updateEdgePeek(sw) {
  const el = sw.el; // .main-swiper
  // 먼저 싹 지우고
  el.classList.remove('is-first', 'is-last');

  // 원본 슬라이드 개수 (클론 제외)
  const originalCount =3;

  if (sw.realIndex === 0) {
    el.classList.add('is-first');     // 맨 왼쪽: 오른쪽만 살짝 보이게
  } else if (sw.realIndex === originalCount - 1) {
    el.classList.add('is-last');      // 맨 오른쪽: 왼쪽만 살짝 보이게
  }
}

// --- 모든 버튼에 대한 인터랙션 피드백 ---
const buttons = document.querySelectorAll('button, a.cta-button, a.nav-item, a.nav-item-main');

buttons.forEach(button => {
    button.addEventListener('pointerdown', () => {
        animate(button, { scale: 0.97 }, { duration: 0.1 });
    });
    button.addEventListener('pointerup', () => {
        animate(button, { scale: 1 }, { duration: 0.1 });
    });
    button.addEventListener('pointerleave', () => {
        animate(button, { scale: 1 }, { duration: 0.1 });
    });
});

// --- '기록 보기' 목록이 순차적으로 나타나는 효과 ---
animate(
    ".history-item",
    { 
        opacity: [0, 1],
        y: [15, 0]
    },
    { 
        delay: stagger(0.1, { start: 0.5 }) 
    }
);