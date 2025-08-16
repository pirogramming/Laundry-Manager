// static/laundry_manager/laundry-upload-script.js
// 모듈 스크립트로 로드됩니다. (template에서 type="module")

// 1) Motion One (애니메이션)
import { animate } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// 2) DOM 준비
document.addEventListener("DOMContentLoaded", () => {
  // ────────────────────────────────────────────────────────────
  // 공통 선택자
  // ────────────────────────────────────────────────────────────
  const container = document.querySelector(".mobile-container");
  const form = document.getElementById("uploadForm");

  // 파일 업로드 관련
  const fileInput = document.getElementById("id_image");
  const dropzone = document.querySelector(".drop-zone");
  const fileNameEl = document.querySelector(".dz-filename");
  const dropzoneTextEl = document.querySelector(".dz-text");

  // 숨겨진 필드(서버 전송용)
  const materialInput = document.getElementById("selected-material");
  const stainsInput = document.getElementById("selected-stains");

  // 선택 리스트
  const materialItems = document.querySelectorAll("#material-selection .selectable-item");
  const stainItems = document.querySelectorAll("#stain-selection .selectable-item");

  // ────────────────────────────────────────────────────────────
  // 페이지/버튼 애니메이션
  // ────────────────────────────────────────────────────────────
  if (container) {
    animate(container, { opacity: [0, 1] }, { duration: 0.4, easing: "ease-out" });
  }

  const buttons = document.querySelectorAll("button, a.tab-btn, .icon-btn, .submit-button");
  buttons.forEach((button) => {
    button.addEventListener("pointerdown", () => animate(button, { scale: 0.97 }, { duration: 0.1 }));
    button.addEventListener("pointerup", () => animate(button, { scale: 1 }, { duration: 0.1 }));
    button.addEventListener("pointerleave", () => animate(button, { scale: 1 }, { duration: 0.1 }));
  });

  // ────────────────────────────────────────────────────────────
  // 선택 로직: 소재 = 단일 선택, 얼룩 = 단일 선택
  // ────────────────────────────────────────────────────────────
  function bindSingleSelect(items, onChange) {
    items.forEach((item) => {
      item.addEventListener("click", () => {
        const wasActive = item.classList.contains("active");
        items.forEach((el) => el.classList.remove("active"));
        if (wasActive) {
          onChange(""); // 해제
        } else {
          item.classList.add("active");
          onChange(item.dataset.value || "");
        }
      });
      // 키보드 접근성(Enter/Space로 토글)
      item.setAttribute("tabindex", "0");
      item.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          item.click();
        }
      });
    });
  }

  // 소재(단일)
  bindSingleSelect(materialItems, (value) => {
    materialInput.value = value;
  });

  // 얼룩(단일)
  bindSingleSelect(stainItems, (value) => {
    stainsInput.value = value;
  });

  // ────────────────────────────────────────────────────────────
  // 파일 업로드: 파일명 표시 + 드롭존 안내 문구 토글
  // ────────────────────────────────────────────────────────────
  function updateDropzoneUI() {
    if (!fileInput || !fileNameEl || !dropzoneTextEl) return;
    const files = fileInput.files;
    if (!files || files.length === 0) {
      fileNameEl.textContent = "";
      dropzoneTextEl.style.display = "block";
    } else {
      fileNameEl.textContent =
        files.length === 1 ? `선택된 파일: ${files[0].name}` : `${files.length}개 파일 선택됨`;
      dropzoneTextEl.style.display = "none";
    }
  }

  if (fileInput) {
    fileInput.addEventListener("change", updateDropzoneUI);
  }

  // (선택) 드래그&드롭 지원
  if (dropzone && fileInput) {
    ["dragenter", "dragover"].forEach((type) =>
      dropzone.addEventListener(type, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("dragging");
      })
    );
    ["dragleave", "drop"].forEach((type) =>
      dropzone.addEventListener(type, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("dragging");
      })
    );
    dropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        fileInput.files = dt.files;
        updateDropzoneUI();
      }
    });
  }

  // ────────────────────────────────────────────────────────────
  // 제출 유효성 검사:
  //  - 이미지 업로드 또는 수동 선택(소재+얼룩) 중 하나는 필수
  // ────────────────────────────────────────────────────────────
  if (form) {
    form.addEventListener("submit", (event) => {
      const fileSelected = fileInput && fileInput.files && fileInput.files.length > 0;
      const manualSelectionDone =
        materialInput.value.trim() !== "" && stainsInput.value.trim() !== "";

      if (!fileSelected && !manualSelectionDone) {
        event.preventDefault();
        alert("세탁 태그 이미지를 업로드하거나, 의류 소재와 얼룩 유형을 모두 선택해주세요.");
        // 시각적 피드백
        animate(".submit-button", { x: [-4, 4, -3, 3, 0] }, { duration: 0.3 });
      }
    });
  }

  // 초기 상태 반영(새로고침/뒤로가기 시)
  updateDropzoneUI();
});
