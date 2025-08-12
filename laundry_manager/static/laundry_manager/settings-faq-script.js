// static/laundry_manager/faq-script.js

import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// --- 페이지 로드 애니메이션 ---
animate(".page-container", { opacity: [0, 1] }, { duration: 0.5 });

// --- 아코디언 기능 및 애니메이션 ---
const accordions = document.querySelectorAll('.accordion-item');

accordions.forEach(accordion => {
    const summary = accordion.querySelector('summary');
    const content = accordion.querySelector('.accordion-content');

    summary.addEventListener('click', (e) => {
        // 기본 <details> 토글 동작을 막음 (JS로 제어하기 위해)
        e.preventDefault();

        // 현재 클릭한 것 외에 다른 아코디언들을 닫음
        accordions.forEach(otherAccordion => {
            if (otherAccordion !== accordion && otherAccordion.open) {
                otherAccordion.removeAttribute('open');
            }
        });

        // 현재 클릭한 아코디언의 열림/닫힘 상태를 토글
        if (accordion.open) {
            accordion.removeAttribute('open');
        } else {
            accordion.setAttribute('open', true);
        }
    });

    // 열리고 닫힐 때 애니메이션 적용
    accordion.addEventListener('toggle', () => {
        if (accordion.open) {
            // 열릴 때
            animate(content, { height: [0, content.scrollHeight + 'px'] }, { duration: 0.3, easing: "ease-out" });
        } else {
            // 닫힐 때
            animate(content, { height: [content.scrollHeight + 'px', 0] }, { duration: 0.3, easing: "ease-in" });
        }
    });
});