// static/laundry_manager/main-script.js

import { animate, scroll, stagger } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

// --- 페이지 로드 애니메이션 ---
animate(
    ".mobile-container",
    { opacity: [0, 1] },
    { duration: 0.5, easing: "ease-out" }
);

// --- Swiper.js 캐러셀 초기화 ---
const swiper = new Swiper('.main-swiper', {
    slidesPerView: 1,
    spaceBetween: 12,
    loop: true,
    autoplay: {
        delay: 3000,
        disableOnInteraction: false,
    },
    pagination: {
        el: '.swiper-pagination',
        clickable: true,
    },
});

// (updateEdgePeek 함수 등 다른 부분은 그대로 둡니다)

// --- 모든 버튼에 대한 인터랙션 피드백 ---
const buttons = document.querySelectorAll('button, a.cta-button, a.nav-item ');
buttons.forEach(button => {
    button.addEventListener('pointerdown', () => {
        animate(button, { scale: 0.97 }, { duration: 0.1 });
    });
    ['pointerup', 'pointerleave'].forEach(eventName => {
        button.addEventListener(eventName, () => {
            animate(button, { scale: 1 }, { duration: 0.1 });
        });
    });
});

// --- '기록 보기' 목록이 순차적으로 나타나는 효과 ---
animate(
    ".history-item",
    { 
        opacity: [0, 1],
        y: [15, 0]
    },
    { 
        delay: stagger(0.1, { start: 0.5 }) 
    }
);



// --- 오늘의 운세 팝업 기능 ---
const fortuneModal = document.getElementById('fortune-modal');
const closeModalBtn = document.getElementById('close-modal-btn');
const dontShowAgainBtn = document.getElementById('dont-show-again-btn');

const fortunes = [
    "마음속 깊이 간직해 온 창조적인 불꽃이 드디어 웅장한 날갯짓을 시작할 것입니다. 예상치 못한 곳에서 영감이 샘솟고, 묵혀두었던 계획들이 놀라운 속도로 현실화될 하루입니다.",
    "오늘은 평범한 일상 속에서 비범한 기쁨을 발견하는 날입니다. 스쳐 지나가는 바람, 따뜻한 커피 한 잔에서도 삶의 소중한 의미를 깨닫게 될 것입니다. 감성을 열어두세요.",
    "강력한 리더십이 발휘되는 날입니다. 망설이지 말고 당신의 비전을 명확하게 제시하세요. 당신의 확신에 찬 언어는 주변 사람들에게 깊은 신뢰를 주어 하나의 목표로 이끌 것입니다.",
    "오랫동안 연락이 끊겼던 소중한 인연으로부터 반가운 소식이 찾아올 수 있습니다. 마음을 열고 먼저 다가가 보세요. 따뜻한 대화가 새로운 기회의 문을 열어줄 것입니다.",
    "논리적인 분석을 넘어선 예리한 직관이 당신을 성공의 지름길로 안내할 것입니다. 중요한 결정을 앞두고 있다면, 오늘은 당신의 첫 느낌을 믿어보세요.",
    "작은 친절이 예상치 못한 큰 행운으로 돌아오는 하루입니다. 도움이 필요한 사람에게 따뜻한 손길을 내미는 것을 망설이지 마세요. 그 선행이 당신의 길을 밝혀줄 것입니다.",
    "오늘은 새로운 지식과 기술을 스펀지처럼 흡수하는 날입니다. 평소 관심 있던 분야의 책을 읽거나 짧은 강의를 들어보세요. 오늘의 배움이 미래의 당신에게 큰 자산이 될 것입니다.",
    "당신의 섬세한 감각과 꾸준한 노력이 마침내 빛을 발하는 날입니다. 오랫동안 공들여온 프로젝트나 작품이 있다면, 오늘 주변에 공개해보세요. 기대 이상의 찬사를 받게 될 것입니다.",
    "오늘은 사소한 우연이 당신을 특별한 길로 인도할 것입니다. 무심코 건넨 미소, 우연히 건넌 발걸음이 예상치 못한 행운의 시작점이 됩니다.",
    "어제의 불안은 사라지고, 오늘은 희망이 가득 차오르는 날입니다. 자신을 믿고 한 걸음 더 내딛는 순간, 닫혀 있던 문이 열릴 것입니다.",
    "오늘은 당신의 말 한마디가 누군가의 하루를 밝히는 등불이 됩니다. 긍정적인 언어를 선택하세요. 그것이 곧 당신에게도 돌아옵니다.",
    "작은 도전이 큰 성취로 이어지는 하루입니다. 망설이지 말고 새로운 시도를 해보세요. 생각보다 훨씬 쉽게 길이 열릴 수 있습니다.",
    "당신의 진심 어린 배려가 주변 사람들의 마음을 깊이 울릴 것입니다. 그 따뜻함이 돌고 돌아 오늘을 특별하게 만들어줍니다.",
    "오늘은 과거의 상처가 치유되는 날입니다. 오래 묵혀둔 감정을 정리하고 나면, 훨씬 가벼운 마음으로 새로운 길을 걸을 수 있습니다.",
    "예상치 못한 기회가 손을 내밀어 옵니다. 그것이 작아 보일지라도 잡아보세요. 그 작은 시작이 큰 미래로 확장됩니다.",
    "자연의 리듬과 함께 조화를 이루는 날입니다. 바람, 햇살, 작은 새소리에 귀 기울여 보세요. 당신의 마음도 고요하게 정돈될 것입니다.",
    "오늘은 평소 간과했던 능력이 스스로 드러나는 순간을 경험합니다. 자신이 몰랐던 가능성을 믿고 새로운 자부심을 느껴보세요.",
    "당신의 웃음소리가 행운을 불러오는 자석이 되는 날입니다. 즐거운 마음으로 하루를 맞이하면, 좋은 소식이 줄줄이 따라올 것입니다."
];


// fortuneModal이 HTML에 실제로 존재할 경우에만 아래 로직을 실행합니다. (오류 방지)
if (fortuneModal) {
      const closeModalBtn = document.getElementById('close-modal-btn');
      const dontShowAgainBtn = document.getElementById('dont-show-again-btn');
      const fortuneTextElement = fortuneModal.querySelector('.fortune-text');

      // 2. '오늘 하루 보지 않기'를 선택하지 않았을 경우에만 팝업을 보여줍니다.
      if (!localStorage.getItem('hideFortuneForToday')) {
          
          // 3. 운세 목록에서 랜덤으로 하나를 선택합니다.
          const randomIndex = Math.floor(Math.random() * fortunes.length);
          const randomFortune = fortunes[randomIndex];

          // 4. 선택된 운세를 팝업의 p 태그 안에 채워 넣습니다.
          if (fortuneTextElement) {
              fortuneTextElement.textContent = randomFortune;
          }
          
          // 5. 팝업을 화면에 표시합니다.
          fortuneModal.classList.add('visible');
      }

      // '닫기' 버튼 이벤트
      closeModalBtn.addEventListener('click', () => {
          fortuneModal.classList.remove('visible');
      });

      // '오늘 하루 보지 않기' 버튼 이벤트
      dontShowAgainBtn.addEventListener('click', () => {
          localStorage.setItem('hideFortuneForToday', 'true');
          fortuneModal.classList.remove('visible');
      });
};