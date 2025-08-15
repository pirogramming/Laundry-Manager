// result-script.js
import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

document.addEventListener('DOMContentLoaded', () => {
  animate(".mobile-container", { opacity: [0, 1] }, { duration: 0.5, easing: "ease-out" });

  // 허용 리스트(고정)
  const ALLOWED_MATERIALS = ['면','니트','실크','린넨','청'];
  const ALLOWED_STAINS = ['커피','김치','기름','과일','잉크'];

  const modal = document.getElementById('edit-modal');
  const openModalBtn = document.getElementById('open-modal-btn');   // "추가 정보 입력하기"
  const closeModalBtn = document.getElementById('close-modal-btn');
  const laundryItemNameElement = document.getElementById('laundry-item-name');
  const editNameInput = document.getElementById('edit-name');

  const editForm = document.getElementById('edit-form');
  const fieldInput = document.getElementById('edit-field');   // 'materials' | 'stains'
  const valueInput = document.getElementById('edit-value');
  const selectMaterial = document.getElementById('edit-material');
  const selectStain = document.getElementById('edit-stain');
  const recommendation = document.getElementById('recommendation');
  const currentMaterialEl = document.getElementById('current-material');
  const currentStainEl = document.getElementById('current-stain');

  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
  const csrftoken = getCookie('csrftoken') ||
    (document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '');

  let lastChanged = null; // ✅ 마지막에 사용자가 건드린 필드 추적

  const openModal = () => { modal.classList.add('visible'); lastChanged = null; };
  const closeModal = () => modal.classList.remove('visible');

  // 현재 텍스트가 목록에 없으면 첫 옵션으로 보정하는 유틸
  function selectOptionIfExists(selectEl, text, allowedList) {
    let matched = false;
    [...selectEl.options].forEach(opt => {
      if (opt.text.trim() === text || opt.value.trim() === text) {
        matched = true;
        selectEl.value = opt.value;
      }
    });
    if (!matched) {
      // 허용 리스트의 첫 값으로 강제 세팅
      const fallback = allowedList?.[0];
      if (fallback) {
        const found = [...selectEl.options].find(o => o.value === fallback || o.text.trim() === fallback);
        if (found) selectEl.value = found.value;
        else selectEl.selectedIndex = 0;
      } else {
        selectEl.selectedIndex = 0;
      }
    }
  }

  // "추가 정보 입력하기"로 열 때: 기본 필드를 materials로 지정 + 둘 다 현재값으로 맞춤
  if (openModalBtn) {
    openModalBtn.addEventListener('click', (e) => {
      e.preventDefault();

      const currentName = laundryItemNameElement?.childNodes?.[0]?.nodeValue?.trim() || '';
      if (editNameInput) editNameInput.value = currentName;

      if (fieldInput) fieldInput.value = 'materials'; // 기본값

      const curMatText = currentMaterialEl?.textContent?.trim() || '';
      const curStainText = currentStainEl?.textContent?.trim() || '';
      if (selectMaterial) selectOptionIfExists(selectMaterial, curMatText, ALLOWED_MATERIALS);
      if (selectStain) selectOptionIfExists(selectStain, curStainText, ALLOWED_STAINS);

      openModal();
    });
  }

  if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
  }

  // (선택사항) data-open-edit 버튼으로도 열 수 있을 때 대비
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-open-edit]');
    if (!btn) return;
    const field = btn.getAttribute('data-field'); // 'materials' | 'stains'
    if (fieldInput) fieldInput.value = field;

    if (field === 'materials') {
      const t = currentMaterialEl?.textContent?.trim() || '';
      if (selectMaterial) selectOptionIfExists(selectMaterial, t, ALLOWED_MATERIALS);
    } else {
      const t = currentStainEl?.textContent?.trim() || '';
      if (selectStain) selectOptionIfExists(selectStain, t, ALLOWED_STAINS);
    }
    openModal();
  });

  // ✅ 사용자가 어떤 셀렉트를 만졌는지에 따라 field 자동 전환
  selectMaterial?.addEventListener('change', () => { lastChanged = 'materials'; if (fieldInput) fieldInput.value = 'materials'; });
  selectMaterial?.addEventListener('focus',  () => { lastChanged = 'materials'; if (fieldInput) fieldInput.value = 'materials'; });
  selectStain?.addEventListener('change', () => { lastChanged = 'stains'; if (fieldInput) fieldInput.value = 'stains'; });
  selectStain?.addEventListener('focus',  () => { lastChanged = 'stains'; if (fieldInput) fieldInput.value = 'stains'; });

  // 전송 전 허용 목록 검증
  function validateAllowed(field, value) {
    if (field === 'materials') return ALLOWED_MATERIALS.includes(value);
    return ALLOWED_STAINS.includes(value);
  }

  if (editForm) {
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // ✅ 마지막으로 조작한 셀렉트가 있으면 그것을 우선
      let field = lastChanged || fieldInput?.value;
      if (!field) {
        if (selectMaterial && selectMaterial.value) field = 'materials';
        else if (selectStain && selectStain.value) field = 'stains';
      }
      if (fieldInput) fieldInput.value = field || 'materials';

      // 실제 전송값 구성
      if (field === 'materials') {
        valueInput.value = selectMaterial ? (selectMaterial.value || '') : '';
      } else {
        valueInput.value = selectStain ? (selectStain.value || '') : '';
      }

      // ✅ 허용 옵션 검증
      if (!valueInput.value || !validateAllowed(field, valueInput.value)) {
        alert(field === 'materials' ? '허용되지 않은 소재입니다.' : '허용되지 않은 얼룩 유형입니다.');
        return;
      }

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
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        if (!data.ok) throw new Error('update failed');

        // 추천 카드 갱신
        if (recommendation && typeof data.html === 'string') {
          recommendation.innerHTML = data.html;
        }
        // 상단 표시 갱신
        if (currentMaterialEl && data.materials_text) currentMaterialEl.textContent = data.materials_text;
        if (currentStainEl && data.stains_text) currentStainEl.textContent = data.stains_text;

        // 히든 리스트 최신화(연속 수정 대비)
        replaceHiddenList(editForm, 'materials[]', data.materials_text || '');
        replaceHiddenList(editForm, 'stains[]', data.stains_text || '');

        closeModal();
      } catch (err) {
        console.error(err);
        alert('저장 중 오류가 발생했습니다.');
      }
    });
  }

  function replaceHiddenList(formEl, name, csvText) {
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

  // 태그 선택 UX 유지
  const tagItems = document.querySelectorAll('.tag-item');
  tagItems.forEach(item => {
    item.addEventListener('click', () => {
      tagItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
    });
  });

  // 버튼 프레스 애니메이션
  const buttons = document.querySelectorAll('button, .cta-button, .submit-button, .nav-item');
  buttons.forEach(button => {
    button.addEventListener('pointerdown', () => animate(button, { scale: 0.97 }, { duration: 0.1 }));
    button.addEventListener('pointerup', () => animate(button, { scale: 1 }, { duration: 0.1 }));
    button.addEventListener('pointerleave', () => animate(button, { scale: 1 }, { duration: 0.1 }));
  });
});
