<script setup>
import { ref } from 'vue'

const isVisible = ref(false)
const message = ref('')
const type = ref('info') // 'info', 'error', 'success'
let timer = null

function show(msg, msgType = 'info', duration = 3000) {
  message.value = msg
  type.value = msgType
  isVisible.value = true

  clearTimeout(timer)
  
  timer = setTimeout(() => {
    isVisible.value = false
  }, duration)
}

defineExpose({ show })
</script>

<template>
  <Transition name="notification">
    <div v-if="isVisible" class="notification" :class="type">
      <span class="badge">Notification</span>
      <span class="text">{{ message }}</span>
    </div>
  </Transition>
</template>

<style scoped>
.notification {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  
  display: flex;
  align-items: center;
  gap: 12px;
  
  padding: 12px 18px;
  border-radius: 8px;
  background: rgba(18, 14, 30, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  font-family: monospace;
  font-size: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
}

.badge {
  background: #3b82f6;
  color: #fff;
  font-size: 10px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 4px;
}

/* Notification types styles */
.notification.error .badge { background: #ef4444; }
.notification.success .badge { background: #10b981; }

/* Animations */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.notification-enter-from,
.notification-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.95);
}
</style>