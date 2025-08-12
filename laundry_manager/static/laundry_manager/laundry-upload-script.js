// static/laundry_manager/laundry-upload-script.js

// 1. import 문을 파일 최상단에 배치합니다.
import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm"

// 2. DOM이 완전히 로드된 후 모든 스크립트가 실행되도록 하나의 이벤트 리스너로 감쌉니다.
document.addEventListener('DOMContentLoaded', () => {

    // --- Motion.js 애니메이션 관련 코드 ---

    // 페이지 로드 애니메이션
    animate(
        ".mobile-container",
        { opacity: [0, 1] },
        { duration: 0.4, easing: "ease-out" }
    );

    // 버튼 인터랙션 피드백
    const buttons = document.querySelectorAll('button, a.tab-btn');
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

    // --- 폼(Form) 관련 기능 코드 ---

    // HTML 요소 선택
    const form = document.getElementById("uploadForm");
    const fileInput = document.getElementById("id_image");
    const fileNameEl = document.querySelector(".dz-filename");
    const dropzoneTextEl = document.querySelector(".dz-text"); // 👈 1. 기존 안내 문구 요소 선택
    const materialInput = document.getElementById("selected-material");
    const stainsInput = document.getElementById("selected-stains");

    // 소재 선택 아이템
    const materialItems = document.querySelectorAll('#material-selection .selectable-item');
    materialItems.forEach(item => {
        item.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            materialItems.forEach(el => el.classList.remove('active'));
            
            if (isActive) {
                materialInput.value = ""; 
            } else {
                item.classList.add('active');
                materialInput.value = item.dataset.value;
            }
        });
    });

    // 얼룩 유형 선택 아이템 (다중 선택)
    const stainItems = document.querySelectorAll('#stain-selection .selectable-item');
    stainItems.forEach(item => {
        item.addEventListener('click', () => {
            item.classList.toggle('active');
            const selectedStains = Array.from(document.querySelectorAll('#stain-selection .selectable-item.active'))
                                        .map(el => el.dataset.value);
            stainsInput.value = selectedStains.join(',');
        });
    });

    // 폼 제출 시 유효성 검사
    if (form) {
        form.addEventListener("submit", function (event) {
            const fileSelected = fileInput.files.length > 0;
            const manualSelectionDone = materialInput.value.trim() !== "" && stainsInput.value.trim() !== "";
    
            if (!fileSelected && !manualSelectionDone) {
                event.preventDefault();
                alert("세탁 태그 이미지를 업로드하거나, 의류 소재와 얼룩 유형을 모두 선택해주세요.");
            }
        });
    }

    // 파일 올리면 파일 이름 표시 및 안내 문구 숨기기 기능
    if (fileInput && fileNameEl && dropzoneTextEl) {
        fileInput.addEventListener("change", () => {
            const files = fileInput.files;
            if (!files || files.length === 0) {
                // 파일 선택이 취소된 경우
                fileNameEl.textContent = "";
                dropzoneTextEl.style.display = 'block'; // 👈 3. 안내 문구 다시 보이기
                return;
            }
            // 파일이 선택된 경우
            fileNameEl.textContent = files.length === 1
                ? `선택된 파일: ${files[0].name}`
                : `${files.length}개 파일 선택됨`;
            dropzoneTextEl.style.display = 'none'; // 👈 2. 기존 안내 문구 숨기기
        });
    }

}); // DOMContentLoaded 이벤트 리스너 종료