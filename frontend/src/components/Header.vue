<script setup>
import LogoImage from '../assets/images/logo.png'

const props = defineProps({
  padding: {
    type: String,
    default: '24px'
  },
  logoHeight: {
    type: String,
    default: '96px'
  },
  logoAlign: {
    type: String,
    default: 'center'
  }
})
</script>

<template>
  <header 
    class="topbar" 
    :style="{
      '--topbar-padding': props.padding,
      '--logo-height': props.logoHeight,
      '--logo-align': props.logoAlign
    }"
  >
    <a href="/" class="logo" aria-label="Yurta.safe">
      <img :src="LogoImage" alt="YURTA.safe" class="logo-img" />
    </a>
  </header>
</template>

<style scoped>
.topbar {
  padding: var(--topbar-padding) clamp(20px, 6vw, 72px) 0;
  text-align: var(--logo-align);
}

.logo {
  display: inline-block;
}

.logo-img {
  height: var(--logo-height); 
  width: auto;
  display: block;
  margin-bottom: -5%; 
}
</style>