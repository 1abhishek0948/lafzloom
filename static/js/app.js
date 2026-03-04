const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
};

const csrfToken = getCookie('csrftoken');

const i18n = window.LAFZVERSE_I18N || {};
const languages = ['hi', 'en', 'ur'];
const languageLabels = i18n.languageLabels || { hi: 'Hindi', en: 'English', ur: 'Urdu' };
const translateToTemplate = i18n.translateTo || 'Translate → {language}';
const translatingLabel = i18n.translating || 'Translating...';
const translationUnavailable =
  i18n.translationUnavailable || 'Translation service unavailable. Configure the provider in .env.';
const loginToLike = i18n.loginToLike || 'Please login to like shayaris.';
const loginToSave = i18n.loginToSave || 'Please login to save shayaris.';
const savedLabel = i18n.saved || 'Saved';
const saveLabel = i18n.save || 'Save';
const copiedLabel = i18n.copied || 'Copied';
const copyLabel = i18n.copy || 'Copy';
const copyFailedLabel = i18n.copyFailed || 'Copy failed.';
const linkCopiedLabel = i18n.linkCopied || 'Link copied to clipboard.';
const showPasswordLabel = i18n.showPassword || 'Show password';
const hidePasswordLabel = i18n.hidePassword || 'Hide password';

const getNextTarget = (source, currentTarget) => {
  const options = languages.filter((lang) => lang !== source);
  if (!currentTarget || !options.includes(currentTarget)) {
    return options[0];
  }
  const idx = options.indexOf(currentTarget);
  return options[(idx + 1) % options.length];
};

const findTextFor = (element) => {
  const container = element.closest('.card, .card-glow, article');
  if (!container) return '';
  const textArea = container.querySelector('.shayari-text');
  return textArea ? textArea.value || textArea.textContent : '';
};

const setTranslationOutput = (element, translation, targetLang) => {
  const container = element.closest('.card, .card-glow, article');
  if (!container) return;
  const output = container.querySelector('.translation-output');
  if (!output) return;
  output.classList.remove('hidden');
  output.textContent = `${languageLabels[targetLang]}: ${translation}`;
};

const handleLike = async (button) => {
  if (!csrfToken) {
    alert(loginToLike);
    return;
  }
  const url = button.dataset.likeUrl;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
    },
  });
  if (!response.ok) return;
  const data = await response.json();
  const countEl = button.querySelector('.like-count');
  if (countEl) countEl.textContent = data.count;
  button.classList.toggle('active', data.liked);
};

const handleSave = async (button) => {
  if (!csrfToken) {
    alert(loginToSave);
    return;
  }
  const url = button.dataset.saveUrl;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
    },
  });
  if (!response.ok) return;
  const data = await response.json();
  button.textContent = data.saved ? savedLabel : saveLabel;
};

const handleTranslate = async (button) => {
  const text = findTextFor(button);
  if (!text.trim()) return;
  const sourceLang = button.dataset.sourceLang || 'hi';
  const currentTarget = button.dataset.targetLang || getNextTarget(sourceLang, null);
  button.textContent = translatingLabel;
  const response = await fetch('/api/translate/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken || '',
    },
    body: JSON.stringify({
      text,
      source_lang: sourceLang,
      target_lang: currentTarget,
    }),
  });
  if (!response.ok) {
    setTranslationOutput(button, translationUnavailable, currentTarget);
    updateTranslateButtons();
    return;
  }
  const data = await response.json();
  setTranslationOutput(button, data.translation, currentTarget);
  const nextTarget = getNextTarget(sourceLang, currentTarget);
  button.dataset.targetLang = nextTarget;
  updateTranslateButtons();
};

const handleCopy = async (button) => {
  const text = findTextFor(button);
  if (!text.trim()) return;
  try {
    await navigator.clipboard.writeText(text);
    button.textContent = copiedLabel;
    setTimeout(() => (button.textContent = copyLabel), 1500);
  } catch (err) {
    alert(copyFailedLabel);
  }
};

const handleShare = async (button) => {
  const url = button.dataset.shareUrl || window.location.href;
  try {
    if (navigator.share) {
      await navigator.share({ title: document.title, url });
    } else {
      await navigator.clipboard.writeText(url);
      alert(linkCopiedLabel);
    }
  } catch (err) {
    console.error(err);
  }
};

