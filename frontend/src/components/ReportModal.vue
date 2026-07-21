<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click.self="emit('close')">
        <div class="modal-container" role="dialog" aria-modal="true">
          
          <!-- Header -->
          <header class="modal-header">
            <div class="header-title-group">
              <div>
                <h2 class="modal-title">Результат анализа договора {{ reportTitle }}</h2>
                <p class="modal-subtitle">Найдено замечаний: {{ findings.length }}</p>
              </div>
            </div>
            <button type="button" class="modal-close" @click="emit('close')" aria-label="Закрыть">
              ✕
            </button>
          </header>

          <!-- Body -->
          <div class="modal-body">
            <div v-if="findings.length" class="findings-list">
              <div 
                v-for="(item, index) in findings" 
                :key="index" 
                class="finding-card" 
                :class="'finding--' + item.category"
              >
                <!-- Card Top Info -->
                <div class="finding-header">
                  <span class="clause-badge">Пункт {{ item.clause_ref }}</span>
                  <span class="category-badge" :class="'badge--' + item.category">
                    {{ getCategoryLabel(item.category) }}
                  </span>
                </div>

                <!-- Excerpt -->
                <blockquote class="finding-excerpt">
                  «{{ item.excerpt }}»
                </blockquote>

                <!-- Explanation -->
                <div class="finding-info">
                  <span class="info-label">Суть:</span>
                  <span class="info-text">{{ item.explanation }}</span>
                </div>

                <!-- Source / Law -->
                <div class="finding-info">
                  <span class="info-label">Источник:</span>
                  <span class="info-text source-text">{{ item.source }}</span>
                </div>

                <!-- Mitigation / Fix -->
                <div v-if="item.mitigation" class="mitigation-box">
                  <div class="mitigation-header">💡 Рекомендация к исправлению:</div>
                  <div class="mitigation-text">{{ item.mitigation }}</div>
                </div>
              </div>
            </div>

            <!-- Empty State -->
            <div v-else class="empty-state">
              <p>Замечания или риски не найдены.</p>
            </div>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  reportData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

const parsedData = computed(() => {
  if (!props.reportData) return {}
  
  let data = props.reportData
  if (typeof data.result === 'string') {
    try {
      data = JSON.parse(data.result)
    } catch (e) {
      return {}
    }
  } else if (typeof data === 'string') {
    try {
      data = JSON.parse(data)
    } catch (e) {
      return {}
    }
  }
  return data || {}
})

const reportTitle = computed(() => {
  return parsedData.value.title || props.reportData?.title || ''
})

const findings = computed(() => {
  return parsedData.value.findings || []
})

const getCategoryLabel = (category) => {
  const map = {
    risk: 'Риск',
    obligation: 'Обязанность',
    deadline: 'Срок',
    right: 'Право'
  }
  return map[category] || category
}
</script>

<style scoped>
.modal-container,
.modal-container * {
  font-family: 'IBM Plex Sans', sans-serif;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: var(--bg-deep);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* Main container */
.modal-container {
  background: #e3e3e3;
  width: 100%;
  max-width: 760px;
  max-height: 85vh;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--line);
}

/* Header */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--text-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 2;
}

.header-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--bg-deep);
}

.modal-subtitle {
  margin: 4px 0 0 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.modal-close {
  background: transparent;
  border: none;
  font-size: 20px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: var(--line);
  color: var(--bg-deep);
}

/* Body & Cards list */
.modal-body {
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Cards style */
.finding-card {
  border-radius: 12px;
  padding: 16px 20px;
  background: #f5f5f5;
  border: 1px solid var(--line);
  border-left: 5px solid var(--line);
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Border colors */
.finding--risk { border-left-color: #ef4444; background: #fffafb; }
.finding--obligation { border-left-color: #3b82f6; }
.finding--deadline { border-left-color: #f59e0b; }
.finding--right { border-left-color: #10b981; }

/* Card header */
.finding-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.clause-badge {
  font-size: 0.85rem;
  font-weight: 700;
  color: #334155;
  background: var(--text-primary);
  border: 1px solid var(--line);
  padding: 4px 10px;
  border-radius: 6px;
}

.category-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Badge colors */
.badge--risk { background: #fee2e2; color: #991b1b; }
.badge--obligation { background: #dbeafe; color: #1e40af; }
.badge--deadline { background: #fef3c7; color: #92400e; }
.badge--right { background: #d1fae5; color: #065f46; }

/* Excerpt */
.finding-excerpt {
  margin: 0;
  padding: 10px 14px;
  background: var(--line);
  border-radius: 8px;
  font-style: italic;
  font-size: 0.92rem;
  color: #334155;
  line-height: 1.45;
  border-left: 2px solid var(--line);
}

/* Info row */
.finding-info {
  font-size: 0.9rem;
  line-height: 1.4;
  display: flex;
  gap: 6px;
}

.info-label {
  font-weight: 600;
  color: #475569;
  min-width: 70px;
}

.info-text {
  color: #1e293b;
}

.source-text {
  color: var(--text-muted);
  font-style: italic;
}

/* Mitigation box */
.mitigation-box {
  margin-top: 4px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 12px 14px;
  border-radius: 8px;
}

.mitigation-header {
  font-size: 0.85rem;
  font-weight: 700;
  color: #166534;
  margin-bottom: 4px;
}

.mitigation-text {
  font-size: 0.9rem;
  color: #14532d;
  line-height: 1.4;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

/* Modal Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>