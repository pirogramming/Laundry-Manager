// static/laundry_manager/record-settings-script.js

import { animate,stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"
// --- 페이지 로드 애니메이션 ---
animate(".page-container", { opacity: [0, 1] }, { duration: 0.5 });

// --- 기록 목록 순차 등장 애니메이션 ---
animate(
    ".history-item",
    {
        opacity: [0, 1],
        y: [20, 0] // 아래에서 위로
    },
    {
        delay: stagger(0.1, { start: 0.2 }) // 0.2초 후부터 0.1초 간격으로
    }
);

// --- 모든 버튼/링크에 대한 인터랙션 피드백 ---
const interactiveElements = document.querySelectorAll('button, a.history-item');
interactiveElements.forEach(element => {
    element.addEventListener('pointerdown', () => {
        animate(element, { scale: 0.98 }, { duration: 0.1 });
    });
    element.addEventListener('pointerup', () => {
        animate(element, { scale: 1 }, { duration: 0.1 });
    });
    element.addEventListener('pointerleave', () => {
        animate(element, { scale: 1 }, { duration: 0.1 });
    });
});