const updateTranslateButtons = () => {
  document.querySelectorAll('.btn-translate').forEach((button) => {
    const source = button.dataset.sourceLang || 'hi';
    const target = button.dataset.targetLang || getNextTarget(source, null);
    button.dataset.targetLang = target;
    button.textContent = translateToTemplate.replace('{language}', languageLabels[target]);
  });
};

const buildPasswordToggleButton = (labels, targetId = '') => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'password-toggle';
  button.dataset.passwordToggle = 'true';
  button.dataset.target = targetId;
  button.dataset.showLabel = labels.show;
  button.dataset.hideLabel = labels.hide;
  button.setAttribute('aria-label', labels.show);
  button.textContent = labels.show;
  return button;
};

const preparePasswordToggleButton = (button) => {
  const showLabel = button.dataset.showLabel || showPasswordLabel;
  const hideLabel = button.dataset.hideLabel || hidePasswordLabel;
  button.dataset.showLabel = showLabel;
  button.dataset.hideLabel = hideLabel;
  if (!button.textContent.trim()) {
    button.textContent = showLabel;
  }
  button.setAttribute('aria-label', showLabel);
  button.setAttribute('aria-pressed', 'false');
};

const bindPasswordToggle = (button) => {
  if (button.dataset.bound === 'true') return;
  preparePasswordToggleButton(button);
  button.dataset.bound = 'true';
  button.addEventListener('click', () => {
    const targetId = button.dataset.target;
    const wrapper = button.closest('.password-field');
    const input = (targetId && document.getElementById(targetId)) || wrapper?.querySelector('input');
    if (!input) return;
    const shouldShow = input.type === 'password';
    input.type = shouldShow ? 'text' : 'password';
    button.classList.toggle('is-visible', shouldShow);
    const showLabel = button.dataset.showLabel;
    const hideLabel = button.dataset.hideLabel;
    const label = shouldShow ? hideLabel : showLabel;
    button.setAttribute('aria-label', label);
    button.setAttribute('aria-pressed', shouldShow ? 'true' : 'false');
    button.textContent = label;
  });
};

const initPasswordToggles = () => {
  const labels = { show: showPasswordLabel, hide: hidePasswordLabel };

  document.querySelectorAll('[data-password-toggle]').forEach((button) => {
    bindPasswordToggle(button);
  });

  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const container = input.closest('.password-field') || input.parentElement;
    if (!container) return;
    const existing = container.querySelector('[data-password-toggle]');
    if (existing) {
      bindPasswordToggle(existing);
      return;
    }
    container.classList.add('password-field');
    const button = buildPasswordToggleButton(labels, input.id || '');
    container.appendChild(button);
    bindPasswordToggle(button);
  });
};

const handleClick = (event) => {
  const likeBtn = event.target.closest('.btn-like');
  if (likeBtn) {
    handleLike(likeBtn);
    return;
  }
  const saveBtn = event.target.closest('.btn-save');
  if (saveBtn) {
    handleSave(saveBtn);
    return;
  }
  const translateBtn = event.target.closest('.btn-translate');
  if (translateBtn) {
    handleTranslate(translateBtn);
    return;
  }
  const copyBtn = event.target.closest('.btn-copy');
  if (copyBtn) {
    handleCopy(copyBtn);
    return;
  }
  const shareBtn = event.target.closest('.btn-share');
  if (shareBtn) {
    handleShare(shareBtn);
    return;
  }
};

document.addEventListener('DOMContentLoaded', () => {
  updateTranslateButtons();
  document.body.addEventListener('click', handleClick);
  initPasswordToggles();

  const langToggle = document.querySelector('.lang-toggle');
  const langMenu = document.querySelector('#mobile-lang-menu');

  const closeLangMenu = () => {
    if (!langToggle || !langMenu) {
      return;
    }
    langMenu.classList.add('hidden');
    langToggle.classList.remove('is-open');
    langToggle.setAttribute('aria-expanded', 'false');
  };

  if (langToggle && langMenu) {
    langToggle.addEventListener('click', (event) => {
      event.stopPropagation();
      const isHidden = langMenu.classList.contains('hidden');
      langMenu.classList.toggle('hidden', !isHidden);
      langToggle.classList.toggle('is-open', isHidden);
      langToggle.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
    });

    langMenu.addEventListener('click', (event) => {
      if (event.target.closest('button') || event.target.closest('a')) {
        closeLangMenu();
      }
    });

    document.addEventListener('click', (event) => {
      if (!langMenu.classList.contains('hidden') && !langMenu.contains(event.target) && !langToggle.contains(event.target)) {
        closeLangMenu();
      }
    });
  }
});
