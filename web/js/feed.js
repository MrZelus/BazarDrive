
    const posts = [];

    const docs = [
      {
        id: 'platform-rules',
        title: 'Правила платформы',
        description: 'Основные требования к безопасности, коммуникации и публикациям.',
        tags: ['правила', 'безопасность', 'публикации'],
        type: 'Правило'
      },
      {
        id: 'pdd-moscow',
        title: 'ПДД Москвы',
        description: 'Актуальные правила дорожного движения в пределах Москвы.',
        tags: ['пдд', 'москва', 'дорога'],
        type: 'Документ'
      },
      {
        id: 'ip-usn',
        title: 'Правила ИП на УСН',
        description: 'УСН 6%, отчётность, сроки и важные нюансы для водителей-ИП.',
        tags: ['ип', 'усн', 'налоги', '6%'],
        type: 'Документ'
      },
      {
        id: 'tariffs',
        title: 'Тарифы',
        description: 'Тарифные планы, комиссии платформы и коэффициенты по зонам.',
        tags: ['тарифы', 'комиссия', 'цены'],
        type: 'Документ'
      },
      {
        id: 'post-template',
        title: 'Шаблон поста гостя',
        description: 'Готовая структура: тема, детали, контакт и время актуальности.',
        tags: ['шаблон', 'пост', 'пример'],
        type: 'Шаблон'
      }
    ];

    const ROLE_STORAGE_KEY = 'bazardrive_selected_role';
    const ACTIVE_TAB_STORAGE_KEY = 'bazardrive_active_tab';
    const PROFILE_STORAGE_KEY = 'bazardrive_profile';
    const FEED_API_BASE_STORAGE_KEY = 'bazardrive_feed_api_base';
    const PENDING_POST_DRAFT_STORAGE_KEY = 'bazardrive_pending_post_draft';

    function normalizeApiBase(url) {
      return String(url || '').trim().replace(/\/+$/, '');
    }

    function resolveFeedApiBase() {
      const url = new URL(window.location.href);
      const apiBaseFromQuery = normalizeApiBase(url.searchParams.get('apiBase'));
      if (apiBaseFromQuery) {
        localStorage.setItem(FEED_API_BASE_STORAGE_KEY, apiBaseFromQuery);
        return apiBaseFromQuery;
      }

      const apiBaseFromStorage = normalizeApiBase(localStorage.getItem(FEED_API_BASE_STORAGE_KEY));
      if (apiBaseFromStorage) {
        return apiBaseFromStorage;
      }

      if (window.location.port === '8001') {
        return normalizeApiBase(window.location.origin);
      }

      return normalizeApiBase(`${window.location.protocol}//${window.location.hostname || 'localhost'}:8001`);
    }

    const FEED_API_BASE = resolveFeedApiBase();

    const feedEl = document.getElementById('feed');
    const newPostInput = document.getElementById('newPostInput');
    const publishBtn = document.getElementById('publishBtn');
    const appNotification = document.getElementById('appNotification');
    let notificationTimer = null;

    const docsList = document.getElementById('docsList');
    const docsSearch = document.getElementById('docsSearch');
    const docsSearchStatus = document.getElementById('docsSearchStatus');

    const tabButtons = document.querySelectorAll('.tab-btn');
    const profileMenuButtons = document.querySelectorAll('.profile-menu-btn');
    const profileTabScreens = {
      overview: document.getElementById('profile-tab-overview'),
      taxi_ip: document.getElementById('profile-tab-taxi_ip'),
      documents: document.getElementById('profile-tab-documents'),
      payouts: document.getElementById('profile-tab-payouts'),
      security: document.getElementById('profile-tab-security')
    };
    const screens = {
      feed: document.getElementById('screen-feed'),
      rules: document.getElementById('screen-rules'),
      profile: document.getElementById('screen-profile')
    };
    const VALID_MAIN_TABS = Object.keys(screens);

    const roleButtons = document.querySelectorAll('.role-btn');
    const roleDriver = document.getElementById('role-driver');
    const roleCommon = document.getElementById('role-common');
    const driverOverviewDocuments = document.getElementById('driverOverviewDocuments');
    const driverAddDocumentBtn = document.getElementById('driverAddDocumentBtn');
    const openDriverDocumentsTabBtn = document.getElementById('openDriverDocumentsTabBtn');
    const profileNameInput = document.getElementById('profileName');
    const profileEmailInput = document.getElementById('profileEmail');
    const profilePhoneInput = document.getElementById('profilePhone');
    const profileAboutInput = document.getElementById('profileAbout');
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    const guestProfileStatus = document.getElementById('guestProfileStatus');
    const addDocumentBtn = document.getElementById('addDocumentBtn');
    const addDocumentForm = document.getElementById('addDocumentForm');
    const submitDocumentBtn = document.getElementById('submitDocumentBtn');
    const cancelDocumentBtn = document.getElementById('cancelDocumentBtn');
    const driverDocumentsList = document.getElementById('driverDocumentsList');
    const documentsApiAlert = document.getElementById('documentsApiAlert');
    const documentTypeInput = document.getElementById('documentType');
    const documentNumberInput = document.getElementById('documentNumber');
    const documentValidUntilInput = document.getElementById('documentValidUntil');
    const documentTypeError = document.getElementById('documentTypeError');
    const documentNumberError = document.getElementById('documentNumberError');
    const documentValidUntilError = document.getElementById('documentValidUntilError');
    let isSubmittingDocument = false;

    function storePendingPostDraft(text = '') {
      const normalized = String(text || '').trim();
      if (!normalized) {
        localStorage.removeItem(PENDING_POST_DRAFT_STORAGE_KEY);
        return;
      }
      localStorage.setItem(PENDING_POST_DRAFT_STORAGE_KEY, normalized);
    }

    function readPendingPostDraft() {
      return String(localStorage.getItem(PENDING_POST_DRAFT_STORAGE_KEY) || '').trim();
    }

    function consumePendingPostDraft() {
      const draft = readPendingPostDraft();
      localStorage.removeItem(PENDING_POST_DRAFT_STORAGE_KEY);
      return draft;
    }

    function showAppNotification(message = '', type = 'info') {
      if (!appNotification) return;
      const normalizedMessage = String(message || '').trim();
      if (!normalizedMessage) {
        appNotification.textContent = '';
        appNotification.classList.add('hidden');
        appNotification.classList.remove('app-notification--info', 'app-notification--success', 'app-notification--error');
        return;
      }

      const normalizedType = ['info', 'success', 'error'].includes(type) ? type : 'info';
      appNotification.textContent = normalizedMessage;
      appNotification.classList.remove('hidden');
      appNotification.classList.remove('app-notification--info', 'app-notification--success', 'app-notification--error');
      appNotification.classList.add(`app-notification--${normalizedType}`);

      if (notificationTimer) {
        window.clearTimeout(notificationTimer);
      }
      notificationTimer = window.setTimeout(() => {
        appNotification.classList.add('hidden');
      }, 4500);
    }

    function formatDocumentDate(dateValue) {
      const value = String(dateValue || '').trim();
      if (!value) return '—';
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleDateString('ru-RU');
    }

    function mapDocumentStatus(status) {
      const labels = {
        uploaded: 'Загружен',
        checking: 'На проверке',
        pending_verification: 'На проверке',
        approved: 'Подтверждён',
        verified: 'Подтверждён',
        rejected: 'Отклонён',
        expired: 'Истёк',
      };
      return labels[String(status || '').trim()] || 'Неизвестно';
    }

    function renderDriverOverviewDocuments(items = []) {
      if (!driverOverviewDocuments) return;
      if (!Array.isArray(items) || items.length === 0) {
        driverOverviewDocuments.innerHTML = '<div class="rounded-xl border border-white/10 bg-panelSoft px-3 py-2 text-sm text-textSoft">Добавьте документы для верификации профиля.</div>';
        return;
      }

      const previewItems = items.slice(0, 3);
      driverOverviewDocuments.innerHTML = previewItems.map((item) => `
        <div class="rounded-xl border border-white/10 bg-panelSoft px-3 py-2">
          <p class="text-sm font-medium">${item.title || item.type}</p>
          <p class="text-xs text-textSoft">Статус: ${item.statusLabel} • Обновлён: ${item.updatedAtLabel}</p>
        </div>
      `).join('');
    }


    function clearDocumentErrors() {
      [documentTypeError, documentNumberError, documentValidUntilError].forEach((el) => {
        if (!el) return;
        el.textContent = '';
        el.classList.add('hidden');
      });
    }

    function showDocumentErrors(errors = {}) {
      const fieldToElement = {
        type: documentTypeError,
        number: documentNumberError,
        valid_until: documentValidUntilError,
      };
      Object.entries(errors).forEach(([field, message]) => {
        const target = fieldToElement[field];
        if (!target) return;
        target.textContent = String(message || 'Некорректное значение');
        target.classList.remove('hidden');
      });
    }

    function setDocumentAlert(message = '') {
      if (!documentsApiAlert) return;
      const normalized = String(message || '').trim();
      if (!normalized) {
        documentsApiAlert.textContent = '';
        documentsApiAlert.classList.add('hidden');
        return;
      }
      documentsApiAlert.textContent = normalized;
      documentsApiAlert.classList.remove('hidden');
    }

    function applyDocumentLoadingState(isLoading) {
      isSubmittingDocument = Boolean(isLoading);
      if (submitDocumentBtn) {
        submitDocumentBtn.disabled = isSubmittingDocument;
        submitDocumentBtn.textContent = isSubmittingDocument ? 'Сохранение...' : 'Сохранить';
      }
      if (cancelDocumentBtn) {
        cancelDocumentBtn.disabled = isSubmittingDocument;
      }
      if (addDocumentBtn) {
        addDocumentBtn.disabled = isSubmittingDocument;
      }
      [documentTypeInput, documentNumberInput, documentValidUntilInput].forEach((field) => {
        if (!field) return;
        field.disabled = isSubmittingDocument;
      });
    }

    function renderDriverDocuments(items = []) {
      if (!driverDocumentsList) return;
      if (!Array.isArray(items) || items.length === 0) {
        driverDocumentsList.innerHTML = '<div class="rounded-xl border border-white/10 bg-panelSoft px-3 py-2 text-sm text-textSoft">Документы пока не добавлены.</div>';
        renderDriverOverviewDocuments([]);
        return;
      }

      const labels = {
        passport: 'Паспорт', inn: 'ИНН', ogrnip: 'ОГРНИП', taxi_license: 'Разрешение на такси',
        driver_license: 'Водительское удостоверение', sts: 'СТС', osago: 'ОСАГО',
        diagnostic_card: 'Диагностическая карта', self_employed_certificate: 'Справка самозанятого'
      };

      const normalizedItems = items.map((item) => ({
        ...item,
        title: labels[item.type] || item.type,
        statusLabel: mapDocumentStatus(item.status),
        updatedAtLabel: formatDocumentDate(item.updated_at),
        validUntilLabel: formatDocumentDate(item.valid_until),
      }));

      driverDocumentsList.innerHTML = normalizedItems.map((item) => `
        <article class="rounded-xl border border-white/10 bg-panelSoft px-3 py-3 space-y-2">
          <div class="flex items-start justify-between gap-3">
            <p class="text-sm font-medium">${item.title}</p>
            <button type="button" data-doc-delete="${item.id}" class="text-xs text-warning hover:underline">Удалить</button>
          </div>
          <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-3 gap-y-1 text-xs">
            <div>
              <dt class="text-textSoft">Номер</dt>
              <dd>${item.number || '—'}</dd>
            </div>
            <div>
              <dt class="text-textSoft">Статус</dt>
              <dd>${item.statusLabel}</dd>
            </div>
            <div>
              <dt class="text-textSoft">Срок действия</dt>
              <dd>${item.validUntilLabel}</dd>
            </div>
            <div>
              <dt class="text-textSoft">Обновлён</dt>
              <dd>${item.updatedAtLabel}</dd>
            </div>
          </dl>
        </article>
      `).join('');
      renderDriverOverviewDocuments(normalizedItems);

      driverDocumentsList.querySelectorAll('[data-doc-delete]').forEach((button) => {
        button.addEventListener('click', async () => {
          const id = Number(button.getAttribute('data-doc-delete'));
          if (!id) return;
          try {
            const response = await fetch(`${FEED_API_BASE}/api/driver/documents/${id}`, { method: 'DELETE' });
            if (!response.ok) {
              throw new Error(`Не удалось удалить документ (HTTP ${response.status})`);
            }
            await loadDriverDocuments();
          } catch (error) {
            console.error(error);
            setDocumentAlert(error.message || 'Не удалось удалить документ');
          }
        });
      });
    }

    async function loadDriverDocuments() {
      try {
        const response = await fetch(`${FEED_API_BASE}/api/driver/documents?profile_id=driver-main`);
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.error || `Не удалось загрузить документы (HTTP ${response.status})`);
        }
        renderDriverDocuments(payload.items || []);
      } catch (error) {
        console.error(error);
        renderDriverOverviewDocuments([]);
        setDocumentAlert(error.message || 'Не удалось загрузить список документов');
      }
    }

    function toggleDocumentForm(forceOpen) {
      if (!addDocumentForm) return;
      if (isSubmittingDocument) return;
      const shouldOpen = typeof forceOpen === 'boolean' ? forceOpen : addDocumentForm.classList.contains('hidden');
      addDocumentForm.classList.toggle('hidden', !shouldOpen);
      if (!shouldOpen) {
        addDocumentForm.reset();
        clearDocumentErrors();
        setDocumentAlert('');
      }
    }

    function validateDocumentForm() {
      const errors = {};
      const type = String(documentTypeInput?.value || '').trim();
      const number = String(documentNumberInput?.value || '').trim();
      const validUntil = String(documentValidUntilInput?.value || '').trim();

      if (!type) errors.type = 'Выберите тип документа';
      if (number.length < 3) errors.number = 'Укажите номер документа (минимум 3 символа)';
      if (validUntil && !/^\d{4}-\d{2}-\d{2}$/.test(validUntil)) {
        errors.valid_until = 'Дата должна быть в формате YYYY-MM-DD';
      }

      return {
        payload: {
          profile_id: 'driver-main',
          type,
          number,
          valid_until: validUntil || null,
          status: 'uploaded',
        },
        errors,
      };
    }

    async function submitDriverDocument(event) {
      event.preventDefault();
      clearDocumentErrors();
      setDocumentAlert('');

      const { payload, errors } = validateDocumentForm();
      if (Object.keys(errors).length > 0) {
        showDocumentErrors(errors);
        return;
      }

      applyDocumentLoadingState(true);

      try {
        const response = await fetch(`${FEED_API_BASE}/api/driver/documents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          if (data.error === 'validation_error' || response.status === 422) {
            showDocumentErrors(data.fields || {});
            return;
          }
          if (data.error === 'duplicate_document' || response.status === 409) {
            showDocumentErrors(data.fields || { number: 'Документ с таким номером уже существует' });
            setDocumentAlert(data.message || 'Документ с такими данными уже добавлен');
            return;
          }
          throw new Error(data.error || `Не удалось добавить документ (HTTP ${response.status})`);
        }

        toggleDocumentForm(false);
        await loadDriverDocuments();
      } catch (error) {
        console.error(error);
        setDocumentAlert(error.message || 'Не удалось добавить документ');
      } finally {
        applyDocumentLoadingState(false);
      }
    }

    function getStoredGuestProfile() {
      try {
        const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
        const parsed = raw ? JSON.parse(raw) : {};
        if (parsed && typeof parsed === 'object') return parsed;
      } catch (error) {
        console.warn('Не удалось прочитать профиль гостя', error);
      }
      return {};
    }

    function makeGuestProfilePayload() {
      const stored = getStoredGuestProfile();
      const fallbackName = String(stored.fullName || '').trim();
      const profileId = String(stored.id || `guest-${crypto.randomUUID()}`).trim();
      const fullName = String(profileNameInput?.value || fallbackName).trim();
      const email = String(profileEmailInput?.value || stored.email || '').trim();
      const phone = String(profilePhoneInput?.value || stored.phone || '').trim();
      const about = String(profileAboutInput?.value || stored.about || '').trim();

      return {
        id: profileId,
        role: 'guest_author',
        display_name: fullName,
        email: email || null,
        phone: phone || null,
        about: about || null,
        status: 'active',
        is_verified: false
      };
    }

    function isGuestProfileReady(profile) {
      const normalizedProfile = profile || {};
      const hasName = String(normalizedProfile.display_name || '').trim().length >= 2;
      const hasContact = Boolean(String(normalizedProfile.email || '').trim() || String(normalizedProfile.phone || '').trim());
      return hasName && hasContact;
    }
    
    function formatPostDate(createdAt) {
      const date = createdAt ? new Date(createdAt) : new Date();
      if (Number.isNaN(date.getTime())) {
        return 'только что';
      }

      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }

    function pickAvatar(author) {
      const seed = encodeURIComponent(author || 'guest');
      return `https://api.dicebear.com/8.x/initials/svg?seed=${seed}`;
    }

    function mapApiPost(item) {
      return {
        id: item.id,
        author: item.author || 'Гость',
        avatar: pickAvatar(item.author),
        publishedAt: formatPostDate(item.created_at),
        text: item.text || '',
        image: item.image_url || '',
        likes: Number(item.likes) || 0,
        comments: 0,
        reposts: 0,
        likedByMe: false,
      };
    }

    function interactionButton(icon, value, label) {
      return `
        <button type="button" aria-label="${label}" class="group inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-textSoft transition hover:bg-panelSoft hover:text-text">
          ${icon}
          <span>${value}</span>
        </button>
      `;
    }

    function renderFeed() {
      feedEl.innerHTML = posts.map((post) => `
        <article class="rounded-2xl bg-panel p-4 border border-white/10 animate-fadeInUp">
          <header class="mb-3 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <img src="${post.avatar}" alt="${post.author}" class="h-10 w-10 rounded-full object-cover" loading="lazy" />
              <div>
                <p class="text-sm font-semibold text-text">${post.author}</p>
                <p class="text-xs text-textSoft">${post.publishedAt}</p>
              </div>
            </div>
          </header>

          <p class="mb-3 text-[15px] leading-7 text-text">${post.text}</p>

          ${post.image ? `<img src="${post.image}" alt="Изображение поста" class="mb-3 max-h-[420px] w-full rounded-xl object-cover" loading="lazy" />` : ''}

          <footer class="flex items-center gap-1 border-t border-white/10 pt-2">
            ${interactionButton(
              '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21s-7-4.35-7-10a4 4 0 0 1 7-2.65A4 4 0 0 1 19 11c0 5.65-7 10-7 10Z"/></svg>',
              post.likes,
              'Лайк'
            ).replace('group inline-flex', `group inline-flex js-like-btn ${post.likedByMe ? 'text-accent' : ''}`).replace('aria-label="Лайк"', `aria-label="Лайк" data-post-id="${post.id}"`)}
            ${interactionButton(
              '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 10h8M8 14h5"/><path d="M21 12a8 8 0 0 1-8 8H5l2.1-2.8A8 8 0 1 1 21 12Z"/></svg>',
              post.comments,
              'Комментарий'
            )}
            ${interactionButton(
              '<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m4 12 7-7v4h6a3 3 0 0 1 3 3v7"/><path d="m20 12-7 7v-4H7a3 3 0 0 1-3-3V5"/></svg>',
              post.reposts,
              'Репост'
            )}
          </footer>
        </article>
      `).join('');

      feedEl.querySelectorAll('.js-like-btn').forEach((button) => {
        button.addEventListener('click', () => {
          const postId = Number(button.dataset.postId);
          const target = posts.find((post) => post.id === postId);
          if (!target) return;
          target.likedByMe = !target.likedByMe;
          target.likes += target.likedByMe ? 1 : -1;
          renderFeed();
        });
      });
    }

    async function loadPosts() {
      try {
        const response = await fetch(`${FEED_API_BASE}/api/feed/posts?limit=50&offset=0`);
        if (!response.ok) {
          throw new Error(`Не удалось загрузить ленту (HTTP ${response.status})`);
        }

        const payload = await response.json();
        const items = Array.isArray(payload.items) ? payload.items : [];
        posts.splice(0, posts.length, ...items.map(mapApiPost));
        renderFeed();
      } catch (error) {
        console.error(error);
        feedEl.innerHTML = `<div class="rounded-2xl bg-panel p-4 border border-white/10 text-sm text-warning">Не удалось загрузить посты. Проверьте доступность API: ${FEED_API_BASE}.</div>`;
      }
    }

    function resolveAuthorName() {
      try {
        const profile = getStoredGuestProfile();
        const fullName = String(profile?.fullName || '').trim();
        if (fullName.length >= 2) return fullName;
      } catch (error) {
        console.warn('Не удалось прочитать профиль пользователя', error);
      }
      return 'Гость';
    }

    async function addNewPost() {
      const text = String(newPostInput?.value || '').trim();
      if (!text) return;
      
      const author = resolveAuthorName();
      const guestProfile = makeGuestProfilePayload();
      if (author === 'Гость' || !isGuestProfileReady(guestProfile)) {
        storePendingPostDraft(text);
        setActiveScreen('profile');
        setActiveProfileTab('documents');
        showAppNotification('Для публикации заполните профиль гостя: имя и хотя бы email или телефон. После сохранения публикация продолжится автоматически.', 'info');
        return;
      }

      storePendingPostDraft('');
      publishBtn.disabled = true;
      publishBtn.textContent = 'Публикация...';
      try {
        const response = await fetch(`${FEED_API_BASE}/api/feed/posts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ author, text, guest_profile: guestProfile }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          if (response.status === 429) {
            const retryAfterRaw = payload.retry_after ?? response.headers.get('Retry-After');
            const retryAfterSeconds = Number(retryAfterRaw) || 0;
            const retryAfterMessage = retryAfterSeconds > 0
              ? `Повторите через ${retryAfterSeconds} сек.`
              : 'Повторите попытку позже.';
            throw new Error(`Слишком много публикаций за короткое время. ${retryAfterMessage}`);
          }
          throw new Error(payload.error || `Ошибка публикации (HTTP ${response.status})`);
        }
        newPostInput.value = '';
        storePendingPostDraft('');
        await loadPosts();
      } catch (error) {
        console.error(error);
        showAppNotification(error.message || 'Не удалось опубликовать пост', 'error');
      } finally {
        publishBtn.disabled = false;
        publishBtn.textContent = 'Опубликовать';
      }
    }

    function renderDocs(query = '') {
      const normalized = query.trim().toLowerCase();
      const shouldFilter = normalized.length >= 2;
      const filteredDocs = docs.filter((doc) => {
        if (!shouldFilter) return true;
        const haystack = `${doc.title} ${doc.description} ${doc.tags.join(' ')}`.toLowerCase();
        return haystack.includes(normalized);
      });

      docsList.innerHTML = filteredDocs.length
        ? filteredDocs.map((doc) => `
            <article class="rounded-2xl bg-panel p-4 border border-white/10 animate-fadeInUp">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <h3 class="text-base font-semibold">${doc.title}</h3>
                  <p class="text-sm text-textSoft mt-1">${doc.description}</p>
                </div>
                <span class="text-[10px] uppercase tracking-wide rounded-full bg-panelSoft text-textSoft px-2 py-1">${doc.type || 'Документ'}</span>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                ${doc.tags.map((tag) => `<span class="rounded-full bg-panelSoft px-2.5 py-1 text-xs text-textSoft">#${tag}</span>`).join('')}
              </div>
            </article>
          `).join('')
        : '<div class="rounded-2xl bg-panel p-4 border border-white/10 text-sm text-textSoft">Ничего не найдено. Попробуйте другой запрос.</div>';

      if (docsSearchStatus) {
        if (!normalized) {
          docsSearchStatus.textContent = `Показаны все материалы: ${docs.length}.`;
        } else if (!shouldFilter) {
          docsSearchStatus.textContent = `Введите ещё ${2 - normalized.length} символ(а), сейчас показаны все материалы: ${docs.length}.`;
        } else if (!filteredDocs.length) {
          docsSearchStatus.textContent = 'По вашему запросу ничего не найдено.';
        } else {
          docsSearchStatus.textContent = `Найдено материалов: ${filteredDocs.length}.`;
        }
      }
    }

    function setActiveScreen(tab) {
      const normalizedTab = VALID_MAIN_TABS.includes(tab) ? tab : 'feed';

      tabButtons.forEach((btn) => {
        const isActive = btn.dataset.tab === normalizedTab;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', String(isActive));
        btn.tabIndex = isActive ? 0 : -1;
      });

      Object.entries(screens).forEach(([name, screen]) => {
        const isActive = name === normalizedTab;
        screen.classList.toggle('active', isActive);
        screen.classList.toggle('animate-fadeInUp', isActive);
        screen.toggleAttribute('hidden', !isActive);
        screen.setAttribute('aria-hidden', String(!isActive));
        screen.toggleAttribute('inert', !isActive);
      });

      localStorage.setItem(ACTIVE_TAB_STORAGE_KEY, normalizedTab);

      if (normalizedTab === 'profile') {
        updateGuestProfileStatus();
      }
    }

    function handleMainTabsKeydown(event) {
      const navigationKeys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];
      if (!navigationKeys.includes(event.key)) {
        return;
      }

      const currentIndex = Array.from(tabButtons).findIndex((btn) => btn === event.currentTarget);
      if (currentIndex === -1) return;

      event.preventDefault();

      let nextIndex = currentIndex;
      if (event.key === 'ArrowRight') {
        nextIndex = (currentIndex + 1) % tabButtons.length;
      } else if (event.key === 'ArrowLeft') {
        nextIndex = (currentIndex - 1 + tabButtons.length) % tabButtons.length;
      } else if (event.key === 'Home') {
        nextIndex = 0;
      } else if (event.key === 'End') {
        nextIndex = tabButtons.length - 1;
      }

      const nextButton = tabButtons[nextIndex];
      nextButton.focus();
      setActiveScreen(nextButton.dataset.tab);
    }

    function setActiveProfileTab(tab) {
      profileMenuButtons.forEach((btn) => {
        const isActive = btn.dataset.profileTab === tab;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', String(isActive));
        btn.tabIndex = isActive ? 0 : -1;
      });
      Object.entries(profileTabScreens).forEach(([name, screen]) => {
        const isActive = name === tab;
        screen.classList.toggle('hidden', !isActive);
        screen.toggleAttribute('hidden', !isActive);
        screen.setAttribute('aria-hidden', String(!isActive));
        screen.toggleAttribute('inert', !isActive);
      });
      if (tab === 'documents') {
        loadDriverDocuments();
      }
    }

    function setRole(role) {
      roleButtons.forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.role === role);
      });

      if (role === 'driver') {
        roleDriver.classList.remove('hidden');
        roleCommon.classList.add('hidden');
        loadDriverDocuments();
      } else {
        roleDriver.classList.add('hidden');
        roleCommon.classList.remove('hidden');
      }

      localStorage.setItem(ROLE_STORAGE_KEY, role);
    }

    async function saveGuestProfile() {
      const profile = makeGuestProfilePayload();
      if (profile.display_name.length < 2) {
        showAppNotification('Имя должно содержать минимум 2 символа.', 'error');
        return;
      }
      if (!profile.email && !profile.phone) {
        showAppNotification('Укажите email или телефон.', 'error');
        return;
      }

      saveProfileBtn.disabled = true;
      saveProfileBtn.textContent = 'Сохранение...';
      try {
        const response = await fetch(`${FEED_API_BASE}/api/feed/profiles`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(profile),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.error || `Ошибка сохранения профиля (HTTP ${response.status})`);
        }

        const localProfile = {
          id: payload.id || profile.id,
          fullName: payload.display_name || profile.display_name,
          email: payload.email || profile.email || '',
          phone: payload.phone || profile.phone || '',
          about: payload.about || profile.about || '',
        };
        localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(localProfile));
        updateGuestProfileStatus();
        const pendingDraft = consumePendingPostDraft();
        if (pendingDraft) {
          if (newPostInput) {
            newPostInput.value = pendingDraft;
          }
          setActiveScreen('feed');
          await addNewPost();
          return;
        }
        showAppNotification('Профиль гостя сохранён.', 'success');
      } catch (error) {
        console.error(error);
        showAppNotification(error.message || 'Не удалось сохранить профиль гостя', 'error');
      } finally {
        saveProfileBtn.disabled = false;
        saveProfileBtn.textContent = 'Сохранить профиль гостя';
      }
    }

    function hydrateProfileForm() {
      const profile = getStoredGuestProfile();
      if (profileNameInput) profileNameInput.value = String(profile.fullName || '');
      if (profileEmailInput) profileEmailInput.value = String(profile.email || '');
      if (profilePhoneInput) profilePhoneInput.value = String(profile.phone || '');
      if (profileAboutInput) profileAboutInput.value = String(profile.about || '');
    }

    function updateGuestProfileStatus() {
      if (!guestProfileStatus) return;
      const profile = makeGuestProfilePayload();
      const hasName = profile.display_name.length >= 2;
      const hasContact = Boolean(profile.email || profile.phone);

      if (hasName && hasContact) {
        guestProfileStatus.textContent = 'Профиль готов к публикации постов ✅';
        guestProfileStatus.classList.remove('text-warning');
        guestProfileStatus.classList.add('text-success');
      } else {
        guestProfileStatus.textContent = 'Заполните имя и хотя бы один контакт (email или телефон).';
        guestProfileStatus.classList.remove('text-success');
        guestProfileStatus.classList.add('text-warning');
      }
    }

    tabButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        setActiveScreen(btn.dataset.tab);
      });
      btn.addEventListener('keydown', handleMainTabsKeydown);
    });
    profileMenuButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        setActiveProfileTab(btn.dataset.profileTab);
      });
    });

    roleButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        setRole(btn.dataset.role);
      });
    });

    publishBtn.addEventListener('click', addNewPost);
    newPostInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        addNewPost();
      }
    });

    docsSearch.addEventListener('input', (event) => {
      renderDocs(event.target.value);
    });
    saveProfileBtn.addEventListener('click', saveGuestProfile);
    addDocumentBtn?.addEventListener('click', () => toggleDocumentForm(true));
    driverAddDocumentBtn?.addEventListener('click', () => {
      setActiveProfileTab('documents');
      toggleDocumentForm(true);
    });
    openDriverDocumentsTabBtn?.addEventListener('click', () => {
      setActiveProfileTab('documents');
    });
    cancelDocumentBtn?.addEventListener('click', () => toggleDocumentForm(false));
    addDocumentForm?.addEventListener('submit', submitDriverDocument);
    addDocumentForm?.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && isSubmittingDocument) {
        event.preventDefault();
      }
    });
    [profileNameInput, profileEmailInput, profilePhoneInput, profileAboutInput].forEach((field) => {
      field.addEventListener('input', updateGuestProfileStatus);
    });

    const savedRole = localStorage.getItem(ROLE_STORAGE_KEY);
    const savedActiveTab = localStorage.getItem(ACTIVE_TAB_STORAGE_KEY);
    const initialRole = ['driver', 'passenger', 'guest'].includes(savedRole) ? savedRole : 'driver';
    const initialTab = VALID_MAIN_TABS.includes(savedActiveTab) ? savedActiveTab : 'feed';

    loadPosts();
    renderDocs();
    loadDriverDocuments();
    hydrateProfileForm();
    setRole(initialRole);
    setActiveProfileTab('overview');
    setActiveScreen(initialTab);
    updateGuestProfileStatus();
