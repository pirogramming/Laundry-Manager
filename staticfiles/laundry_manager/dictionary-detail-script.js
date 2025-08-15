import { animate, stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// 1. 페이지 전체가 부드럽게 나타나는 효과
animate(
    ".mobile-container.detail-page",
    { opacity: [0, 1] },
    { duration: 0.5, easing: "ease-out" }
);

// 2. 관련 팁 목록이 순차적으로 나타나는 효과 (메인페이지와 동일)
animate(
    ".related-tips-section .history-item",
    { 
        opacity: [0, 1],
        y: [15, 0]
    },
    { 
        delay: stagger(0.1, { start: 0.3 }) 
    }
);

// 3. 버튼 클릭 시 피드백 애니메이션 (메인페이지와 동일)
const buttons = document.querySelectorAll('.icon-btn-nav, .history-item');

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

// 4. 즐겨찾기 버튼 토글 기능
const bookmarkBtn = document.getElementById('bookmarkBtn');
if (bookmarkBtn) {
    const heartIcon = bookmarkBtn.querySelector('i');
    bookmarkBtn.addEventListener('click', () => {
        const isActive = bookmarkBtn.classList.toggle('active');
        
        // 아이콘 모양도 함께 변경 (solid <-> regular)
        if (isActive) {
            heartIcon.classList.remove('fa-regular');
            heartIcon.classList.add('fa-solid');
        } else {
            heartIcon.classList.remove('fa-solid');
            heartIcon.classList.add('fa-regular');
        }

        // 버튼이 활성화될 때 애니메이션 효과
        animate(bookmarkBtn, { scale: [1, 1.2, 1] }, { duration: 0.3 });
    });
}