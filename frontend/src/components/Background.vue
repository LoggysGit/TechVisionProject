<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  imageSrc: {
    type: String,
    required: true
  },
  speed: {
    type: Number,
    default: 0.2
  }
})

const scrollY = ref(0)

function handleScroll() {
  scrollY.value = window.scrollY
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="backdrop" aria-hidden="true">
    <img 
      :src="props.imageSrc" 
      alt="" 
      class="backdrop-img"
      :style="{
        transform: `translate3d(0, ${scrollY * -props.speed}px, 0) scale(1.15)`
      }"
    />
    <div class="backdrop-overlay"></div>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.backdrop-img {
  width: 100%;
  height: 125%;
  object-fit: cover;
  opacity: 0.5;
  filter: blur(2px);
  will-change: transform;
}

.backdrop-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg, 
    rgba(18, 14, 30, 0.05) 0%,
    rgba(18, 14, 30, 0.5) 60%,
    var(--bg-deep) 100%
  );
}
</style>