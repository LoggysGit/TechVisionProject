import * as pdfjsLib from 'pdfjs-dist/build/pdf.mjs';

const { createWorker } = Tesseract;

pdfjsLib.GlobalWorkerOptions.workerSrc =
  new URL('./node_modules/pdfjs-dist/build/pdf.worker.mjs', import.meta.url).href;

export class ExtractorService {
  async extractText(file) {
    const fileType = file.type;
    const extension = file.name.split('.').pop().toLowerCase();

    if (fileType === 'application/pdf' || extension === 'pdf') {
      return await this._extractFromPdf(file);
    }

    if (fileType.startsWith('image/') || ['png', 'jpg', 'jpeg'].includes(extension)) {
      return await this._extractFromImage(file);
    }

    throw new Error('Format is not supported.');
  }

  // PDF
  async _extractFromPdf(file) {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let fullText = '';

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map(item => item.str).join(' ');
      fullText += pageText + '\n';
    }
    return fullText;
  }

  // OCR
  async _extractFromImage(file) {
    const worker = await createWorker('rus+eng');
    const { data: { text } } = await worker.recognize(file);
    await worker.terminate();
    return text;
  }
}

export class Anonymizer {
  constructor() {
    this.patterns = {
      iin: /\b\d{12}\b/g,
      phone: /(?<!\d)(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)/g,
      card: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
      iban: /\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g,
      email: /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g,
      idCard: /(Удостоверение личности[^:]*:\s*|Документ,\s*удостоверяющий личность:\s*)(\d{9})/gi
    };

    this.history = { iin: {}, phone: {}, card: {}, iban: {}, email: {}, idCard: {} };
    this.counters = { iin: 1, phone: 1, card: 1, iban: 1, email: 1, idCard: 1 };
  }

  process(text) {
    if (!text) return '';
    let processedText = text;

    const items = [
      [this.patterns.iban, 'iban', 'IBAN'],
      [this.patterns.card, 'card', 'КАРТА'],
      [this.patterns.phone, 'phone', 'ТЕЛЕФОН'],
      [this.patterns.iin, 'iin', 'ИИН'],
      [this.patterns.email, 'email', 'EMAIL'],
    ]

    for (const key of items){
      processedText = this._replace(processedText, key[0], key[1], key[2]);
    }
    processedText = this._replaceIdCard(processedText);

    return processedText;
  }

  _replace(text, regex, type, label) {
    return text.replace(regex, (match) => {
      const cleanMatch = match.replace(/[\s\-()]/g, '');

      if (this.history[type][cleanMatch]) {
        return `[${label}_${this.history[type][cleanMatch]}]`;
      }

      const currentId = this.counters[type];
      this.history[type][cleanMatch] = currentId;
      this.counters[type]++;

      return `[${label}_${currentId}]`;
    });
  }

  _replaceIdCard(text) {
    return text.replace(this.patterns.idCard, (fullMatch, label, value) => {
      if (this.history.idCard[value]) {
        return `${label}[ID_${this.history.idCard[value]}]`;
      }

      const currentId = this.counters.idCard;
      this.history.idCard[value] = currentId;
      this.counters.idCard++;

      return `${label}[ID_${currentId}]`;
    });
  }

  reset() {
    this.history = { iin: {}, phone: {}, card: {}, iban: {}, email: {}, idCard: {} };
    this.counters = { iin: 1, phone: 1, card: 1, iban: 1, email: 1, idCard: 1 };
  }
}