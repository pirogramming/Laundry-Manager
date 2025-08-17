// static/laundry_manager/result-script.js
import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

document.addEventListener('DOMContentLoaded', () => {
  // 페이드 인
  animate(".mobile-container", { opacity: [0, 1] }, { duration: 0.5, easing: "ease-out" });

  // (옵션) 폴백 허용 리스트 — 칩이 하나도 없을 때만 사용
  const ALLOWED_MATERIALS = ['면','니트','실크','린넨','청'];
  const ALLOWED_STAINS = ['커피','김치','기름','과일','잉크'];

  // 엘리먼트
  const modal = document.getElementById('edit-modal');
  const openModalBtn = document.getElementById('open-modal-btn');
  const closeModalBtn = document.getElementById('close-modal-btn');
  const laundryItemNameElement = document.getElementById('laundry-item-name');

  const editForm = document.getElementById('edit-form');
  const fieldInput = document.getElementById('edit-field');   // 기본 'both'
  const valueInput = document.getElementById('edit-value');

  const currentMaterialEl = document.getElementById('current-material');
  const currentStainEl = document.getElementById('current-stain');

  // 칩 컨테이너
  const matList = document.getElementById('edit-material-list'); // <div class="item-list"> ... .selectable-item ...
  const stnList = document.getElementById('edit-stain-list');

  // CSRF
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
  const csrftoken = getCookie('csrftoken') ||
    (document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '');

  // 마지막으로 사용자가 조작한 필드(키보드 포커스 등)
  let lastChanged = null;

  // ---- 모달 열기/닫기 ----
  const openModal = () => { modal?.classList.add('visible'); lastChanged = null; };
  const closeModal = () => { modal?.classList.remove('visible'); };

  if (openModalBtn) {
    openModalBtn.addEventListener('click', (e) => {
      e.preventDefault();
      // 현재 화면 값으로 칩 선택 동기화
      syncChipsWithCurrent();
      // 기본은 both
      if (fieldInput) fieldInput.value = 'both';
      openModal();
    });
  }
  if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
  modal?.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

  // ---- 칩 선택 초기화/키보드 접근성 ----
  initSingleSelect(matList);
  initSingleSelect(stnList);

  // ---- 제출 핸들러 (AJAX) ----
  if (editForm) {
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const selectedMat = getSelectedValue(matList); // "면(Cotton)" 같이 raw(material)
      const selectedStn = getSelectedValue(stnList); // "커피와 차 얼룩" 같이 title

      // 서버가 both를 처리하도록 고정
      fieldInput.value = 'both';
      valueInput.value = JSON.stringify({
        materials: selectedMat ? [selectedMat] : [],
        stains: selectedStn ? [selectedStn] : []
      });

      const formData = new FormData(editForm);
      try {
        const res = await fetch(editForm.action, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: formData,
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();

        // UI 동기화
        const matTxt = data.materials_text || selectedMat || '(소재 미선택)';
        const stnTxt = data.stains_text    || selectedStn || '(얼룩 미선택)';

        if (currentMaterialEl) currentMaterialEl.textContent = data.materials_text || selectedMat || '-';
        if (currentStainEl)    currentStainEl.textContent    = data.stains_text    || selectedStn || '-';

        if (laundryItemNameElement) {
          const iconHtml = '<i class="fa-solid fa-pen-to-square"></i>';
          laundryItemNameElement.innerHTML = `${escapeHtml(matTxt)} / ${escapeHtml(stnTxt)} ${iconHtml}`;
        }

        // hidden 리스트 갱신 (다음 전송 대비)
        replaceHiddenList(editForm, 'materials[]', data.materials_text || selectedMat || '');
        replaceHiddenList(editForm, 'stains[]',    data.stains_text    || selectedStn || '');

        closeModal();
      } catch (err) {
        console.error(err);
        alert('저장 중 오류가 발생했습니다.');
      }
    });
  }

  // ---- 세탁 태그 칩 UX (기존 유지) ----
  const tagItems = document.querySelectorAll('.tag-item');
  tagItems.forEach(item => {
    item.addEventListener('click', () => {
      tagItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
    });
  });

  // 버튼 프레스 애니메이션
  const buttons = document.querySelectorAll('button, .cta-button, .submit-button, .nav-item, a.tab-btn, .icon-btn-bordered, .text-btn-dark');
  buttons.forEach(button => {
    button.addEventListener('pointerdown', () => animate(button, { scale: 0.97 }, { duration: 0.1 }));
    button.addEventListener('pointerup', () => animate(button, { scale: 1 }, { duration: 0.1 }));
    button.addEventListener('pointerleave', () => animate(button, { scale: 1 }, { duration: 0.1 }));
  });

  // ===== 유틸리티 =====

  // 현재 화면 텍스트를 기준으로 칩 활성화
  function syncChipsWithCurrent() {
    const curMat = (currentMaterialEl?.textContent || '').trim();
    const curStn = (currentStainEl?.textContent || '').trim();

    // 소재: "면" vs 칩의 data-value "면(Cotton)" or data-kor "면" 모두 매칭
    if (!activateByText(matList, curMat, (chipVal, chip) => {
      const kor = (chip.dataset.kor || '').trim();
      return chipVal === curMat || kor === curMat || chipVal.startsWith(curMat + '(');
    })) {
      // 폴백: 첫 칩 or ALLOWED_MATERIALS[0]
      fallbackSelect(matList, ALLOWED_MATERIALS[0]);
    }

    // 얼룩: title 정확 매칭
    if (!activateByText(stnList, curStn)) {
      fallbackSelect(stnList, ALLOWED_STAINS[0]);
    }
  }

  function initSingleSelect(listEl) {
    if (!listEl) return;

    // 마우스/터치로 단일 선택
    listEl.addEventListener("click", (e) => {
      const item = e.target.closest(".selectable-item");
      if (!item || !listEl.contains(item)) return;
      listEl.querySelectorAll(".selectable-item.active").forEach((el) => el.classList.remove("active"));
      item.classList.add("active");
      lastChanged = listEl.id.includes('material') ? 'materials' : 'stains';
    });

    // 키보드 접근성 (방향키 이동 + 스페이스/엔터로 선택)
    listEl.addEventListener("keydown", (e) => {
      const items = Array.from(listEl.querySelectorAll(".selectable-item"));
      if (!items.length) return;
      const idx = items.findIndex((el) => el === document.activeElement);
      if (["ArrowRight","ArrowDown"].includes(e.key)) {
        e.preventDefault();
        const next = items[(idx + 1 + items.length) % items.length];
        next?.focus();
      } else if (["ArrowLeft","ArrowUp"].includes(e.key)) {
        e.preventDefault();
        const prev = items[(idx - 1 + items.length) % items.length];
        prev?.focus();
      } else if ([" ","Enter"].includes(e.key)) {
        e.preventDefault();
        const el = document.activeElement.closest(".selectable-item");
        if (!el) return;
        items.forEach((n) => n.classList.remove("active"));
        el.classList.add("active");
        lastChanged = listEl.id.includes('material') ? 'materials' : 'stains';
      }
    });

    // 포커스 가능하도록 tabindex 지정
    Array.from(listEl.querySelectorAll(".selectable-item")).forEach((el, i) => {
      if (!el.hasAttribute('tabindex')) el.setAttribute("tabindex", i === 0 ? "0" : "-1");
    });
  }

  function getSelectedValue(listEl) {
    const sel = listEl?.querySelector(".selectable-item.active");
    return (sel?.dataset.value || '').trim();
  }

  function activateByText(listEl, text, matcher) {
    if (!listEl) return false;
    const t = (text || '').trim();
    if (!t) return false;
    const chips = Array.from(listEl.querySelectorAll('.selectable-item'));
    const found = chips.find(chip => {
      const chipVal = (chip.dataset.value || '').trim();
      return typeof matcher === 'function' ? matcher(chipVal, chip) : (chipVal === t);
    });
    if (found) {
      chips.forEach(c => c.classList.remove('active'));
      found.classList.add('active');
      return true;
    }
    return false;
    }

  function fallbackSelect(listEl, fallbackText) {
    if (!listEl) return;
    const chips = Array.from(listEl.querySelectorAll('.selectable-item'));
    if (chips.length) {
      chips.forEach(c => c.classList.remove('active'));
      chips[0].classList.add('active');
      return;
    }
    // (거의 없지만) 칩이 아예 없을 때 폴백 생성은 생략 — 서버 템플릿에서 칩 렌더가 기본
  }

  // hidden 리스트(materials[]/stains[]) 교체 (연속 수정 대비)
  function replaceHiddenList(formEl, name, csvText) {
    if (!formEl) return;
    [...formEl.querySelectorAll(`input[name="${name}"]`)].forEach(n => n.remove());
    const values = (csvText || '').split(',').map(s => s.trim()).filter(Boolean);
    if (values.length === 0) {
      const i = document.createElement('input');
      i.type = 'hidden';
      i.name = name;
      i.value = '';
      formEl.appendChild(i);
      return;
    }
    values.forEach(v => {
      const i = document.createElement('input');
      i.type = 'hidden';
      i.name = name;
      i.value = v;
      formEl.appendChild(i);
    });
  }

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
