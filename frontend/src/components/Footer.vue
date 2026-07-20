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

<style>
/* Footer */
.site-footer {
  border-top: 1px solid var(--line);
  padding: 40px clamp(20px, 6vw, 72px);
  margin-top: auto;
}
.disclaimer {
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 0 0 40px;
  max-width: 1000px;
}
.disclaimer strong { 
  color: var(--text-primary); 
  display: inline-block;
  margin-bottom: 8px;
}

.footer-columns {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 24px;
}
.footer-contact {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.footer-label {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.footer-sublabel {
  font-size: 0.85rem;
  color: var(--text-muted);
}
.footer-contact a { 
  color: var(--text-primary); 
  text-decoration: none; 
  font-size: 1rem; 
  font-weight: 500;
}
.footer-contact a:hover { color: var(--lime); text-decoration: underline; }
.footer-credit { 
  font-size: 0.85rem; 
  color: var(--text-muted); 
}

@media (max-width: 600px) {
  .footer-columns { flex-direction: column; align-items: flex-start; }
}
</style>
