<template>
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="isOpen" class="modal-overlay" @click.self="emit('close')">
          <div class="modal-container" role="dialog" aria-modal="true">
            
            <!-- Header -->
            <header class="modal-header">
              <div class="header-title-group">
                <span class="header-icon">🛡️</span>
                <div>
                  <h2 class="modal-title">Результат анализа договора</h2>
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
  
  const findings = computed(() => {
    if (!props.reportData) return []
    
    let data = props.reportData
    if (typeof data.result === 'string') {
      try {
        data = JSON.parse(data.result)
      } catch (e) {
        return []
      }
    } else if (typeof data === 'string') {
      try {
        data = JSON.parse(data)
      } catch (e) {
        return []
      }
    }
  
    return data.findings || []
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
  /* Overlay & Backdrop Filter */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 20px;
  }
  
  /* Main Container */
  .modal-container {
    background: #ffffff;
    width: 100%;
    max-width: 760px;
    max-height: 85vh;
    border-radius: 16px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #e2e8f0;
  }
  
  /* Header */
  .modal-header {
    padding: 20px 24px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f8fafc;
  }
  
  .header-title-group {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .header-icon {
    font-size: 24px;
  }
  
  .modal-title {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
  }
  
  .modal-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.85rem;
    color: #64748b;
  }
  
  .modal-close {
    background: transparent;
    border: none;
    font-size: 20px;
    color: #64748b;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    transition: all 0.2s;
  }
  
  .modal-close:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
  
  /* Body & Cards List */
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
  
  /* Cards Base Style */
  .finding-card {
    border-radius: 12px;
    padding: 16px 20px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #cbd5e1;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  /* Border Accent per Category */
  .finding--risk { border-left-color: #ef4444; background: #fffafb; }
  .finding--obligation { border-left-color: #3b82f6; }
  .finding--deadline { border-left-color: #f59e0b; }
  .finding--right { border-left-color: #10b981; }
  
  /* Card Header */
  .finding-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .clause-badge {
    font-size: 0.85rem;
    font-weight: 700;
    color: #334155;
    background: #f1f5f9;
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
  
  /* Badge Accent Colors */
  .badge--risk { background: #fee2e2; color: #991b1b; }
  .badge--obligation { background: #dbeafe; color: #1e40af; }
  .badge--deadline { background: #fef3c7; color: #92400e; }
  .badge--right { background: #d1fae5; color: #065f46; }
  
  /* Excerpt Blockquote */
  .finding-excerpt {
    margin: 0;
    padding: 10px 14px;
    background: rgba(241, 245, 249, 0.6);
    border-radius: 8px;
    font-style: italic;
    font-size: 0.92rem;
    color: #334155;
    line-height: 1.45;
  }
  
  /* Info Row */
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
    color: #64748b;
    font-style: italic;
  }
  
  /* Mitigation Box */
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
    color: #94a3b8;
  }
  
  /* Vue Modal Transitions */
  .modal-enter-active,
  .modal-leave-active {
    transition: opacity 0.25s ease;
  }
  
  .modal-enter-from,
  .modal-leave-to {
    opacity: 0;
  }
  </style>