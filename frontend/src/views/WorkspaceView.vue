<script setup>
import { ref, computed } from 'vue'
import Footer from '../components/Footer.vue'
import { ExtractorService, Anonymizer } from '../assets/censorer.js'

const pastAnalyses = ref([])

const selectedFile = ref(null)
const isDragging = ref(false)
const fileInput = ref(null)

const acceptedTypes = ['.pdf', '.png', '.jpg', '.jpeg']

function openFilePicker() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  const file = event.target.files?.[0]
  if (file) selectedFile.value = file
}

function handleDrop(event) {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  if (file) selectedFile.value = file
}

const fileLabel = computed(() => selectedFile.value?.name || null)

const isLoading = ref(false)
const isModalOpen = ref(false)
const result = ref(null)

function closeModal() {
  isModalOpen.value = false
}

async function submitAnalysis() {
  const file = selectedFile.value
  if (!file) return

  console.log(`[Censorer] File selected: ${file.name}`)
  const extractor = new ExtractorService()
  const anonymizer = new Anonymizer()

  try {
    isLoading.value = true

    // 1. Extract & Preprocess
    const rawText = await extractor.extractText(file)
    anonymizer.reset()
    const secureText = anonymizer.process(rawText)

    // 2. Send
    const response = await fetch('http://yurtadotsafe-api.loca.lt/api/analyze/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: 0,
        content: secureText
      })
    })

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`)
    }

    const backendData = await response.json()
    console.log('[Backend]:', backendData)

    // 3. Get & Open Modal
    result.value = {
      raw: rawText,
      secure: secureText,
      analysis: backendData
    }
    isModalOpen.value = true

  } catch (error) {
    console.error('File error:', error)
  } finally {
    isLoading.value = false
  }
}

// UI Points
const detectionPoints = [
  {
    title: 'Финансовые риски',
    text: 'Подсветим условия удержания депозита, штрафы и порядок изменения арендной платы.',
  },
  {
    title: 'Сроки и расторжение',
    text: 'Проверим правила выселения и порядок уведомления о прекращении договора.',
  },
  {
    title: 'И другие спорные пункты',
    text: 'Обратим внимание на нетипичные обязанности и потенциальные риски.',
  },
]
</script>

<template>
  <div class="page">
    <!-- Background with Overlay & bg_workspace.jpeg -->
    <div class="backdrop" aria-hidden="true">
      <img src="../assets/bg_workspace.jpeg" alt="" class="backdrop-img" />
      <div class="backdrop-overlay"></div>
    </div>

    <!-- Topbar: Logo Left -->
    <header class="topbar">
      <router-link to="/" class="logo" aria-label="Yurta.safe">
        <img src="../assets/logo.png" alt="YURTA.safe" class="logo-img" />
      </router-link>
    </header>

    <main class="content">
      <!-- History -->
      <section class="section">
        <h2 class="section__title">Ваши прошлые анализы:</h2>

        <ul v-if="pastAnalyses.length" class="history-list">
          <li v-for="(item, index) in pastAnalyses" :key="item.id" class="history-item">
            <span class="history-item__number">{{ index + 1 }}.</span>
            <span class="history-item__title">{{ item.title }}</span>
            <span class="history-item__date">{{ item.date }}</span>
          </li>
        </ul>

        <p v-else class="empty-state">
          Здесь появятся ваши прошлые анализы, как только вы загрузите первый договор.
        </p>
      </section>

      <!-- Load & Info -->
      <section class="section section--split">
        <div class="upload-block">
          <h2 class="section__title">Загрузите ваш договор (PDF / PNG)</h2>

          <div
            class="dropzone"
            :class="{ 'dropzone--active': isDragging, 'dropzone--filled': fileLabel }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop="handleDrop"
            @click="openFilePicker"
            role="button"
            tabindex="0"
            @keydown.enter="openFilePicker"
          >
            <input
              ref="fileInput"
              type="file"
              class="dropzone__input"
              :accept="acceptedTypes.join(',')"
              @change="handleFileChange"
            />
            <p v-if="!fileLabel" class="dropzone__hint">
              Перетащите файл сюда или нажмите, чтобы выбрать
            </p>
            <p v-else class="dropzone__filename">{{ fileLabel }}</p>
          </div>

          <button
            type="button"
            class="submit-btn"
            :disabled="!fileLabel || isLoading"
            @click="submitAnalysis"
          >
            {{ isLoading ? 'Анализируем...' : 'Проверить договор' }}
          </button>
        </div>

        <aside class="detection-panel">
          <h3 class="detection-panel__title">Что мы ищем в договоре:</h3>

          <div
            v-for="point in detectionPoints"
            :key="point.title"
            class="detection-item"
          >
            <span class="detection-item__title">{{ point.title }}</span>
            <span class="detection-item__text">{{ point.text }}</span>
          </div>
        </aside>
      </section>
    </main>

    <!-- Modal Window for Results -->
    <Teleport to="body">
      <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
        <div class="modal-container" role="dialog" aria-modal="true">
          <header class="modal-header">
            <h2 class="modal-title">Результат анализа договора</h2>
            <button type="button" class="modal-close" @click="closeModal" aria-label="Закрыть">
              ✕
            </button>
          </header>

          <div class="modal-body">
            <div v-if="result" class="result-content">
              <pre>{{ result.secure }}</pre>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <Footer />
  </div>
</template>

<style scoped>
.page {
  position: relative;
  min-height: 100vh;
  background-color: var(--lime);
  color: var(--bg-deep);
  display: flex;
  flex-direction: column;
}

.backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.backdrop-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.55;
}

.backdrop-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(155, 232, 108, 0.65) 0%, rgba(155, 232, 108, 0.95) 100%);
}

.topbar,
.content {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.topbar {
  padding: 24px clamp(20px, 6vw, 72px) 0;
  text-align: left;
}

.logo-img {
  height: 160px;
  width: auto;
  display: inline-block;
  margin: 0;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 56px;
  padding: 40px clamp(20px, 6vw, 72px) 64px;
  flex-grow: 1;
}

/* Без подчеркиваний */
.section__title {
  font-family: var(--font-display, 'Montserrat', sans-serif);
  font-weight: 700;
  font-size: 24px;
  color: var(--bg-deep);
  text-decoration: none;
  margin: 0 0 20px;
}

/* ---------- Прошлые анализы ---------- */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 28px;
  border-radius: 999px;
  background: var(--text-primary);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
  font-family: var(--font-display, 'Montserrat', sans-serif);
  font-weight: 700;
  color: var(--bg-deep);
}

.history-item__number {
  flex-shrink: 0;
  color: var(--bg-panel);
}

.history-item__title {
  flex: 1;
  min-width: 0;
}

.history-item__date {
  flex-shrink: 0;
  font-weight: 500;
  color: var(--text-muted);
  font-size: 14px;
}

.empty-state {
  padding: 24px 28px;
  border-radius: 20px;
  background: var(--text-primary);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
  color: var(--text-muted);
  font-weight: 600;
  text-align: center;
  width: 100%;
  box-sizing: border-box;
}

/* ---------- Загрузка договора ---------- */
.section--split {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 40px;
  align-items: start;
}

.upload-block {
  display: flex;
  flex-direction: column;
}

.dropzone {
  position: relative;
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border-radius: 28px;
  background: var(--text-primary);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
  cursor: pointer;
  text-align: center;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.dropzone:focus-visible {
  outline: 3px solid var(--bg-panel);
  outline-offset: 3px;
}

.dropzone--active {
  box-shadow: 0 0 0 3px var(--bg-panel);
  transform: scale(1.01);
}

.dropzone__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
}

.dropzone__hint {
  color: var(--text-muted);
  font-weight: 600;
  margin: 0;
}

.dropzone__filename {
  color: var(--bg-panel);
  font-weight: 700;
  margin: 0;
  word-break: break-word;
}

.submit-btn {
  align-self: flex-start;
  margin-top: 20px;
  padding: 14px 32px;
  border: none;
  border-radius: 999px;
  background: var(--bg-panel);
  color: var(--text-primary);
  font-family: inherit;
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.submit-btn:not(:disabled):hover {
  opacity: 0.9;
}

/* ---------- Панель детекции ---------- */
.detection-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0;
}

.detection-panel__title {
  font-family: var(--font-display, 'Montserrat', sans-serif);
  font-weight: 800;
  font-size: 20px;
  color: var(--bg-panel);
  margin: 0 0 4px;
}

.detection-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--text-primary);
  padding: 16px 20px;
  border-radius: 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

.detection-item__title {
  color: var(--bg-panel);
  font-weight: 800;
  font-size: 15px;
}

.detection-item__text {
  color: var(--bg-deep);
  font-weight: 500;
  line-height: 1.4;
  font-size: 13px;
}

/* ---------- Модальное окно результатов ---------- */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(18, 14, 30, 0.7);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.modal-container {
  background: var(--text-primary);
  color: var(--bg-deep);
  width: 100%;
  max-width: 800px;
  max-height: 85vh;
  border-radius: 28px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px;
  border-bottom: 1px solid var(--line);
}

.modal-title {
  font-family: var(--font-display, 'Montserrat', sans-serif);
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: var(--bg-panel);
}

.modal-close {
  background: transparent;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--bg-deep);
  line-height: 1;
  padding: 4px 8px;
  border-radius: 8px;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.05);
}

.modal-body {
  padding: 24px 28px;
  overflow-y: auto; /* Внутренний скролл */
  flex-grow: 1;
}

.result-content pre {
  white-space: pre-wrap;
  word-break: break-word;
  background: rgba(28, 22, 48, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.1);
  padding: 16px;
  border-radius: 16px;
  color: var(--bg-deep);
  font-family: monospace;
  font-size: 14px;
  margin: 0;
}

/* ---------- Responsive ---------- */
@media (max-width: 860px) {
  .section--split {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .history-item {
    flex-wrap: wrap;
    border-radius: 20px;
  }

  .history-item__date {
    width: 100%;
    padding-left: 32px;
  }
}
</style>