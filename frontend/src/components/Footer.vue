<script setup>
</script>

<template>
  <footer class="site-footer">
    <p class="disclaimer">
      <strong>Дисклеймер</strong><br />
      Инструмент Yurta.safe работает на базе генеративных трансформеров (искусственного интеллекта) и предназначен исключительно для информационных целей и первичного анализа документов. Результаты работы платформы не являются квалифицированной юридической консультацией или официальным правовым заключением. Для принятия юридически значимых решений рекомендуется обращаться к профильным юристам.
    </p>
    
    <div class="footer-columns">
      <div class="footer-contact">
        <span class="footer-label">Get in Touch</span>
        <span class="footer-sublabel">Partnerships & Collaborations:</span>
        <a href="mailto:itemail@yurta.safe">itemail@yurta.safe</a>
      </div>
      <div class="footer-credit">
        Yurta.safe, 2026. Website was made by Usmanova I. & Metsler A.
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  all: initial !important;
  display: block !important;
  box-sizing: border-box !important;
  width: 100% !important;
  background-color: #120e1e !important;
  border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
  padding: 40px clamp(20px, 6vw, 72px) !important;
  margin-top: auto !important;
  font-family: sans-serif !important;
  color: #f4f2f9 !important;
  position: relative !important;
  z-index: 10 !important;
}

.disclaimer {
  font-size: 0.85rem !important;
  line-height: 1.6 !important;
  color: #b3a9c7 !important;
  margin: 0 0 40px !important;
  max-width: 1000px !important;
}

.disclaimer strong { 
  color: #f4f2f9 !important; 
  display: inline-block !important;
  margin-bottom: 8px !important;
}

.footer-columns {
  display: flex !important;
  justify-content: space-between !important;
  align-items: flex-end !important;
  flex-wrap: wrap !important;
  gap: 24px !important;
}

.footer-contact {
  display: flex !important;
  flex-direction: column !important;
  gap: 4px !important;
}

.footer-label {
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 600 !important;
  font-size: 1rem !important;
  color: #f4f2f9 !important;
  margin-bottom: 4px !important;
}

.footer-sublabel {
  font-size: 0.85rem !important;
  color: #b3a9c7 !important;
}

.footer-contact a { 
  color: #f4f2f9 !important; 
  text-decoration: none !important; 
  font-size: 1rem !important; 
  font-weight: 500 !important;
}

.footer-contact a:hover { 
  color: #9be86c !important; 
  text-decoration: underline !important; 
}

.footer-credit { 
  font-size: 0.85rem !important; 
  color: #b3a9c7 !important; 
}

@media (max-width: 600px) {
  .footer-columns { 
    flex-direction: column !important; 
    align-items: flex-start !important; 
  }
}
</style>