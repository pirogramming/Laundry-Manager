// static/laundry_manager/account-settings-script.js

import { animate } from "https://cdn.jsdelivr.net/npm/motion@10.18.0/dist/motion.es.js";

// --- 페이지 로드 시 화면 전환 애니메이션 ---
animate(
    ".page-container",
    { opacity: [0, 1] },
    { duration: 0.5, easing: "ease-out" }
);

// --- 비밀번호 보이기/숨기기 토글 ---
const togglePassword = document.querySelector('.toggle-password');
const passwordInput = document.getElementById('password');

if (togglePassword && passwordInput) {
    togglePassword.addEventListener('click', () => {
        // 아이콘 모양 변경
        const isPassword = passwordInput.type === 'password';
        togglePassword.classList.toggle('fa-eye-slash', !isPassword);
        togglePassword.classList.toggle('fa-eye', isPassword);

        // input 타입 변경
        passwordInput.type = isPassword ? 'text' : 'password';
    });
}