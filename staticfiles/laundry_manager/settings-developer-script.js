// static/laundry_manager/developer-info-script.js

import { animate,stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// --- 페이지 로드 애니메이션 ---
animate(
    ".page-container",
    { opacity: [0, 1] },
    { duration: 0.5, easing: "ease-out" }
);

// --- 개발자 카드 순차 등장 애니메이션 ---
animate(
    ".member-card",
    {
        opacity: [0, 1],
        y: [20, 0] // 아래에서 위로
    },
    {
        delay: stagger(0.1, { start: 0.3 }) // 0.3초 후부터 0.1초 간격으로
    }
);