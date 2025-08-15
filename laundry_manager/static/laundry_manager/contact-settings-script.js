// static/laundry_manager/contact-script.js

import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

/**
 * ===================================================================
 * 문의하기 페이지 스크립트
 * -------------------------------------------------------------------
 * - 페이지 로드 애니메이션
 * - 버튼/링크 클릭 시 시각적 피드백
 * - 문의 폼 비동기 제출 및 결과 처리
 * ===================================================================
 */

// DOM이 모두 로드된 후에 스크립트를 실행합니다.
document.addEventListener('DOMContentLoaded', () => {

    // --------- 1. 페이지 로드 애니메이션 ----------
    animate(
        ".page-container",
        { opacity: [0, 1] },
        { duration: 0.5, easing: "ease-out" }
    );

    // --------- 2. 모든 버튼/링크에 대한 인터랙션 피드백 ----------
    const interactiveElements = document.querySelectorAll('button, a.contact-item, a.faq-link');
    interactiveElements.forEach(element => {
        element.addEventListener('pointerdown', () => {
            animate(element, { scale: 0.98 }, { duration: 0.1 });
        });
        ['pointerup', 'pointerleave'].forEach(eventName => {
            element.addEventListener(eventName, () => {
                animate(element, { scale: 1 }, { duration: 0.1 });
            });
        });
    });

    // --------- 3. 문의 폼 비동기 제출 처리 ----------
    const inquiryForm = document.getElementById('inquiry-form');
    const successMessage = document.getElementById('success-message');

    if (inquiryForm) {
        inquiryForm.addEventListener('submit', function(e) {
            e.preventDefault(); // 기본 폼 제출(새로고침) 방지

            // 1. 폼 데이터를 FormData 객체로 가져옵니다.
            const formData = new FormData(inquiryForm);

            // 💡 2. HTML의 data-url 속성에서 서버로 요청할 URL을 가져옵니다.
            const submitUrl = inquiryForm.dataset.url;

            // 3. Fetch API로 서버에 POST 요청을 보냅니다.
            fetch(submitUrl, {
                method: 'POST',
                body: formData,
                // FormData와 함께 보낼 때는 CSRF 토큰을 헤더에 명시해주는 것이 안전합니다.
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json()) // 서버의 응답을 JSON으로 파싱
            .then(data => {
                if (data.status === 'success') {
                    // 4-1. 성공 시: 폼을 숨기고 성공 메시지를 보여줍니다.
                    inquiryForm.style.display = 'none';
                    successMessage.style.display = 'block';
                    
                    // 성공 메시지 애니메이션
                    animate(successMessage, { opacity: [0, 1], y: [10, 0] });
                } else {
                    // 4-2. 실패 시: 에러 메시지를 표시합니다.
                    // (실제 서비스에서는 필드별 에러를 표시하는 것이 더 좋습니다.)
                    alert('오류가 발생했습니다. 입력 내용을 확인해주세요.');
                    console.error('Validation Errors:', data.errors);
                }
            })
            .catch(error => {
                // 5. 네트워크 오류 등 통신 자체에 문제가 발생했을 때
                console.error('Fetch Error:', error);
                alert('서버와 통신 중 문제가 발생했습니다.');
            });
        });
    }
});