// static/laundry_manager/login-script.js

// 💡 timeline 대신 animate 함수를 사용하도록 수정했습니다.
import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// --- 페이지 로드 시 순차 애니메이션 ---
document.addEventListener('DOMContentLoaded', () => {
    
    // 1. 상단 로고 영역 애니메이션
    animate(
        ".welcome-section",
        { transform: "translateY(0)", opacity: 1 }, 
        { duration: 0.7, easing: [0.33, 1, 0.68, 1] }
    );

    // 2. 하단 로그인 패널 애니메이션 (0.2초 지연 시작)
    animate(
        ".login-panel",
        { transform: "translateY(0)", opacity: 1 },
        { duration: 0.7, delay: 0.2, easing: [0.33, 1, 0.68, 1] }
    );

});


// --- 모든 버튼에 대한 인터랙션 피드백 (기존과 동일) ---
const buttons = document.querySelectorAll('button, .guest-link, .signup-prompt a, .social-btn');

buttons.forEach(button => {
    button.addEventListener('pointerdown', (e) => {
        // animate 함수를 직접 사용하여 클릭 효과를 줍니다.
        animate(e.currentTarget, { scale: 0.97 }, { duration: 0.1 });
    });

    ['pointerup', 'pointerleave'].forEach(eventName => {
        button.addEventListener(eventName, (e) => {
            animate(e.currentTarget, { scale: 1 }, { duration: 0.1 });
        });
    });
});