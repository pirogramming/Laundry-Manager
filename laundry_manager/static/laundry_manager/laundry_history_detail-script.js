// static/laundry_manager/laundry_history_detail-script.js

import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// DOM이 완전히 로드된 후 스크립트를 실행합니다.
document.addEventListener('DOMContentLoaded', () => {

    // --- 1. 페이지 로드 시 부드럽게 나타나는 애니메이션 ---
    // CSS에 설정된 opacity: 0 상태에서 1로 0.5초 동안 변경합니다.
    animate(
        ".page-container",
        { opacity: [0, 1] },
        { duration: 0.5, easing: "ease-out" }
    );

    // --- 2. 버튼 클릭 시 시각적 피드백 효과 ---
    // 페이지 내의 모든 버튼 요소를 선택합니다.
    const interactiveButtons = document.querySelectorAll('.icon-btn, .delete-button');

    interactiveButtons.forEach(button => {
        // 마우스를 누르거나 터치를 시작했을 때
        button.addEventListener('pointerdown', () => {
            animate(button, { scale: 0.97 }, { duration: 0.1 });
        });

        // 마우스를 떼거나 터치가 끝났을 때
        button.addEventListener('pointerup', () => {
            animate(button, { scale: 1 }, { duration: 0.1 });
        });

        // 버튼 밖으로 포인터가 나갔을 때도 원래 크기로 복귀
        button.addEventListener('pointerleave', () => {
            animate(button, { scale: 1 }, { duration: 0.1 });
        });
    });

});