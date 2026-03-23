
    const posts = [];
    const postIds = new Set();
    const FEED_PAGE_SIZE = 20;
    let feedNextCursor = null;
    let feedHasMore = true;
    let feedIsLoading = false;
    let feedObserver = null;

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
    const feedLoadStateEl = document.createElement('div');
    feedLoadStateEl.id = 'feedLoadState';
    feedLoadStateEl.className = 'space-y-2';
    const feedSentinelEl = document.createElement('div');
    feedSentinelEl.id = 'feedLoadSentinel';
    feedSentinelEl.className = 'h-1 w-full';
    if (feedEl && feedEl.parentElement) {
      feedEl.parentElement.append(feedLoadStateEl, feedSentinelEl);
    }
    const newPostInput = document.getElementById('newPostInput');
    const publishBtn = document.getElementById('publishBtn');
    const publishPrecheckHint = document.getElementById('publishPrecheckHint');
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
    const MODERATION_ERROR_COPY = {
      prohibited: 'Публикация отклонена модерацией: обнаружена запрещённая тема.',
      links: 'Публикация отклонена: в одном посте можно указать не более 2 ссылок.',
      spam: 'Публикация отклонена: текст похож на спам из повторяющихся слов.',
      too_short: 'Текст слишком короткий: напишите минимум 5 символов.',
      generic: 'Публикация отклонена правилами модерации. Исправьте текст и попробуйте снова.',
    };

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

    function resolveModerationErrorMessage(rawMessage = '') {
      const source = String(rawMessage || '').trim();
      if (!source) return MODERATION_ERROR_COPY.generic;
      const normalized = source.toLowerCase();
      if (
        normalized.includes('азарт') ||
        normalized.includes('наркот') ||
        normalized.includes('ставк') ||
        normalized.includes('18+')
      ) {
        return MODERATION_ERROR_COPY.prohibited;
      }
      if (normalized.includes('слишком много ссылок')) return MODERATION_ERROR_COPY.links;
      if (normalized.includes('спам')) return MODERATION_ERROR_COPY.spam;
      if (normalized.includes('минимум 5 символ')) return MODERATION_ERROR_COPY.too_short;
      if (normalized.includes('правила')) return MODERATION_ERROR_COPY.generic;
      return source;
    }

    function getPublishPrecheckState(textValue = '') {
      const text = String(textValue || '').trim();
      if (!text) {
        return { type: 'neutral', message: 'Пре‑проверка: минимум 5 символов, без спама и запрещённых тем.' };
      }
      if (text.length < 5) return { type: 'warning', message: MODERATION_ERROR_COPY.too_short };

      const lowered = text.toLowerCase();
      const linksCount = (lowered.match(/https?:\/\//g) || []).length;
      if (linksCount > 2) return { type: 'warning', message: MODERATION_ERROR_COPY.links };

      if (lowered.includes('казино') || lowered.includes('наркот') || lowered.includes('ставк') || lowered.includes('18+')) {
        return { type: 'warning', message: MODERATION_ERROR_COPY.prohibited };
      }

      const tokens = lowered.split(/\s+/).filter((token) => token.length >= 3);
      if (tokens.length) {
        const frequencies = {};
        tokens.forEach((token) => {
          frequencies[token] = (frequencies[token] || 0) + 1;
        });
        if (Math.max(...Object.values(frequencies)) > 4) {
          return { type: 'warning', message: MODERATION_ERROR_COPY.spam };
        }
      }
      return { type: 'ok', message: 'Пре‑проверка пройдена: можно отправлять публикацию.' };
    }

    function applyPublishPrecheckHint(state) {
      if (!publishPrecheckHint) return;
      const normalized = state || getPublishPrecheckState(String(newPostInput?.value || ''));
      publishPrecheckHint.textContent = normalized.message;
      publishPrecheckHint.classList.remove('text-textSoft', 'text-warning', 'text-accent');
      if (normalized.type === 'warning') {
        publishPrecheckHint.classList.add('text-warning');
      } else if (normalized.type === 'ok') {
        publishPrecheckHint.classList.add('text-accent');
      } else {
        publishPrecheckHint.classList.add('text-textSoft');
      }
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

    function clearChildren(element) {
      if (!element) return;
      while (element.firstChild) {
        element.removeChild(element.firstChild);
      }
    }

    function buildInfoCard(message) {
      const card = document.createElement('div');
      card.className = 'rounded-xl border border-white/10 bg-panelSoft px-3 py-2 text-sm text-textSoft';
      card.textContent = String(message || '').trim();
      return card;
    }

    function renderDriverOverviewDocuments(items = []) {
      if (!driverOverviewDocuments) return;
      clearChildren(driverOverviewDocuments);
      if (!Array.isArray(items) || items.length === 0) {
        driverOverviewDocuments.appendChild(buildInfoCard('Добавьте документы для верификации профиля.'));
        return;
      }

      const previewItems = items.slice(0, 3);
      previewItems.forEach((item) => {
        const card = document.createElement('div');
        card.className = 'rounded-xl border border-white/10 bg-panelSoft px-3 py-2';

        const title = document.createElement('p');
        title.className = 'text-sm font-medium';
        title.textContent = String(item.title || item.type || 'Документ');

        const meta = document.createElement('p');
        meta.className = 'text-xs text-textSoft';
        meta.textContent = `Статус: ${item.statusLabel} • Обновлён: ${item.updatedAtLabel}`;

        card.append(title, meta);
        driverOverviewDocuments.appendChild(card);
      });
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
      clearChildren(driverDocumentsList);
      if (!Array.isArray(items) || items.length === 0) {
        driverDocumentsList.appendChild(buildInfoCard('Документы пока не добавлены.'));
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

      normalizedItems.forEach((item) => {
        const article = document.createElement('article');
        article.className = 'rounded-xl border border-white/10 bg-panelSoft px-3 py-3 space-y-2';

        const header = document.createElement('div');
        header.className = 'flex items-start justify-between gap-3';

        const title = document.createElement('p');
        title.className = 'text-sm font-medium';
        title.textContent = String(item.title || 'Документ');

        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.className = 'text-xs text-warning hover:underline';
        deleteButton.dataset.docDelete = String(item.id || '');
        deleteButton.textContent = 'Удалить';
        deleteButton.addEventListener('click', async () => {
          const id = Number(deleteButton.dataset.docDelete);
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

        header.append(title, deleteButton);

        const metaGrid = document.createElement('dl');
        metaGrid.className = 'grid grid-cols-1 sm:grid-cols-2 gap-x-3 gap-y-1 text-xs';

        const entries = [
          ['Номер', item.number || '—'],
          ['Статус', item.statusLabel],
          ['Срок действия', item.validUntilLabel],
          ['Обновлён', item.updatedAtLabel],
        ];

        entries.forEach(([label, value]) => {
          const wrapper = document.createElement('div');
          const dt = document.createElement('dt');
          dt.className = 'text-textSoft';
          dt.textContent = label;
          const dd = document.createElement('dd');
          dd.textContent = String(value || '—');
          wrapper.append(dt, dd);
          metaGrid.appendChild(wrapper);
        });

        article.append(header, metaGrid);
        driverDocumentsList.appendChild(article);
      });
      renderDriverOverviewDocuments(normalizedItems);
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
      const reactions = (item && typeof item.reactions === 'object' && item.reactions !== null) ? item.reactions : {};
      const myReaction = String(item.my_reaction || '').trim() || null;
      const media = Array.isArray(item.media) ? item.media : [];
      const normalizedMedia = media
        .map((entry, index) => ({
          mediaType: String(entry?.media_type || 'image').trim().toLowerCase() || 'image',
          url: String(entry?.url || '').trim(),
          position: Number.isFinite(Number(entry?.position)) ? Number(entry.position) : index,
        }))
        .filter((entry) => entry.url)
        .sort((a, b) => a.position - b.position);
      const legacyImage = String(item.image_url || '').trim();
      if (!normalizedMedia.length && legacyImage) {
        normalizedMedia.push({ mediaType: 'image', url: legacyImage, position: 0 });
      }
      return {
        id: item.id,
        author: item.author || 'Гость',
        guestProfileId: String(item.guest_profile_id || '').trim(),
        avatar: pickAvatar(item.author),
        publishedAt: formatPostDate(item.created_at),
        text: item.text || '',
        image: item.image_url || '',
        media: normalizedMedia,
        reactions,
        myReaction,
        likes: Number(item.likes ?? reactions.like) || 0,
        comments: [],
        reposts: 0,
        likedByMe: myReaction === 'like',
      };
    }

    function mapApiComment(item) {
      return {
        id: Number(item.id) || 0,
        postId: Number(item.post_id) || 0,
        guestProfileId: String(item.guest_profile_id || '').trim(),
        author: String(item.author || 'Гость'),
        text: String(item.text || '').trim(),
        createdAt: formatPostDate(item.created_at),
      };
    }

    function getCurrentGuestActor() {
      const profile = getStoredGuestProfile();
      return {
        id: String(profile?.id || '').trim(),
        fullName: String(profile?.fullName || '').trim() || 'Гость',
      };
    }

    function canDeletePost(post, actorId) {
      return Boolean(actorId && String(post?.guestProfileId || '').trim() === actorId);
    }

    async function deletePost(postId, actorId) {
      const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${postId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_profile_id: actorId }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `Не удалось удалить пост (HTTP ${response.status})`);
      }
    }


    function applyReactionPayload(post, payload) {
      if (!post || !payload || typeof payload !== 'object') return;
      const reactions = (typeof payload.reactions === 'object' && payload.reactions !== null) ? payload.reactions : {};
      post.reactions = reactions;
      post.myReaction = String(payload.my_reaction || '').trim() || null;
      post.likes = Number(payload.likes ?? reactions.like) || 0;
      post.likedByMe = post.myReaction === 'like';
    }

    async function setPostReaction(postId, actorId, reactionType) {
      const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${postId}/react`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_profile_id: actorId, type: reactionType }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `Не удалось установить реакцию (HTTP ${response.status})`);
      }
      return payload;
    }

    async function deletePostReaction(postId, actorId) {
      const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${postId}/react`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_profile_id: actorId }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `Не удалось снять реакцию (HTTP ${response.status})`);
      }
      return payload;
    }

    function createInteractionButton(iconText, value, label, extraClasses = '') {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', String(label || '').trim());
      button.className = `group inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-textSoft transition hover:bg-panelSoft hover:text-text ${extraClasses}`.trim();

      const icon = document.createElement('span');
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = iconText;

      const counter = document.createElement('span');
      counter.textContent = String(value || 0);

      button.append(icon, counter);
      return button;
    }

    function renderFeed() {
      clearChildren(feedEl);
      posts.forEach((post) => {
        const actor = getCurrentGuestActor();
        const article = document.createElement('article');
        article.className = 'rounded-2xl bg-panel p-4 border border-white/10 animate-fadeInUp';

        const header = document.createElement('header');
        header.className = 'mb-3 flex items-center justify-between';
        const headerRow = document.createElement('div');
        headerRow.className = 'flex items-center gap-3';

        const avatar = document.createElement('img');
        avatar.src = String(post.avatar || '');
        avatar.alt = String(post.author || 'Гость');
        avatar.className = 'h-10 w-10 rounded-full object-cover';
        avatar.loading = 'lazy';

        const meta = document.createElement('div');
        const author = document.createElement('p');
        author.className = 'text-sm font-semibold text-text';
        author.textContent = String(post.author || 'Гость');
        const publishedAt = document.createElement('p');
        publishedAt.className = 'text-xs text-textSoft';
        publishedAt.textContent = String(post.publishedAt || 'только что');
        meta.append(author, publishedAt);
        headerRow.append(avatar, meta);
        header.appendChild(headerRow);

        if (canDeletePost(post, actor.id)) {
          const deletePostBtn = document.createElement('button');
          deletePostBtn.type = 'button';
          deletePostBtn.className = 'text-xs text-warning hover:underline';
          deletePostBtn.textContent = 'Удалить';
          deletePostBtn.addEventListener('click', async () => {
            deletePostBtn.disabled = true;
            try {
              await deletePost(post.id, actor.id);
              await loadPosts({ reset: true });
              showAppNotification('Пост удалён.', 'success');
            } catch (error) {
              console.error(error);
              showAppNotification(error.message || 'Не удалось удалить пост.', 'error');
            } finally {
              deletePostBtn.disabled = false;
            }
          });
          header.appendChild(deletePostBtn);
        }

        const body = document.createElement('p');
        body.className = 'mb-3 text-[15px] leading-7 text-text';
        body.textContent = String(post.text || '');

        article.append(header, body);

        if (Array.isArray(post.media) && post.media.length) {
          const mediaContainer = document.createElement('div');
          mediaContainer.className = 'mb-3 flex snap-x snap-mandatory gap-2 overflow-x-auto';

          post.media.forEach((item, index) => {
            const type = String(item.mediaType || 'image').toLowerCase();
            if (type === 'video') {
              const video = document.createElement('video');
              video.src = String(item.url || '');
              video.controls = true;
              video.preload = 'metadata';
              video.className = 'max-h-[420px] min-w-full snap-center rounded-xl bg-black object-contain';
              mediaContainer.appendChild(video);
              return;
            }
            const image = document.createElement('img');
            image.src = String(item.url || '');
            image.alt = `Изображение поста ${index + 1}`;
            image.className = 'max-h-[420px] min-w-full snap-center rounded-xl object-cover';
            image.loading = 'lazy';
            mediaContainer.appendChild(image);
          });
          article.appendChild(mediaContainer);
        } else if (post.image) {
          const image = document.createElement('img');
          image.src = String(post.image);
          image.alt = 'Изображение поста';
          image.className = 'mb-3 max-h-[420px] w-full rounded-xl object-cover';
          image.loading = 'lazy';
          article.appendChild(image);
        }

        const footer = document.createElement('footer');
        footer.className = 'flex items-center gap-1 border-t border-white/10 pt-2';

        const likeButton = createInteractionButton('♡', post.likes, 'Лайк', `js-like-btn ${post.likedByMe ? 'text-accent' : ''}`);
        likeButton.dataset.postId = String(post.id || '');
        likeButton.addEventListener('click', async () => {
          const postId = Number(likeButton.dataset.postId);
          const target = posts.find((currentPost) => currentPost.id === postId);
          if (!target) return;
          if (!actor.id) {
            showAppNotification('Сначала заполните и сохраните профиль гостя.', 'error');
            return;
          }
          likeButton.disabled = true;
          try {
            const payload = target.myReaction === 'like'
              ? await deletePostReaction(postId, actor.id)
              : await setPostReaction(postId, actor.id, 'like');
            applyReactionPayload(target, payload);
            renderFeed();
          } catch (error) {
            console.error(error);
            showAppNotification(error.message || 'Не удалось обновить реакцию.', 'error');
          } finally {
            likeButton.disabled = false;
          }
        });

        footer.append(
          likeButton,
          createInteractionButton('💬', Array.isArray(post.comments) ? post.comments.length : 0, 'Комментарий'),
          createInteractionButton('↻', post.reposts, 'Репост'),
        );
        article.appendChild(footer);

        const commentsWrap = document.createElement('section');
        commentsWrap.className = 'mt-3 border-t border-white/10 pt-3 space-y-2';

        const commentsTitle = document.createElement('p');
        commentsTitle.className = 'text-xs uppercase tracking-wide text-textSoft';
        commentsTitle.textContent = `Комментарии (${Array.isArray(post.comments) ? post.comments.length : 0})`;
        commentsWrap.appendChild(commentsTitle);

        const commentList = document.createElement('div');
        commentList.className = 'space-y-2';
        (post.comments || []).forEach((comment) => {
          const row = document.createElement('div');
          row.className = 'rounded-lg border border-white/10 bg-panelSoft px-3 py-2';

          const top = document.createElement('div');
          top.className = 'mb-1 flex items-center justify-between gap-2';

          const meta = document.createElement('span');
          meta.className = 'text-xs text-textSoft';
          meta.textContent = `${comment.author} • ${comment.createdAt}`;
          top.appendChild(meta);

          if (actor.id && comment.guestProfileId === actor.id) {
            const controls = document.createElement('div');
            controls.className = 'inline-flex items-center gap-2';
            const editBtn = document.createElement('button');
            editBtn.type = 'button';
            editBtn.className = 'text-xs text-accent hover:underline';
            editBtn.textContent = 'Редактировать';
            editBtn.addEventListener('click', async () => {
              const nextText = window.prompt('Изменить комментарий', comment.text);
              if (nextText === null) return;
              const cleaned = String(nextText || '').trim();
              if (!cleaned) {
                showAppNotification('Текст комментария не должен быть пустым.', 'error');
                return;
              }
              try {
                const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${post.id}/comments/${comment.id}`, {
                  method: 'PATCH',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ guest_profile_id: actor.id, text: cleaned }),
                });
                const payload = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(payload.error || `Не удалось обновить комментарий (HTTP ${response.status})`);
                await loadCommentsForPost(post);
                renderFeed();
                showAppNotification('Комментарий обновлён.', 'success');
              } catch (error) {
                console.error(error);
                showAppNotification(error.message || 'Не удалось обновить комментарий.', 'error');
              }
            });
            const deleteBtn = document.createElement('button');
            deleteBtn.type = 'button';
            deleteBtn.className = 'text-xs text-warning hover:underline';
            deleteBtn.textContent = 'Удалить';
            deleteBtn.addEventListener('click', async () => {
              try {
                const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${post.id}/comments/${comment.id}`, {
                  method: 'DELETE',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ guest_profile_id: actor.id }),
                });
                const payload = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(payload.error || `Не удалось удалить комментарий (HTTP ${response.status})`);
                await loadCommentsForPost(post);
                renderFeed();
                showAppNotification('Комментарий удалён.', 'success');
              } catch (error) {
                console.error(error);
                showAppNotification(error.message || 'Не удалось удалить комментарий.', 'error');
              }
            });
            controls.append(editBtn, deleteBtn);
            top.appendChild(controls);
          }

          const text = document.createElement('p');
          text.className = 'text-sm text-text';
          text.textContent = comment.text;
          row.append(top, text);
          commentList.appendChild(row);
        });
        commentsWrap.appendChild(commentList);

        const form = document.createElement('form');
        form.className = 'flex gap-2 pt-1';
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'Напишите комментарий...';
        input.className = 'min-w-0 flex-1 rounded-lg border border-white/15 bg-panel px-3 py-2 text-sm text-text outline-none focus:border-accent';
        const submit = document.createElement('button');
        submit.type = 'submit';
        submit.className = 'rounded-lg bg-accent px-3 py-2 text-xs font-semibold text-black hover:opacity-90';
        submit.textContent = 'Отправить';
        form.append(input, submit);
        form.addEventListener('submit', async (event) => {
          event.preventDefault();
          const text = String(input.value || '').trim();
          if (!text) {
            showAppNotification('Введите текст комментария.', 'error');
            return;
          }
          if (!actor.id) {
            showAppNotification('Сначала заполните и сохраните профиль гостя.', 'error');
            return;
          }
          submit.disabled = true;
          try {
            const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${post.id}/comments`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ guest_profile_id: actor.id, author: actor.fullName, text }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(payload.error || `Не удалось добавить комментарий (HTTP ${response.status})`);
            input.value = '';
            await loadCommentsForPost(post);
            renderFeed();
            showAppNotification('Комментарий добавлен.', 'success');
          } catch (error) {
            console.error(error);
            showAppNotification(error.message || 'Не удалось добавить комментарий.', 'error');
          } finally {
            submit.disabled = false;
          }
        });
        commentsWrap.appendChild(form);
        article.appendChild(commentsWrap);
        feedEl.appendChild(article);
      });
    }

    async function loadCommentsForPost(post) {
      if (!post || !post.id) return;
      const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${post.id}/comments?limit=100&offset=0`);
      if (!response.ok) throw new Error(`Не удалось загрузить комментарии (HTTP ${response.status})`);
      const payload = await response.json().catch(() => ({}));
      const items = Array.isArray(payload.items) ? payload.items : [];
      post.comments = items.map(mapApiComment);
    }

    function setFeedLoadingSkeleton(isVisible) {
      if (!feedLoadStateEl) return;
      clearChildren(feedLoadStateEl);
      if (!isVisible) return;
      for (let idx = 0; idx < 2; idx += 1) {
        const skeleton = document.createElement('div');
        skeleton.className = 'rounded-2xl border border-white/10 bg-panel p-4 animate-pulse';
        const line1 = document.createElement('div');
        line1.className = 'mb-2 h-3 w-1/3 rounded bg-panelSoft';
        const line2 = document.createElement('div');
        line2.className = 'h-3 w-2/3 rounded bg-panelSoft';
        skeleton.append(line1, line2);
        feedLoadStateEl.appendChild(skeleton);
      }
    }

    function setFeedError(message = '') {
      if (!feedLoadStateEl) return;
      clearChildren(feedLoadStateEl);
      const normalized = String(message || '').trim();
      if (!normalized) return;
      const warning = document.createElement('div');
      warning.className = 'rounded-2xl bg-panel p-4 border border-white/10 text-sm text-warning';
      warning.textContent = normalized;
      feedLoadStateEl.appendChild(warning);
    }

    function stopFeedInfiniteScroll() {
      if (feedObserver) {
        feedObserver.disconnect();
      }
    }

    function ensureFeedInfiniteScroll() {
      if (!feedSentinelEl || feedObserver || !window.IntersectionObserver) return;
      feedObserver = new IntersectionObserver((entries) => {
        const [entry] = entries;
        if (!entry?.isIntersecting || !feedHasMore || feedIsLoading) return;
        loadPosts();
      }, { rootMargin: '0px 0px 320px 0px' });
      feedObserver.observe(feedSentinelEl);
    }

    async function loadPosts({ reset = false } = {}) {
      if (feedIsLoading) return;
      if (!reset && !feedHasMore) return;
      feedIsLoading = true;
      if (reset) {
        feedNextCursor = null;
        feedHasMore = true;
        postIds.clear();
        posts.splice(0, posts.length);
        renderFeed();
      }
      setFeedError('');
      setFeedLoadingSkeleton(true);
      try {
        const actor = getCurrentGuestActor();
        const params = new URLSearchParams();
        params.set('limit', String(FEED_PAGE_SIZE));
        if (feedNextCursor) {
          params.set('cursor', feedNextCursor);
        } else {
          params.set('offset', '0');
        }
        if (actor.id) {
          params.set('guest_profile_id', actor.id);
        }
        const query = `?${params.toString()}`;
        const response = await fetch(`${FEED_API_BASE}/api/feed/posts${query}`);
        if (!response.ok) {
          throw new Error(`Не удалось загрузить ленту (HTTP ${response.status})`);
        }

        const payload = await response.json();
        const items = Array.isArray(payload.items) ? payload.items : [];
        const mapped = items.map(mapApiPost);
        const freshPosts = mapped.filter((post) => {
          const postId = Number(post.id) || 0;
          if (postIds.has(postId)) return false;
          postIds.add(postId);
          return true;
        });
        posts.push(...freshPosts);
        feedNextCursor = String(payload.next_cursor || '').trim() || null;
        feedHasMore = Boolean(payload.has_more) && Boolean(feedNextCursor);

        await Promise.all(freshPosts.map((post) => loadCommentsForPost(post).catch(() => {
          post.comments = [];
        })));
        renderFeed();
        if (!feedHasMore) {
          stopFeedInfiniteScroll();
        }
      } catch (error) {
        console.error(error);
        setFeedError(`Не удалось загрузить посты. Проверьте доступность API: ${FEED_API_BASE}.`);
        showAppNotification(error.message || 'Ошибка загрузки ленты.', 'error');
      } finally {
        setFeedLoadingSkeleton(false);
        feedIsLoading = false;
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
      const precheckState = getPublishPrecheckState(text);
      applyPublishPrecheckHint(precheckState);
      if (precheckState.type === 'warning') {
        showAppNotification(precheckState.message, 'error');
        return;
      }
      
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
          throw new Error(resolveModerationErrorMessage(payload.error || `Ошибка публикации (HTTP ${response.status})`));
        }
        newPostInput.value = '';
        applyPublishPrecheckHint();
        storePendingPostDraft('');
        await loadPosts({ reset: true });
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

      clearChildren(docsList);
      if (filteredDocs.length) {
        filteredDocs.forEach((doc) => {
          const article = document.createElement('article');
          article.className = 'rounded-2xl bg-panel p-4 border border-white/10 animate-fadeInUp';

          const top = document.createElement('div');
          top.className = 'flex items-start justify-between gap-3';
          const content = document.createElement('div');
          const title = document.createElement('h3');
          title.className = 'text-base font-semibold';
          title.textContent = String(doc.title || 'Документ');
          const description = document.createElement('p');
          description.className = 'text-sm text-textSoft mt-1';
          description.textContent = String(doc.description || '');
          content.append(title, description);

          const typeBadge = document.createElement('span');
          typeBadge.className = 'text-[10px] uppercase tracking-wide rounded-full bg-panelSoft text-textSoft px-2 py-1';
          typeBadge.textContent = String(doc.type || 'Документ');
          top.append(content, typeBadge);

          const tags = document.createElement('div');
          tags.className = 'mt-3 flex flex-wrap gap-2';
          doc.tags.forEach((tag) => {
            const tagElement = document.createElement('span');
            tagElement.className = 'rounded-full bg-panelSoft px-2.5 py-1 text-xs text-textSoft';
            tagElement.textContent = `#${tag}`;
            tags.appendChild(tagElement);
          });

          article.append(top, tags);
          docsList.appendChild(article);
        });
      } else {
        const empty = document.createElement('div');
        empty.className = 'rounded-2xl bg-panel p-4 border border-white/10 text-sm text-textSoft';
        empty.textContent = 'Ничего не найдено. Попробуйте другой запрос.';
        docsList.appendChild(empty);
      }

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
    newPostInput.addEventListener('input', () => {
      applyPublishPrecheckHint(getPublishPrecheckState(newPostInput.value));
    });
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

    ensureFeedInfiniteScroll();
    loadPosts({ reset: true });
    renderDocs();
    loadDriverDocuments();
    hydrateProfileForm();
    setRole(initialRole);
    setActiveProfileTab('overview');
    setActiveScreen(initialTab);
    updateGuestProfileStatus();
    applyPublishPrecheckHint();
