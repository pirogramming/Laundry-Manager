import { animate, stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// 1. 페이지 전체가 부드럽게 나타나는 효과
animate(
    ".mobile-container.detail-page",
    { opacity: [0, 1] },
    { duration: 0.5, easing: "ease-out" }
);

// 2. 관련 팁 목록이 순차적으로 나타나는 효과 (메인페이지와 동일)
animate(
    ".related-tips-section .history-item",
    { 
        opacity: [0, 1],
        y: [15, 0]
    },
    { 
        delay: stagger(0.1, { start: 0.3 }) 
    }
);

// 3. 버튼 클릭 시 피드백 애니메이션 (메인페이지와 동일)
const buttons = document.querySelectorAll('.icon-btn-nav, .history-item');

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

// 4. 즐겨찾기 버튼 토글 기능 (HTML 수정 없이 JS로만 해결)
const bookmarkBtn = document.getElementById('bookmarkBtn');

if (bookmarkBtn) {
    // --- JavaScript가 HTML에서 직접 정보 찾아오기 ---
    const titleElement = document.querySelector('.title-wrapper h1');
    const bgImageElement = document.querySelector('.detail-background-image');

    // 제목이나 배경 이미지 요소를 찾지 못하면 즐겨찾기 기능을 실행하지 않음
    if (!titleElement) {
        console.error("즐겨찾기 기능에 필요한 제목(h1) 요소를 찾을 수 없습니다.");
    } else {
        const currentTitle = titleElement.textContent.trim();
        let itemImageUrl = '';

        // 배경 이미지 요소에서 URL을 추출하는 로직
        if (bgImageElement) {
            const style = window.getComputedStyle(bgImageElement);
            const bgImage = style.backgroundImage;
            
            // bgImage 변수에는 'url("http://...")' 와 같은 문자열이 담깁니다.
            // 'none'이 아닐 경우에만 URL을 추출합니다.
            if (bgImage && bgImage !== 'none') {
                // 정규표현식을 사용해 url(...) 안의 주소만 정확히 꺼내옵니다.
                itemImageUrl = bgImage.replace(/url\(['"]?(.*?)['"]?\)/i, "$1");
            }
        }
        
        const heartIcon = bookmarkBtn.querySelector('i');

        // 로컬 스토리지 상태를 읽어와 버튼 UI(모양)를 설정하는 함수
        const setButtonState = () => {
            const favorites = JSON.parse(localStorage.getItem('favorites')) || [];
            const isFavorite = favorites.some(fav => fav.title === currentTitle);

            if (isFavorite) {
                bookmarkBtn.classList.add('active');
                heartIcon.classList.remove('fa-regular');
                heartIcon.classList.add('fa-solid');
            } else {
                bookmarkBtn.classList.remove('active');
                heartIcon.classList.remove('fa-solid');
                heartIcon.classList.add('fa-regular');
            }
        };

        // 버튼 클릭 이벤트 리스너
        bookmarkBtn.addEventListener('click', () => {
            let favorites = JSON.parse(localStorage.getItem('favorites')) || [];
            const existingIndex = favorites.findIndex(fav => fav.title === currentTitle);

            if (existingIndex > -1) {
                favorites.splice(existingIndex, 1); // 있으면 제거
            } else {
                // 없으면 추가
                favorites.push({
                    title: currentTitle,
                    image_url: itemImageUrl,
                    url: window.location.href
                });
            }

            localStorage.setItem('favorites', JSON.stringify(favorites));
            setButtonState();
            animate(bookmarkBtn, { scale: [1, 1.2, 1] }, { duration: 0.3 });
        });

        // 페이지가 처음 로드될 때, 로컬 스토리지 상태를 반영하여 버튼 초기 모양 설정
        setButtonState();
    }
}