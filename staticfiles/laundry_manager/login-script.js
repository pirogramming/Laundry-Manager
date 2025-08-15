// static/laundry_manager/login-script.js

import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// --- 페이지 로드 시 화면 전환 애니메이션 ---
document.addEventListener('DOMContentLoaded', () => {
    animate(
        ".guest-section",
        { 
            
            opacity: [0, 1],
        },
        { 
            duration: 0.6,
            easing: "ease-out"
        }
    );
    animate(
        ".login-card",
        { 
            y: [40, 0],
            opacity: [0, 1],
        },
        { 
            duration: 1,
            easing: "ease-out"
        }
    );

});


// --- 모든 버튼에 대한 인터랙션 피드백 ---
const buttons = document.querySelectorAll('button, .guest-link, .signup-prompt a');

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