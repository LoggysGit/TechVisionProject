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

            <!-- Controls Group (Export + Close) -->
            <div class="header-actions">
              <button 
                type="button" 
                class="modal-action-btn export-btn" 
                @click="exportReport" 
                title="Экспортировать в PDF"
                aria-label="Экспортировать отчет"
              >
                <!-- SVG -->
                <svg class="icon-blank" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="12" y1="18" x2="12" y2="12"></line>
                  <line x1="9" y1="15" x2="15" y2="15"></line>
                </svg>
                <span>Экспорт</span>
              </button>

              <button type="button" class="modal-close" @click="emit('close')" aria-label="Закрыть">
                ✕
              </button>
            </div>
          </header>

          <!-- Body -->
          <div class="modal-body" id="pdf-export-content">
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
import pdfMake from 'pdfmake/build/pdfmake'
import pdfFonts from 'pdfmake/build/vfs_fonts'

// Fonts
pdfMake.vfs = pdfFonts.pdfMake ? pdfFonts.pdfMake.vfs : pdfFonts.vfs

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

  let data = props.reportData.report
  if (data.result && typeof data.result === 'string') {
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
  return parsedData.value.title || props.reportData?.title || '-'
})

const findings = computed(() => {
  return parsedData.value.findings || []
})

const getCategoryLabel = (category) => {
  const map = {
    risk: 'РИСК',
    obligation: 'ОБЯЗАННОСТЬ',
    deadline: 'СРОК',
    right: 'ПРАВО'
  }
  return map[category] || category.toUpperCase()
}

const getCategoryColor = (category) => {
  const map = {
    risk: '#c53030',       // Dark-red
    obligation: '#2b6cb0', // Dark-blue
    deadline: '#c05621',   // Dark-orange
    right: '#2f855a'       // Dark-green
  }
  return map[category] || '#4a5568'
}

const exportReport = () => {
  if (!findings.value.length) return

  // Form document content
  const content = []

  // Header
  content.push({
    text: `ОТЧЕТ АНАЛИЗА ДОГОВОРА`,
    style: 'docHeader'
  })

  if (reportTitle.value) {
    content.push({
      text: `Документ: ${reportTitle.value}`,
      style: 'docSubHeader'
    })
  }

  content.push({
    text: `Дата генерации: ${new Date().toLocaleDateString('ru-RU')} | Найдено замечаний: ${findings.value.length}`,
    style: 'docMeta'
  })

  content.push({
    canvas: [{ type: 'line', x1: 0, y1: 5, x2: 515, y2: 5, lineWidth: 1, lineColor: '#cbd5e0' }],
    margin: [0, 0, 0, 15]
  })

  // Main
  findings.value.forEach((item, _) => {
    const catLabel = getCategoryLabel(item.category)
    const catColor = getCategoryColor(item.category)

    const cardContent = [
      {
        columns: [
          { text: `Пункт ${item.clause_ref || '—'}`, style: 'clauseBadge', width: '*' },
          { text: catLabel, color: catColor, style: 'categoryBadge', alignment: 'right', width: 'auto' }
        ],
        margin: [0, 0, 0, 6]
      },
      {
        text: `«${item.excerpt}»`,
        style: 'excerpt'
      },
      {
        text: [
          { text: 'Суть: ', bold: true, color: '#4a5568' },
          { text: item.explanation, color: '#1a202c' }
        ],
        margin: [0, 0, 0, 4]
      }
    ]
    // Source
    if (item.source) {
      cardContent.push({
        text: [
          { text: 'Источник: ', bold: true, color: '#4a5568' },
          { text: item.source, italics: true, color: '#718096' }
        ],
        margin: [0, 0, 0, 4]
      })
    }
    // Mitigation
    if (item.mitigation) {
      cardContent.push({
        table: {
          widths: ['*'],
          body: [[
            {
              stack: [
                { text: 'Рекомендация правки:', bold: true, color: '#276749', margin: [0, 0, 0, 2] },
                { text: item.mitigation, color: '#2f855a' }
              ],
              fillColor: '#f0fff4',
              borderColor: ['#c6f6d5', '#c6f6d5', '#c6f6d5', '#c6f6d5'],
              margin: [8, 6, 8, 6]
            }
          ]]
        },
        margin: [0, 4, 0, 0]
      })
    }

    // Push all
    content.push({
      unbreakable: true,
      margin: [0, 0, 0, 12],
      table: {
        widths: ['*'],
        body: [[
          {
            stack: cardContent,
            fillColor: '#f7fafc',
            borderColor: ['#e2e8f0', '#e2e8f0', '#e2e8f0', '#e2e8f0'],
            border: [true, true, true, true],
            padding: [12, 10, 12, 10]
          }
        ]]
      }
    })
  })

  // Document entity & styles
  const docDefinition = {
    pageSize: 'A4',
    pageMargins: [40, 40, 40, 40],
    content: content,
    styles: {
      docHeader: {
        fontSize: 16,
        bold: true,
        color: '#1a202c',
        margin: [0, 0, 0, 4]
      },
      docSubHeader: {
        fontSize: 11,
        bold: true,
        color: '#4a5568',
        margin: [0, 0, 0, 2]
      },
      docMeta: {
        fontSize: 9,
        color: '#718096',
        margin: [0, 0, 0, 10]
      },
      clauseBadge: {
        fontSize: 11,
        bold: true,
        color: '#2d3748'
      },
      categoryBadge: {
        fontSize: 10,
        bold: true
      },
      excerpt: {
        fontSize: 9.5,
        italics: true,
        color: '#2d3748',
        margin: [0, 0, 0, 6]
      }
    },
    defaultStyle: {
      fontSize: 9.5,
      lineHeight: 1.2
    }
  }

  pdfMake.createPdf(docDefinition).download(`Отчет_${reportTitle.value || 'договора'}.pdf`)
}
</script>

