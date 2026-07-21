<script setup>
import Footer from '@/components/Footer.vue';

import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const steps = [
  {
    n: '1',
    title: 'ЗАГРУЗКА ФАЙЛА',
    text: 'Выберите файл договора и укажите, кем вы являетесь в сделке по ФИО.',
  },
  {
    n: '2',
    title: 'ЛОКАЛЬНАЯ ОЧИСТКА',
    text: 'Наш скрипт находит ИИН, ФИО, номера телефонов и заменяет их на безопасные маркеры. Сырые данные не уходят в интернет.',
  },
  {
    n: '3',
    title: 'ИИ-АУДИТ РИСКОВ',
    text: 'Очищенный текст анализируется на соответствие Гражданскому кодексу РК, и вы получаете детальный разбор аспектов, обязанностей и скрытых рисков.',
  },
]

const redirect = (pageName) => {
  router.push({ name: pageName }) 
}
</script>

<template>
  <div class="page">
    <!-- Background -->
    <div class="backdrop" aria-hidden="true">
      <img src="../assets/bg.jpeg" alt="" class="backdrop-img" />
      <div class="backdrop-overlay"></div>
    </div>

    <header class="topbar">
      <!-- Logo -->
      <a href="#" class="logo" aria-label="Yurta.safe">
        <img src="../assets/logo.png" alt="YURTA.safe" class="logo-img" />
      </a>
    </header>

    <main>
      <!-- HEADER -->
      <section class="hero-header">
        <h1>Проверь договор аренды за 10 секунд без юристов и слива данных</h1>
        <hr class="accent-line" />
      </section>

      <!-- HERO BLOCK -->
      <section class="hero-content">
        <!-- Left: Note -->
        <div class="hero-card">
          <div class="card-binders">
            <span class="ring"></span><span class="ring"></span><span class="ring"></span>
          </div>
          <p class="card-text">
            Умный разбор договоров аренды и сопутствующих документов по законам РК. Быстро, безопасно и без утечки личных данных.
          </p>
        </div>

        <!-- Right: Description -->
        <div class="hero-description">
          <h2 class="brand-title">Yurta.safe —</h2>
          <p class="lead">
            это интеллектуальная юридическая платформа, созданная для автоматизированного анализа юридических документов и договоров.
          </p>
          <p class="lead">
            Сервис принимает текст или документы и с помощью технологии нейросетей автоматически выявляет правовые риски, критические условия и «подводные камни».
          </p>
        </div>
      </section>

      <!-- HOW IT WORKS -->
      <section class="how">
        <h2 class="section-title">КАК ЭТО РАБОТАЕТ?</h2>
        
        <div class="how-layout">
          <div class="steps-vertical">
            <div v-for="step in steps" :key="step.n" class="step-row">
              <div class="step-number">{{ step.n }}</div>
              <div class="step-content">
                <span class="step-label">{{ step.title }}:</span>
                {{ step.text }}
              </div>
            </div>
          </div>

          <!-- START Button -->
          <div class="action-panel">
            <button class="btn-start" type="button" @click="redirect('workspace')">
              <span class="arrow">→</span> START
            </button>
          </div>
        </div>
      </section>
    </main>

    <!-- FOOTER -->
    <Footer />
  </div>
</template>

<style scoped>
/* BG with gradient*/
.backdrop {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.backdrop-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.7;
}
.backdrop-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(18,14,30,0.6) 0%, rgba(18,14,30,0.95) 100%);
}

.topbar, main, .site-footer {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.topbar {
  padding: 16px clamp(20px, 6vw, 72px) 0;
  text-align: center;
}

.logo-img {
  height: 200px; 
  width: auto;
  display: block;
  margin: 0 auto -5% auto; 
}

/* Header */
.hero-header {
  padding: 50px 0;
  text-align: center;
}
.hero-header h1 {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: clamp(1.8rem, 3vw, 2.6rem);
  line-height: 1.2;
  color: var(--lime);
  margin: 0 auto 24px;
  max-width: 900px;
  text-transform: uppercase;
}
.accent-line {
  border: none;
  height: 2px;
  background: var(--lime);
  margin: 0;
  width: 100%;
  box-shadow: 0 0 10px rgba(155, 232, 108, 0.4);
}

/* Hero */
.hero-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(40px, 6vw, 80px);
  padding: clamp(40px, 6vw, 80px) clamp(20px, 6vw, 72px);
  align-items: center;
}

/* Card */
.hero-card {
  background: #f4f2f9;
  color: #120e1e;
  border-radius: 4px;
  padding: 40px 32px;
  position: relative;
  box-shadow: 0 20px 40px rgba(0,0,0,0.5);
  transform: rotate(-1deg);
}
.card-binders {
  position: absolute;
  top: 15px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 40px;
}
.ring {
  width: 12px;
  height: 24px;
  background: #d4d4d4;
  border-radius: 6px;
  border: 1px solid #999;
  box-shadow: none;
  transform: translateY(-20px);
}
.card-text {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: clamp(1.4rem, 2vw, 1.8rem);
  line-height: 1.4;
  margin: 0;
  color: #555;
}

/* Right text */
.brand-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2rem;
  color: var(--lime);
  margin: 0 0 16px;
}
.lead {
  font-size: 1.1rem;
  line-height: 1.6;
  color: var(--text-primary);
  margin: 0 0 20px;
  font-weight: 500;
}

/* How-it-works */
.how {
  padding: 40px clamp(20px, 6vw, 72px) 80px;
}
.section-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2rem;
  color: var(--text-primary);
  text-align: center;
  margin: 0 0 48px;
}

.how-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 40px;
  align-items: center;
}

/* Steps */
.steps-vertical {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.step-row {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  background: rgba(28, 22, 48, 0.6);
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--line);
}
.step-number {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 3.5rem;
  font-weight: 700;
  color: var(--lime);
  line-height: 0.8;
  text-shadow: 0 0 20px rgba(155, 232, 108, 0.2);
}
.step-content {
  font-size: 1.05rem;
  line-height: 1.5;
  color: var(--text-primary);
}
.step-label {
  color: var(--lime);
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 4px;
  margin-right: 6px;
}

/* Button */
.action-panel {
  display: flex;
  justify-content: center;
}
.btn-start {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 1.5rem;
  color: #120e1e;
  background: #f4f2f9;
  -border: 3px solid var(--lime);
  border-radius: 8px;
  padding: 20px 48px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s ease;
  box-shadow: 0 0 20px rgba(155, 232, 108, 0.15);
}
.btn-start:hover {
  background: var(--lime);
  box-shadow: 0 0 30px rgba(155, 232, 108, 0.4);
  transform: translateY(-2px);
}
.btn-start .arrow { transition: transform 0.2s ease; }
.btn-start:hover .arrow { transform: translateX(5px); }

/* Responsive */
@media (max-width: 992px) {
  .hero-content { grid-template-columns: 1fr; gap: 40px; }
  .how-layout { grid-template-columns: 1fr; gap: 40px; }
  .action-panel { justify-content: flex-start; }
}
@media (max-width: 600px) {
  .hero-header h1 { font-size: 1.5rem; }
  .step-row { flex-direction: column; gap: 12px; }
  .step-number { font-size: 2.5rem; }
}
</style>