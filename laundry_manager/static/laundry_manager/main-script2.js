// static/laundry_manager/main-script2.js
// 모듈로 로드하세요: <script type="module" src="{% static 'laundry_manager/main-script2.js' %}"></script>

import { animate, stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// -------- 유틸 --------
const qs  = (s, r=document) => r.querySelector(s);
const qsa = (s, r=document) => Array.from(r.querySelectorAll(s));

// -------- 페이지 로드 후 초기화 --------
document.addEventListener("DOMContentLoaded", () => {
  fadeInPage();
  initSwiperOnce();
  initButtonFeedback();
  animateHistoryItems();
  initDailyFortuneModal();
});

// -------- 1) 첫 화면 페이드인 --------
function fadeInPage() {
  animate(".mobile-container", { opacity: [0, 1] }, { duration: 0.5, easing: "ease-out" });
}

// -------- 2) Swiper 캐러셀 --------
function initSwiperOnce() {
  if (typeof window.Swiper === "undefined") {
    console.warn("Swiper not loaded.");
    return;
  }
  const el = qs(".main-swiper");
  if (!el) return;

  // 중복 초기화 방지
  if (el.__initialized) return;
  el.__initialized = true;

  /* eslint-disable no-new */
  new Swiper(".main-swiper", {
    slidesPerView: 1,
    spaceBetween: 12,
    loop: true,
    autoplay: { delay: 3000, disableOnInteraction: false },
    pagination: { el: ".swiper-pagination", clickable: true },
  });
}

// -------- 3) 버튼 인터랙션(하단 카메라 포함) --------
function initButtonFeedback() {
  const buttons = qsa("button, a.cta-button, a.nav-item, a.nav-item-main");
  buttons.forEach((btn) => {
    btn.addEventListener("pointerdown", () => animate(btn, { scale: 0.97 }, { duration: 0.1 }));
    const to1 = () => animate(btn, { scale: 1 }, { duration: 0.1 });
    btn.addEventListener("pointerup", to1);
    btn.addEventListener("pointerleave", to1);
  });
}

// -------- 4) 기록 리스트 순차 등장 --------
function animateHistoryItems() {
  animate(".history-item", { opacity: [0, 1], y: [15, 0] }, { delay: stagger(0.1, { start: 0.5 }) });
}

// -------- 5) 오늘의 운세 모달 --------
function initDailyFortuneModal() {
  const backdrop = qs("#fortune-modal");
  const closeBtn = qs("#fortune-close");
  const textBox  = qs("#fortune-text");
  if (!backdrop || !closeBtn || !textBox) return; // 마크업 없으면 종료

  const today = new Date().toISOString().slice(0, 10);
  const KEY = "fortune_shown_" + today;
  if (localStorage.getItem(KEY) === "1") return;

  // API 호출 (없거나 실패하면 모달을 띄우지 않음)
  fetch("/api/fortune/today/", { credentials: "same-origin" })
    .then((res) => (res.ok ? res.json() : Promise.reject()))
    .then((data) => {
      if (data && data.fortune) textBox.textContent = data.fortune;
      open();
    })
    .catch(() => {
      /* 조용히 실패 */
    });

  function open() {
    backdrop.hidden = false;
    backdrop.setAttribute("show", "");
    // 스크롤 잠금
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
  }

  function close() {
    localStorage.setItem(KEY, "1");
    backdrop.removeAttribute("show");
    backdrop.hidden = true;
    // 스크롤 복원
    document.documentElement.style.overflow = "";
    document.body.style.overflow = "";
  }

  // 닫기 바인딩
  closeBtn.addEventListener("click", close);
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !backdrop.hidden) close(); });
}
