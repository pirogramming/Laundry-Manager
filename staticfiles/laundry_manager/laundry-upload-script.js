document.addEventListener('DOMContentLoaded', () => {
    // 소재 선택 영역
    const materialItems = document.querySelectorAll('#material-selection .selectable-item');
    materialItems.forEach(item => {
        item.addEventListener('click', () => {
            materialItems.forEach(el => el.classList.remove('active'));
            item.classList.add('active');
        });
    });

    // 얼룩 유형 선택 영역
    const stainItems = document.querySelectorAll('#stain-selection .selectable-item');
    stainItems.forEach(item => {
        item.addEventListener('click', () => {
            stainItems.forEach(el => el.classList.remove('active'));
            item.classList.add('active');
        });
    });
});

import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

document.addEventListener('DOMContentLoaded', () => {

    animate(
        ".page-container, .mobile-container",
        { 
            
            opacity: [0, 1]     // 투명도 0에서 1로
        },
        { 
            duration: 0.4,      // 0.5초 동안
            easing: "ease-out"  // 부드러운 감속 효과
        }

        
    );
});



const buttons = document.querySelectorAll('button, .cta-button, .submit-button, .nav-item, ');

buttons.forEach(button => {
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