<style scoped>
.modal-container,
.modal-container * {
  font-family: 'IBM Plex Sans', sans-serif;
  box-sizing: border-box;
}

/* Overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(18, 14, 30, 0.82);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* Container */
.modal-container {
  background: var(--bg-panel, #1c1630);
  width: 100%;
  max-width: 760px;
  max-height: 85vh;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--line, rgba(255, 255, 255, 0.15));
  color: var(--text-primary, #f4f2f9);
}

/* Header */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--line, rgba(255, 255, 255, 0.15));
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #161126;
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
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary, #f4f2f9);
}

.modal-subtitle {
  margin: 4px 0 0 0;
  font-size: 0.85rem;
  color: var(--text-muted, #b3a9c7);
}

/* Buttons */
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--lime-dim, rgba(155, 232, 108, 0.14));
  border: 1px solid var(--lime, #9be86c);
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--lime, #9be86c);
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-action-btn:hover {
  background: var(--lime, #9be86c);
  color: #120e1e;
  transform: translateY(-1px);
}

.icon-blank {
  opacity: 0.9;
}

.modal-close {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--line, rgba(255, 255, 255, 0.15));
  font-size: 16px;
  color: var(--text-muted, #b3a9c7);
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.15);
  color: var(--text-primary, #f4f2f9);
}

/* Body */
.modal-body {
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--bg-panel, #1c1630);
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Cards */
.finding-card {
  border-radius: 12px;
  padding: 18px 20px;
  background: #241c3d;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-left: 5px solid var(--line, rgba(255, 255, 255, 0.15));
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  gap: 12px;

  page-break-inside: avoid !important;
  break-inside: avoid !important;
}

/* Badges pallete */
.finding--risk { border-left-color: #ef4444; }
.finding--obligation { border-left-color: #60a5fa; }
.finding--deadline { border-left-color: #fbbf24; }
.finding--right { border-left-color: var(--lime, #9be86c); }

.finding-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.clause-badge {
  font-size: 0.85rem;
  font-weight: 700;
  color: #e2daee;
  background: #161126;
  border: 1px solid var(--line, rgba(255, 255, 255, 0.15));
  padding: 4px 10px;
  border-radius: 6px;
}

.category-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Catigories pallete */
.badge--risk { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }
.badge--obligation { background: rgba(96, 165, 250, 0.2); color: #93c5fd; border: 1px solid rgba(96, 165, 250, 0.4); }
.badge--deadline { background: rgba(251, 191, 36, 0.2); color: #fde68a; border: 1px solid rgba(251, 191, 36, 0.4); }
.badge--right { background: var(--lime-dim, rgba(155, 232, 108, 0.14)); color: var(--lime, #9be86c); border: 1px solid var(--lime, #9be86c); }

.finding-excerpt {
  margin: 0;
  padding: 10px 14px;
  background: #1a132e;
  border-radius: 8px;
  font-style: italic;
  font-size: 0.92rem;
  color: #d3cbdc;
  line-height: 1.45;
  border-left: 3px solid var(--lime, #9be86c);
}

.finding-info {
  font-size: 0.9rem;
  line-height: 1.4;
  display: flex;
  gap: 8px;
}

.info-label {
  font-weight: 600;
  color: var(--text-muted, #b3a9c7);
  min-width: 75px;
}

.info-text {
  color: var(--text-primary, #f4f2f9);
}

.source-text {
  color: #a397bd;
  font-style: italic;
}

.mitigation-box {
  margin-top: 4px;
  background: rgba(155, 232, 108, 0.08);
  border: 1px solid rgba(155, 232, 108, 0.25);
  padding: 12px 14px;
  border-radius: 8px;
}

.mitigation-header {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--lime, #9be86c);
  margin-bottom: 4px;
}

.mitigation-text {
  font-size: 0.9rem;
  color: #d9f5c2;
  line-height: 1.4;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-muted, #b3a9c7);
}

/* Animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>