import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

document.addEventListener('DOMContentLoaded', () => {
    // --- 페이지 로드 애니메이션 ---
    animate(
        ".mobile-container",
        { opacity: [0, 1] },
        { duration: 0.5, easing: "ease-out" }
    );

    // --- 팝업(모달) 관련 요소 선택 ---
    const modal = document.getElementById('edit-modal');
    const openModalBtn = document.getElementById('open-modal-btn');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const laundryItemNameElement = document.getElementById('laundry-item-name');
    const editNameInput = document.getElementById('edit-name');

    const openTheModal = () => {
        const currentName = laundryItemNameElement.childNodes[0].nodeValue.trim();
        editNameInput.value = currentName;
        modal.classList.add('visible');
    };
    // --- 팝업 여는 기능 ---
    openModalBtn.addEventListener('click', (e) => {
        e.preventDefault();
        openTheModal();
    });
    laundryItemNameElement.addEventListener('click', openTheModal);
    // --- 팝업 닫는 기능 ---
    const closeModal = () => {
        modal.classList.remove('visible');
    }
    closeModalBtn.addEventListener('click', closeModal);
    // 반투명 배경 클릭 시 닫기
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // --- 팝업 내 태그 선택 기능 ---
    const tagItems = document.querySelectorAll('.tag-item');
    tagItems.forEach(item => {
        item.addEventListener('click', () => {
            // 다른 태그의 active 상태 해제
            tagItems.forEach(i => i.classList.remove('active'));
            // 클릭된 태그에 active 상태 추가
            item.classList.add('active');
        });
    });

    
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
