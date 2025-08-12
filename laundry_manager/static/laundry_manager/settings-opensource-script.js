// static/laundry_manager/opensource-script.js

import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// --- 페이지 로드 시 화면 전환 애니메이션 ---
animate(
    ".page-container",
    { opacity: [0, 1] },
    { duration: 0.5, easing: "ease-out" }
);

// --- 헤더 버튼 인터랙션 피드백 ---
const interactiveElements = document.querySelectorAll('.icon-btn');
interactiveElements.forEach(element => {
    element.addEventListener('pointerdown', () => {
        animate(element, { scale: 0.95 }, { duration: 0.1 });
    });
    element.addEventListener('pointerup', () => {
        animate(element, { scale: 1 }, { duration: 0.1 });
    });
    element.addEventListener('pointerleave', () => {
        animate(element, { scale: 1 }, { duration: 0.1 });
    });
});