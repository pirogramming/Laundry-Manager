// static/laundry_manager/result-script.js
import { animate, scroll } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

document.addEventListener('DOMContentLoaded', () => {
  // 페이드 인
  animate(".mobile-container", { opacity: [0, 1] }, { duration: 0.5, easing: "ease-out" });

  // 허용 리스트(템플릿 옵션과 동일하게 유지)
  const ALLOWED_MATERIALS = ['면','니트','실크','린넨','청'];
  const ALLOWED_STAINS = ['커피','김치','기름','과일','잉크'];

  // 엘리먼트
  const modal = document.getElementById('edit-modal');
  const openModalBtn = document.getElementById('open-modal-btn');
  const closeModalBtn = document.getElementById('close-modal-btn');
  const laundryItemNameElement = document.getElementById('laundry-item-name');

  const editForm = document.getElementById('edit-form');
  const fieldInput = document.getElementById('edit-field');   // 'materials' | 'stains'
  const valueInput = document.getElementById('edit-value');
  const selectMaterial = document.getElementById('edit-material');
  const selectStain = document.getElementById('edit-stain');
  const recommendation = document.getElementById('recommendation'); // 있을 수도/없을 수도 있음
  const currentMaterialEl = document.getElementById('current-material');
  const currentStainEl = document.getElementById('current-stain');

  // CSRF
  function getCookie(name) {
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
  const csrftoken = getCookie('csrftoken') ||
    (document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '');

  // 마지막으로 사용자가 조작한 필드 추적
  let lastChanged = null;

  // 모달 열기/닫기
  const openModal = () => { modal?.classList.add('visible'); lastChanged = null; };
  const closeModal = () => { modal?.classList.remove('visible'); };

  // 셀렉트 박스 초기 선택값 보정
  function selectOptionIfExists(selectEl, text, allowedList) {
    if (!selectEl) return;
    let matched = false;
    [...selectEl.options].forEach(opt => {
      if (opt.text.trim() === text || opt.value.trim() === text) {
        matched = true;
        selectEl.value = opt.value;
      }
    });
    if (!matched) {
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

  // 현재 선택값으로 hidden value/field 채우기 (서버가 비어있으면 400 반환 방지)
  function primeHiddenWithCurrent(defaultField = 'materials') {
    const field = (lastChanged || fieldInput?.value || defaultField);
    if (fieldInput) fieldInput.value = field;

    if (field === 'stains') {
      valueInput.value = selectStain?.value || '';
    } else {
      valueInput.value = selectMaterial?.value || '';
    }
  }

  // “수정하기” 버튼으로 열기
  if (openModalBtn) {
    openModalBtn.addEventListener('click', (e) => {
      e.preventDefault();

      // 현재 화면 값 기준으로 셀렉트 맞추기
      const curMatText = currentMaterialEl?.textContent?.trim() || '';
      const curStainText = currentStainEl?.textContent?.trim() || '';
      selectOptionIfExists(selectMaterial, curMatText, ALLOWED_MATERIALS);
      selectOptionIfExists(selectStain, curStainText, ALLOWED_STAINS);

      // 기본은 materials로, hidden 미리 채워두기
      if (fieldInput) fieldInput.value = 'materials';
      primeHiddenWithCurrent('materials');

      openModal();
    });
  }

  if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
  modal?.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

  // data-open-edit 버튼으로 개별 열기 (선택사항)
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-open-edit]');
    if (!btn) return;
    const field = btn.getAttribute('data-field'); // 'materials' | 'stains'
    if (fieldInput) fieldInput.value = field || 'materials';

    if (field === 'stains') {
      const t = currentStainEl?.textContent?.trim() || '';
      selectOptionIfExists(selectStain, t, ALLOWED_STAINS);
    } else {
      const t = currentMaterialEl?.textContent?.trim() || '';
      selectOptionIfExists(selectMaterial, t, ALLOWED_MATERIALS);
    }
    primeHiddenWithCurrent(field || 'materials');
    openModal();
  });

  // 셀렉트 조작 시 field/value 동기화
  selectMaterial?.addEventListener('change', () => {
    lastChanged = 'materials';
    if (fieldInput) fieldInput.value = 'materials';
    valueInput.value = selectMaterial.value || '';
  });
  selectMaterial?.addEventListener('focus', () => {
    lastChanged = 'materials';
    if (fieldInput) fieldInput.value = 'materials';
    valueInput.value = selectMaterial.value || '';
  });
  selectStain?.addEventListener('change', () => {
    lastChanged = 'stains';
    if (fieldInput) fieldInput.value = 'stains';
    valueInput.value = selectStain.value || '';
  });
  selectStain?.addEventListener('focus', () => {
    lastChanged = 'stains';
    if (fieldInput) fieldInput.value = 'stains';
    valueInput.value = selectStain.value || '';
  });

  // 허용 옵션 검증
  function validateAllowed(field, value) {
    if (field === 'materials') return ALLOWED_MATERIALS.includes(value);
    return ALLOWED_STAINS.includes(value);
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


if (editForm) {
  editForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  // 현재 화면 값 vs 선택 값 비교
  const currentMat = (currentMaterialEl?.textContent || '').trim();
  const currentStn = (currentStainEl?.textContent || '').trim();
  const selectedMat = (selectMaterial?.value || '').trim();
  const selectedStn = (selectStain?.value || '').trim();

  const matChanged = selectedMat && selectedMat !== currentMat;
  const stnChanged = selectedStn && selectedStn !== currentStn;

  // 허용값 검증 함수 재사용
  const isMatAllowed = ALLOWED_MATERIALS.includes(selectedMat);
  const isStnAllowed = ALLOWED_STAINS.includes(selectedStn);

  // 작은 유틸: 실제 전송
  async function postUpdate(field, value) {
    // hidden 채우기
    fieldInput.value = field;
    valueInput.value = value;

    const formData = new FormData(editForm);
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
    if (!data.ok) throw new Error('update failed');
    // UI 반영
    if ('materials_text' in data && currentMaterialEl) currentMaterialEl.textContent = data.materials_text || '-';
    if ('stains_text' in data && currentStainEl) currentStainEl.textContent = data.stains_text || '-';
    if (laundryItemNameElement) {
      const iconHtml = '<i class="fa-solid fa-pen-to-square"></i>';
      const matTxt = (data.materials_text ?? currentMat) || '(소재 미선택)';
      const stnTxt = (data.stains_text ?? currentStn) || '(얼룩 미선택)';
      laundryItemNameElement.innerHTML = `${matTxt} / ${stnTxt} ${iconHtml}`;
    }
    // 히든 리스트도 갱신
    replaceHiddenList(editForm, 'materials[]', data.materials_text || selectedMat || '');
    replaceHiddenList(editForm, 'stains[]', data.stains_text || selectedStn || '');
    // 추천 카드 섹션 갱신
    if (recommendation && typeof data.html === 'string') {
      recommendation.innerHTML = data.html;
    }
  }

  try {
    if (matChanged && !isMatAllowed) return alert('허용되지 않은 소재입니다.');
    if (stnChanged && !isStnAllowed) return alert('허용되지 않은 얼룩 유형입니다.');

    if (matChanged && stnChanged) {
      // ① 소재 → ② 얼룩 순차 호출
      await postUpdate('materials', selectedMat);
      await postUpdate('stains', selectedStn);
    } else if (matChanged) {
      await postUpdate('materials', selectedMat);
    } else if (stnChanged) {
      await postUpdate('stains', selectedStn);
    } else {
      // 변화 없음
      closeModal();
      return;
    }

    closeModal();
  } catch (err) {
    console.error(err);
    alert('저장 중 오류가 발생했습니다.');
  }
});

}



  // 태그 선택 UX
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
});
