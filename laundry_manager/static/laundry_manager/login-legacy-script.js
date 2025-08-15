// static/laundry_manager/login-script.js

import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. 상단 흰색 영역 애니메이션 (화면 밖에서 아래로)
    animate(
        ".welcome-section",
        // CSS에서 설정한 transform: translateY(-100%) 에서 시작
        { transform: "translateY(0)", opacity: 1 }, 
        { duration: 0.8, easing: [0.22, 1, 0.36, 1] } // 더 부드러운 Easing 효과
    );

    // 2. 하단 로그인 패널 애니메이션 (아래에서 위로)
    animate(
        ".login-panel",
        { transform: "translateY(0)", opacity: 1 },
        { duration: 0.9, delay: 0.1, easing: [0.22, 1, 0.36, 1] }
    );

});

// (버튼 인터랙션 스크립트는 이전과 동일)
const buttons = document.querySelectorAll('button, .guest-link, .signup-prompt a, .social-btn');
buttons.forEach(button => {
    button.addEventListener('pointerdown', (e) => {
        animate(e.currentTarget, { scale: 0.97 }, { duration: 0.1 });
    });
    ['pointerup', 'pointerleave'].forEach(eventName => {
        button.addEventListener(eventName, (e) => {
            animate(e.currentTarget, { scale: 1 }, { duration: 0.1 });
        });
    });
});