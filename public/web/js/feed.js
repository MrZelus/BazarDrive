
    const posts = [];
    const postIds = new Set();
    const FEED_PAGE_SIZE = 20;
    let feedNextCursor = null;
    let feedHasMore = true;
    let feedIsLoading = false;
    let feedObserver = null;
    let feedSearchQuery = '';
    let feedSearchDebounceTimer = null;
    let feedPendingReset = false;

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
    const THEME_STYLE_STORAGE_KEY = 'bazardrive_theme_style';
    const THEME_STYLE_DEFAULT = 'nebula';
    const VALID_THEME_STYLES = new Set(['nebula', 'aurora']);

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

    function normalizeFeedMediaUrl(rawUrl) {
      const value = String(rawUrl || '').trim();
      if (!value) return '';
      const lowered = value.toLowerCase();
      if (lowered.startsWith('http://') || lowered.startsWith('https://') || lowered.startsWith('data:')) {
        return value;
      }
      if (value.startsWith('/uploads/feed/')) {
        return `${FEED_API_BASE}${value}`;
      }
      return value;
    }

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
    const newPostImageInput = document.getElementById('newPostImageInput');
    const clearPostImageBtn = document.getElementById('clearPostImageBtn');
    const selectedPostImageName = document.getElementById('selectedPostImageName');
    const publishFileError = document.getElementById('publishFileError');
    const feedSearch = document.getElementById('feedSearch');
    const feedSearchStatus = document.getElementById('feedSearchStatus');
    const appNotification = document.getElementById('appNotification');
    let notificationTimer = null;
    const POST_IMAGE_MAX_BYTES = 3 * 1024 * 1024;
    const POST_IMAGE_ALLOWED_MIME_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
    const postDraftMediaState = {
      selectedFile: null,
      error: '',
    };

    const docsList = document.getElementById('docsList');
    const docsSearch = document.getElementById('docsSearch');
    const docsSearchStatus = document.getElementById('docsSearchStatus');
    const themeStyleButtons = document.querySelectorAll('[data-theme-style]');

    function normalizeThemeStyle(style) {
      const normalized = String(style || '').trim().toLowerCase();
      return VALID_THEME_STYLES.has(normalized) ? normalized : THEME_STYLE_DEFAULT;
    }

    function applyThemeStyle(style) {
      const normalized = normalizeThemeStyle(style);
      document.documentElement.setAttribute('data-theme-style', normalized);
      themeStyleButtons.forEach((button) => {
        const isActive = button.dataset.themeStyle === normalized;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-pressed', String(isActive));
      });
      return normalized;
    }

    function setThemeStyle(style) {
      const normalized = applyThemeStyle(style);
      localStorage.setItem(THEME_STYLE_STORAGE_KEY, normalized);
    }

    function hydrateThemeStyle() {
      const styleFromStorage = normalizeThemeStyle(localStorage.getItem(THEME_STYLE_STORAGE_KEY));
      applyThemeStyle(styleFromStorage);
    }

    const tabButtons = document.querySelectorAll('.tab-btn');
	    const profileMenuButtons = document.querySelectorAll('.profile-menu-btn');
	    const profileTabScreens = {
	      overview: document.getElementById('profile-tab-overview'),
	      taxi_ip: document.getElementById('profile-tab-taxi_ip'),
	      documents: document.getElementById('profile-tab-documents'),
	      payouts: document.getElementById('profile-tab-payouts'),
	      security: document.getElementById('profile-tab-security')
	    };
	    const ROLE_TABS = {
	      driver: ['overview', 'taxi_ip', 'documents', 'payouts', 'security'],
	      passenger: ['overview', 'documents', 'security'],
	      guest: ['overview', 'documents', 'security']
	    };
	    const PROFILE_TAB_FALLBACK = 'overview';
    const screens = {
      feed: document.getElementById('screen-feed'),
      rules: document.getElementById('screen-rules'),
      profile: document.getElementById('screen-profile')
    };
	    const VALID_MAIN_TABS = Object.keys(screens);

	    function getAllowedProfileTabs(role) {
	      if (Object.prototype.hasOwnProperty.call(ROLE_TABS, role)) {
	        return ROLE_TABS[role];
	      }
	      return ROLE_TABS.driver;
	    }

	    function getCurrentRole() {
	      const savedRole = localStorage.getItem(ROLE_STORAGE_KEY);
	      return ['driver', 'passenger', 'guest'].includes(savedRole) ? savedRole : 'guest';
	    }

	    function updateProfileTabButtonAccess(role) {
	      const allowedTabs = new Set(getAllowedProfileTabs(role));
	      profileMenuButtons.forEach((btn) => {
	        const tabName = btn.dataset.profileTab;
	        const isAllowed = allowedTabs.has(tabName);
	        btn.disabled = !isAllowed;
	        btn.setAttribute('aria-disabled', String(!isAllowed));
	        btn.setAttribute('aria-hidden', String(!isAllowed));
	        btn.toggleAttribute('hidden', !isAllowed);
	        if (!isAllowed) {
	          btn.tabIndex = -1;
	        }
	      });
	    }

	    function getActiveProfileTab() {
	      const activeButton = Array.from(profileMenuButtons).find((btn) => btn.classList.contains('active'));
	      const requestedTab = activeButton?.dataset?.profileTab;
	      if (requestedTab && Object.prototype.hasOwnProperty.call(profileTabScreens, requestedTab)) {
	        return requestedTab;
	      }
	      return PROFILE_TAB_FALLBACK;
	    }

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
    const profileVerificationBadge = document.getElementById('profileVerificationBadge');
    const profileTrustBadge = document.getElementById('profileTrustBadge');
    const profileVerificationReason = document.getElementById('profileVerificationReason');
    const profileVerificationResubmitBtn = document.getElementById('profileVerificationResubmitBtn');
    const driverDocumentsSection = document.getElementById('driverDocumentsSection');
	    const addDocumentBtn = document.getElementById('addDocumentBtn');
    const addDocumentForm = document.getElementById('addDocumentForm');
    const submitDocumentBtn = document.getElementById('submitDocumentBtn');
    const cancelDocumentBtn = document.getElementById('cancelDocumentBtn');
    const driverDocumentsList = document.getElementById('driverDocumentsList');
    const driverDocumentsLoadingState = document.getElementById('driverDocumentsLoadingState');
    const driverDocumentsEmptyState = document.getElementById('driverDocumentsEmptyState');
    const driverDocumentsErrorState = document.getElementById('driverDocumentsErrorState');
    const documentsApiAlert = document.getElementById('documentsApiAlert');
    const documentTypeInput = document.getElementById('documentType');
    const documentNumberInput = document.getElementById('documentNumber');
    const documentValidUntilInput = document.getElementById('documentValidUntil');
    const documentFileInput = document.getElementById('documentFileInput');
    const documentFileName = document.getElementById('documentFileName');
    const documentTypeError = document.getElementById('documentTypeError');
    const documentNumberError = document.getElementById('documentNumberError');
    const documentValidUntilError = document.getElementById('documentValidUntilError');
    const documentFileError = document.getElementById('documentFileError');
    let isSubmittingDocument = false;
    const DOCUMENT_ALLOWED_MIME_TYPES = new Set(['application/pdf']);
    const DOCUMENT_MAX_BYTES = 10 * 1024 * 1024;

    function isPdfDocumentFile(file) {
      if (!file) return false;
      const fileType = String(file.type || '').trim().toLowerCase();
      if (DOCUMENT_ALLOWED_MIME_TYPES.has(fileType)) return true;
      if (fileType === 'application/octet-stream' || !fileType) {
        const fileName = String(file.name || '').trim().toLowerCase();
        return fileName.endsWith('.pdf');
      }
      return false;
    }
    const MODERATION_ERROR_COPY = {
      prohibited: 'Публикация отклонена модерацией: обнаружена запрещённая тема.',
      links: 'Публикация отклонена: в одном посте можно указать не более 2 ссылок.',
      spam: 'Публикация отклонена: текст похож на спам из повторяющихся слов.',
      too_short: 'Текст слишком короткий: напишите минимум 5 символов.',
      generic: 'Публикация отклонена правилами модерации. Исправьте текст и попробуйте снова.',
    };
    const INTERACTION_ERROR_COPY = {
      profileRequired: 'Сначала заполните и сохраните профиль публикации.',
      forbiddenCommentEdit: 'Можно редактировать только свои комментарии.',
      forbiddenCommentDelete: 'Можно удалять только свои комментарии.',
      postNotFound: 'Пост не найден или уже удалён.',
      commentNotFound: 'Комментарий не найден или уже удалён.',
      commentValidation: 'Проверьте текст комментария и попробуйте снова.',
      reactionValidation: 'Некорректная реакция. Попробуйте обновить страницу.',
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

    function setButtonBusyState(button, isBusy, busyText = '', idleText = '') {
      if (!button) return;
      const busy = Boolean(isBusy);
      button.disabled = busy;
      button.setAttribute('aria-disabled', String(busy));
      button.setAttribute('aria-busy', String(busy));
      button.classList.toggle('is-loading', busy);
      if (busy && busyText) {
        button.textContent = busyText;
      } else if (!busy && idleText) {
        button.textContent = idleText;
      }
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

    function resolveInteractionErrorMessage(rawMessage = '', rawCode = '', fallbackMessage = 'Не удалось выполнить действие.') {
      const source = String(rawMessage || '').trim();
      const code = String(rawCode || '').trim().toLowerCase();
      if (!source) return String(fallbackMessage || '').trim() || 'Не удалось выполнить действие.';
      if (code === 'guest_profile_required') return INTERACTION_ERROR_COPY.profileRequired;
      if (code === 'comment_edit_forbidden') return INTERACTION_ERROR_COPY.forbiddenCommentEdit;
      if (code === 'comment_delete_forbidden') return INTERACTION_ERROR_COPY.forbiddenCommentDelete;
      if (code === 'comment_not_found') return INTERACTION_ERROR_COPY.commentNotFound;
      if (code === 'post_not_found') return INTERACTION_ERROR_COPY.postNotFound;
      if (code === 'comment_text_required' || code === 'comment_text_too_long' || code === 'comment_text_too_short') {
        return INTERACTION_ERROR_COPY.commentValidation;
      }
      if (code === 'reaction_type_invalid') return INTERACTION_ERROR_COPY.reactionValidation;

      const normalized = source.toLowerCase();
      if (normalized.includes('guest_profile_id') && normalized.includes('обязательно')) {
        return INTERACTION_ERROR_COPY.profileRequired;
      }
      if (normalized.includes('недостаточно прав для изменения комментария')) {
        return INTERACTION_ERROR_COPY.forbiddenCommentEdit;
      }
      if (normalized.includes('недостаточно прав для удаления комментария')) {
        return INTERACTION_ERROR_COPY.forbiddenCommentDelete;
      }
      if (normalized.includes('комментар') && normalized.includes('не найден')) {
        return INTERACTION_ERROR_COPY.commentNotFound;
      }
      if (normalized.includes('пост') && normalized.includes('не найден')) {
        return INTERACTION_ERROR_COPY.postNotFound;
      }
      if (normalized.includes('комментар') && (normalized.includes('обязательно') || normalized.includes('слишком длин') || normalized.includes('минимум'))) {
        return INTERACTION_ERROR_COPY.commentValidation;
      }
      if (normalized.includes('тип реакции') || normalized.includes('реакц') && normalized.includes('допустимые значения')) {
        return INTERACTION_ERROR_COPY.reactionValidation;
      }

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

    function bytesToMb(sizeInBytes = 0) {
      const value = Number(sizeInBytes) / (1024 * 1024);
      return value.toFixed(1);
    }

    function setPublishFileError(message = '') {
      const normalized = String(message || '').trim();
      postDraftMediaState.error = normalized;
      if (!publishFileError) return;
      publishFileError.textContent = normalized;
      publishFileError.classList.toggle('hidden', !normalized);
    }

    function updateSelectedPostImageUi() {
      if (selectedPostImageName) {
        selectedPostImageName.textContent = postDraftMediaState.selectedFile
          ? `Выбрано фото: ${postDraftMediaState.selectedFile.name}`
          : 'Фото не выбрано';
      }
      if (clearPostImageBtn) {
        clearPostImageBtn.classList.toggle('hidden', !postDraftMediaState.selectedFile);
      }
    }

    function clearSelectedPostImage() {
      postDraftMediaState.selectedFile = null;
      setPublishFileError('');
      if (newPostImageInput) {
        newPostImageInput.value = '';
      }
      updateSelectedPostImageUi();
    }

    function validateSelectedPostImage(file) {
      if (!file) {
        return 'Не удалось прочитать выбранный файл. Попробуйте выбрать фото ещё раз.';
      }
      if (!POST_IMAGE_ALLOWED_MIME_TYPES.has(file.type)) {
        return 'Неподдерживаемый формат фото. Допустимые типы: JPG, PNG, WEBP.';
      }
      if (file.size > POST_IMAGE_MAX_BYTES) {
        return `Фото слишком большое. Максимальный размер: ${bytesToMb(POST_IMAGE_MAX_BYTES)} МБ.`;
      }
      return '';
    }

    function handlePostImageChange(event) {
      const file = event?.target?.files?.[0];
      if (!file) {
        clearSelectedPostImage();
        return;
      }
      const validationError = validateSelectedPostImage(file);
      if (validationError) {
        postDraftMediaState.selectedFile = null;
        if (newPostImageInput) {
          newPostImageInput.value = '';
        }
        setPublishFileError(validationError);
        updateSelectedPostImageUi();
        return;
      }
      postDraftMediaState.selectedFile = file;
      setPublishFileError('');
      updateSelectedPostImageUi();
    }

    function fileToBase64Payload(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const rawResult = String(reader.result || '');
          const [, base64Payload = ''] = rawResult.split(',', 2);
          if (!base64Payload) {
            reject(new Error('Не удалось подготовить фото к публикации. Попробуйте выбрать другой файл.'));
            return;
          }
          resolve(base64Payload);
        };
        reader.onerror = () => {
          reject(new Error('Не удалось прочитать фото. Попробуйте выбрать файл ещё раз.'));
        };
        reader.readAsDataURL(file);
      });
    }

    function isImageValidationErrorMessage(message) {
      const normalized = String(message || '').trim().toLowerCase();
      if (!normalized) return false;
      return [
        'image',
        'изображ',
        'mime',
        'base64',
        'media_type',
        'media[]',
        'фото',
      ].some((needle) => normalized.includes(needle));
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
      card.className = 'rounded-xl border border-textSoft/20 bg-panelSoft px-3 py-2 text-sm text-textSoft';
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
        card.className = 'rounded-xl border border-textSoft/20 bg-panelSoft px-3 py-2';

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
      [documentTypeError, documentNumberError, documentValidUntilError, documentFileError].forEach((el) => {
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
        file_url: documentFileError,
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
        setButtonBusyState(submitDocumentBtn, isSubmittingDocument, 'Сохранение...', 'Сохранить');
      }
      if (cancelDocumentBtn) {
        cancelDocumentBtn.disabled = isSubmittingDocument;
        cancelDocumentBtn.setAttribute('aria-disabled', String(isSubmittingDocument));
      }
      if (addDocumentBtn) {
        addDocumentBtn.disabled = isSubmittingDocument;
        addDocumentBtn.setAttribute('aria-disabled', String(isSubmittingDocument));
      }
      [documentTypeInput, documentNumberInput, documentValidUntilInput, documentFileInput].forEach((field) => {
        if (!field) return;
        field.disabled = isSubmittingDocument;
      });
    }

    function setDriverDocumentsListState(state, errorMessage = '') {
      const normalizedState = ['loading', 'empty', 'error', 'ready'].includes(state) ? state : 'ready';
      const isLoading = normalizedState === 'loading';
      const isEmpty = normalizedState === 'empty';
      const isError = normalizedState === 'error';

      if (driverDocumentsLoadingState) {
        driverDocumentsLoadingState.classList.toggle('hidden', !isLoading);
        driverDocumentsLoadingState.setAttribute('aria-hidden', String(!isLoading));
      }
      if (driverDocumentsEmptyState) {
        driverDocumentsEmptyState.classList.toggle('hidden', !isEmpty);
        driverDocumentsEmptyState.setAttribute('aria-hidden', String(!isEmpty));
      }
      if (driverDocumentsErrorState) {
        driverDocumentsErrorState.classList.toggle('hidden', !isError);
        driverDocumentsErrorState.setAttribute('aria-hidden', String(!isError));
        if (isError) {
          driverDocumentsErrorState.textContent = String(errorMessage || 'Не удалось загрузить список документов.');
        }
      }
      if (driverDocumentsList) {
        driverDocumentsList.setAttribute('aria-busy', String(isLoading));
        if (isLoading || isError) {
          clearChildren(driverDocumentsList);
        }
      }
    }

    function renderDriverDocuments(items = []) {
      if (!driverDocumentsList) return;
      clearChildren(driverDocumentsList);
      if (!Array.isArray(items) || items.length === 0) {
        setDriverDocumentsListState('empty');
        renderDriverOverviewDocuments([]);
        return;
      }

      setDriverDocumentsListState('ready');

      const labels = {
        passport: 'Паспорт', inn: 'ИНН', ogrnip: 'ОГРНИП', taxi_license: 'Разрешение на такси',
        waybill: 'Путевой лист',
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
        article.className = 'rounded-xl border border-textSoft/20 bg-panelSoft px-3 py-3 space-y-2';

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
        deleteButton.setAttribute('aria-label', `Удалить документ: ${String(item.title || 'Документ')}`);
        deleteButton.addEventListener('click', async () => {
          const id = Number(deleteButton.dataset.docDelete);
          if (!id) return;
          setButtonBusyState(deleteButton, true, 'Удаление...');
          try {
            const response = await fetch(`${FEED_API_BASE}/api/driver/documents/${id}`, { method: 'DELETE' });
            if (!response.ok) {
              throw new Error(`Не удалось удалить документ (HTTP ${response.status})`);
            }
            await loadDriverDocuments();
          } catch (error) {
            console.error(error);
            setDocumentAlert(error.message || 'Не удалось удалить документ');
            setButtonBusyState(deleteButton, false, '', 'Удалить');
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
        if (item.file_url) {
          const link = document.createElement('a');
          link.className = 'text-xs text-accent hover:underline';
          link.href = normalizeFeedMediaUrl(item.file_url);
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = 'Открыть PDF-документ';
          article.appendChild(link);
        }
        driverDocumentsList.appendChild(article);
      });
      renderDriverOverviewDocuments(normalizedItems);
    }

    async function loadDriverDocuments() {
      setDriverDocumentsListState('loading');
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
        const errorMessage = error.message || 'Не удалось загрузить список документов';
        setDocumentAlert(errorMessage);
        setDriverDocumentsListState('error', errorMessage);
      } finally {
        if (driverDocumentsList?.getAttribute('aria-busy') === 'true') {
          setDriverDocumentsListState('ready');
        }
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
        if (documentFileName) {
          documentFileName.textContent = 'Файл не выбран';
        }
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

    async function uploadDriverDocumentFile(file) {
      const formData = new FormData();
      formData.append('file', file, file.name || 'waybill.pdf');
      const response = await fetch(`${FEED_API_BASE}/api/driver/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || `Не удалось загрузить PDF (HTTP ${response.status})`);
      }
      return String(data.file_url || '').trim();
    }

    async function submitDriverDocument(event) {
      event.preventDefault();
      clearDocumentErrors();
      setDocumentAlert('');

      const { payload, errors } = validateDocumentForm();
      const selectedFile = documentFileInput?.files?.[0] || null;
      if (selectedFile && !isPdfDocumentFile(selectedFile)) {
        errors.file_url = 'Поддерживается только PDF-файл';
      }
      if (selectedFile && selectedFile.size > DOCUMENT_MAX_BYTES) {
        errors.file_url = 'PDF-файл слишком большой (максимум 10 МБ)';
      }
      if (Object.keys(errors).length > 0) {
        showDocumentErrors(errors);
        return;
      }

      applyDocumentLoadingState(true);

      try {
        if (selectedFile) {
          payload.file_url = await uploadDriverDocumentFile(selectedFile);
        }
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

    if (documentFileInput && documentFileName) {
      documentFileInput.addEventListener('change', () => {
        const selectedFile = documentFileInput.files?.[0];
        documentFileName.textContent = selectedFile ? selectedFile.name : 'Файл не выбран';
        if (documentFileError) {
          documentFileError.textContent = '';
          documentFileError.classList.add('hidden');
        }
      });
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
      const allowedVerificationStates = new Set(['unverified', 'pending_verification', 'verified', 'rejected', 'expired']);
      const rawVerificationState = String(stored.verificationState || stored.verification_state || '').trim().toLowerCase();
      const safeVerificationState = allowedVerificationStates.has(rawVerificationState) ? rawVerificationState : null;

      return {
        id: profileId,
        role: 'guest_author',
        display_name: fullName,
        email: email || null,
        phone: phone || null,
        about: about || null,
        status: 'active',
        is_verified: Boolean(stored.isVerified),
        verification_state: safeVerificationState || '',
      };
    }

    function isGuestProfileReady(profile) {
      const normalizedProfile = profile || {};
      const hasName = String(normalizedProfile.display_name || '').trim().length >= 2;
      const hasContact = Boolean(String(normalizedProfile.email || '').trim() || String(normalizedProfile.phone || '').trim());
      return hasName && hasContact;
    }

    function resolveVerificationState(profile) {
      const rawState = String(profile?.verification_state || profile?.verificationState || '').trim();
      if (rawState) return rawState;
      if (profile?.is_verified || profile?.isVerified) return 'verified';
      return 'unverified';
    }

    function renderProfileTrustSignals(profile) {
      const verificationState = resolveVerificationState(profile);
      const verificationLabels = {
        unverified: 'не начата',
        pending_verification: 'на проверке',
        verified: 'подтверждена',
        rejected: 'отклонена',
        blocked: 'заблокирована',
      };

      if (profileVerificationBadge) {
        profileVerificationBadge.textContent = `Верификация: ${verificationLabels[verificationState] || verificationState}`;
      }
      if (profileTrustBadge) {
        const trustLabel = verificationState === 'verified' ? 'подтверждённый' : 'базовый';
        profileTrustBadge.textContent = `Trust badge: ${trustLabel}`;
      }
      if (profileVerificationReason) {
        const reason = String(profile?.verification_rejection_reason || profile?.verificationRejectionReason || '').trim();
        const showReason = verificationState === 'rejected' && reason;
        profileVerificationReason.classList.toggle('hidden', !showReason);
        profileVerificationReason.textContent = showReason ? `Причина отклонения: ${reason}` : '';
      }
      if (profileVerificationResubmitBtn) {
        const canResubmit = verificationState === 'rejected';
        profileVerificationResubmitBtn.classList.toggle('hidden', !canResubmit);
      }
    }

    async function submitProfileForResubmission() {
      const profile = getStoredGuestProfile();
      const profileId = String(profile.id || '').trim();
      if (!profileId) {
        showAppNotification('Сначала сохраните профиль публикации.', 'error');
        return;
      }
      setButtonBusyState(profileVerificationResubmitBtn, true, 'Отправка...');
      try {
        const response = await fetch(`${FEED_API_BASE}/api/feed/profiles/${encodeURIComponent(profileId)}/verification/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ actor: profileId }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.error || `Не удалось отправить на повторную проверку (HTTP ${response.status})`);
        }
        localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify({
          ...profile,
          isVerified: Boolean(payload.is_verified),
          verificationState: String(payload.verification_state || payload.verificationState || '').trim(),
          verificationRejectionReason: String(payload.verification_rejection_reason || '').trim(),
        }));
        updateGuestProfileStatus();
        showAppNotification('Профиль повторно отправлен на проверку.', 'success');
      } catch (error) {
        console.error(error);
        showAppNotification(error.message || 'Не удалось отправить профиль на повторную проверку.', 'error');
      } finally {
        setButtonBusyState(profileVerificationResubmitBtn, false, '', 'Отправить на повторную проверку');
      }
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
          url: normalizeFeedMediaUrl(entry?.url),
          position: Number.isFinite(Number(entry?.position)) ? Number(entry.position) : index,
        }))
        .filter((entry) => entry.url)
        .sort((a, b) => a.position - b.position);
      const legacyImage = String(item.image_url || '').trim();
      const normalizedLegacyImage = legacyImage.toLowerCase();
      const safeLegacyImage = (
        legacyImage &&
        normalizedLegacyImage !== 'none' &&
        normalizedLegacyImage !== 'null'
      ) ? normalizeFeedMediaUrl(legacyImage) : '';
      if (
        !normalizedMedia.length &&
        safeLegacyImage
      ) {
        normalizedMedia.push({ mediaType: 'image', url: safeLegacyImage, position: 0 });
      }
      return {
        id: item.id,
        author: item.author || 'Гость',
        guestProfileId: String(item.guest_profile_id || '').trim(),
        avatar: pickAvatar(item.author),
        publishedAt: formatPostDate(item.created_at),
        text: item.text || '',
        image: safeLegacyImage,
        media: normalizedMedia,
        reactions,
        myReaction,
        likes: Number(item.likes ?? reactions.like) || 0,
        comments: [],
        commentsTotal: Number.isFinite(Number(item.comments_total)) ? Number(item.comments_total) : null,
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
      const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${postId}/reactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_profile_id: actorId, type: reactionType }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(resolveInteractionErrorMessage(payload.error, payload.error_code, `Не удалось установить реакцию (HTTP ${response.status})`));
      }
      return payload;
    }

    async function deletePostReaction(postId, actorId) {
      const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${postId}/reactions`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ guest_profile_id: actorId }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(resolveInteractionErrorMessage(payload.error, payload.error_code, `Не удалось снять реакцию (HTTP ${response.status})`));
      }
      return payload;
    }

    function createInteractionButton(iconText, value, label, extraClasses = '') {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', `${String(label || '').trim()}: ${Number(value || 0)}`);
      button.className = `group inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-textSoft transition hover:bg-panelSoft hover:text-text ${extraClasses}`.trim();

      const icon = document.createElement('span');
      icon.setAttribute('aria-hidden', 'true');
      icon.textContent = iconText;

      const counter = document.createElement('span');
      counter.textContent = String(value || 0);

      button.append(icon, counter);
      return button;
    }

    function resolveCommentCounter(post) {
      if (Number.isFinite(Number(post?.commentsTotal))) {
        return Math.max(0, Number(post.commentsTotal));
      }
      return Array.isArray(post?.comments) ? post.comments.length : 0;
    }

    function renderFeed() {
      clearChildren(feedEl);
      posts.forEach((post) => {
        const actor = getCurrentGuestActor();
        const article = document.createElement('article');
        article.className = 'rounded-2xl bg-panel p-4 border border-textSoft/20 animate-fadeInUp';

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
          deletePostBtn.setAttribute('aria-label', `Удалить пост автора ${String(post.author || 'Гость')}`);
          deletePostBtn.addEventListener('click', async () => {
            setButtonBusyState(deletePostBtn, true, 'Удаление...');
            try {
              await deletePost(post.id, actor.id);
              await loadPosts({ reset: true });
              showAppNotification('Пост удалён.', 'success');
            } catch (error) {
              console.error(error);
              showAppNotification(error.message || 'Не удалось удалить пост.', 'error');
            } finally {
              setButtonBusyState(deletePostBtn, false, '', 'Удалить');
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
              video.className = 'max-h-[420px] min-w-full snap-center rounded-xl bg-panel object-contain';
              mediaContainer.appendChild(video);
              return;
            }
            const image = document.createElement('img');
            image.src = String(item.url || '');
            image.alt = `Изображение поста ${index + 1}`;
            image.className = 'h-auto w-full max-h-[420px] snap-center rounded-xl object-contain';
            image.loading = 'lazy';
            mediaContainer.appendChild(image);
          });
          article.appendChild(mediaContainer);
        } else if (post.image) {
          const image = document.createElement('img');
          image.src = String(post.image);
          image.alt = 'Изображение поста';
          image.className = 'mb-3 h-auto w-full max-h-[420px] rounded-xl object-contain';
          image.loading = 'lazy';
          article.appendChild(image);
        }

        const footer = document.createElement('footer');
        footer.className = 'flex items-center gap-1 border-t border-textSoft/20 pt-2';

        const likeButton = createInteractionButton('♡', post.likes, 'Лайк', `js-like-btn ${post.likedByMe ? 'text-accent' : ''}`);
        likeButton.dataset.postId = String(post.id || '');
        likeButton.addEventListener('click', async () => {
          const postId = Number(likeButton.dataset.postId);
          const target = posts.find((currentPost) => currentPost.id === postId);
          if (!target) return;
          if (!actor.id) {
            showAppNotification('Сначала заполните и сохраните профиль публикации.', 'error');
            return;
          }
          setButtonBusyState(likeButton, true);
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
            setButtonBusyState(likeButton, false);
          }
        });

        const commentsCounter = resolveCommentCounter(post);
        footer.append(
          likeButton,
          createInteractionButton('💬', commentsCounter, 'Комментарий'),
          createInteractionButton('↻', post.reposts, 'Репост'),
        );
        article.appendChild(footer);

        const commentsWrap = document.createElement('section');
        commentsWrap.className = 'mt-3 border-t border-textSoft/20 pt-3 space-y-2';

        const commentsTitle = document.createElement('p');
        commentsTitle.className = 'text-xs uppercase tracking-wide text-textSoft';
        commentsTitle.textContent = `Комментарии (${commentsCounter})`;
        commentsWrap.appendChild(commentsTitle);

        const commentList = document.createElement('div');
        commentList.className = 'space-y-2';
        (post.comments || []).forEach((comment) => {
          const row = document.createElement('div');
          row.className = 'rounded-lg border border-textSoft/20 bg-panelSoft px-3 py-2';

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
            editBtn.setAttribute('aria-label', `Редактировать комментарий от ${String(comment.author || 'автора')}`);
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
                if (!response.ok) throw new Error(resolveInteractionErrorMessage(payload.error, payload.error_code, `Не удалось обновить комментарий (HTTP ${response.status})`));
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
            deleteBtn.setAttribute('aria-label', `Удалить комментарий от ${String(comment.author || 'автора')}`);
            deleteBtn.addEventListener('click', async () => {
              setButtonBusyState(deleteBtn, true, 'Удаление...');
              try {
                const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${post.id}/comments/${comment.id}`, {
                  method: 'DELETE',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ guest_profile_id: actor.id }),
                });
                const payload = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(resolveInteractionErrorMessage(payload.error, payload.error_code, `Не удалось удалить комментарий (HTTP ${response.status})`));
                await loadCommentsForPost(post);
                renderFeed();
                showAppNotification('Комментарий удалён.', 'success');
              } catch (error) {
                console.error(error);
                showAppNotification(error.message || 'Не удалось удалить комментарий.', 'error');
              } finally {
                setButtonBusyState(deleteBtn, false, '', 'Удалить');
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
        input.className = 'min-w-0 flex-1 rounded-lg border border-textSoft/25 bg-panel px-3 py-2 text-sm text-text outline-none focus:border-accent';
        const submit = document.createElement('button');
        submit.type = 'submit';
        submit.className = 'rounded-lg bg-accent px-3 py-2 text-xs font-semibold text-white hover:opacity-90';
        submit.textContent = 'Отправить';
        submit.setAttribute('aria-label', `Отправить комментарий к посту автора ${String(post.author || 'Гость')}`);
        form.append(input, submit);
        form.addEventListener('submit', async (event) => {
          event.preventDefault();
          const text = String(input.value || '').trim();
          if (!text) {
            showAppNotification('Введите текст комментария.', 'error');
            return;
          }
          if (!actor.id) {
            showAppNotification('Сначала заполните и сохраните профиль публикации.', 'error');
            return;
          }
          setButtonBusyState(submit, true, 'Отправка...');
          try {
            const response = await fetch(`${FEED_API_BASE}/api/feed/posts/${post.id}/comments`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ guest_profile_id: actor.id, author: actor.fullName, text }),
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(resolveInteractionErrorMessage(payload.error, payload.error_code, `Не удалось добавить комментарий (HTTP ${response.status})`));
            input.value = '';
            await loadCommentsForPost(post);
            renderFeed();
            showAppNotification('Комментарий добавлен.', 'success');
          } catch (error) {
            console.error(error);
            showAppNotification(error.message || 'Не удалось добавить комментарий.', 'error');
          } finally {
            setButtonBusyState(submit, false, '', 'Отправить');
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
      post.commentsTotal = Number.isFinite(Number(payload.total)) ? Number(payload.total) : post.comments.length;
    }

    function setFeedLoadingSkeleton(isVisible) {
      if (!feedLoadStateEl) return;
      clearChildren(feedLoadStateEl);
      if (!isVisible) return;
      for (let idx = 0; idx < 2; idx += 1) {
        const skeleton = document.createElement('div');
        skeleton.className = 'rounded-2xl border border-textSoft/20 bg-panel p-4 animate-pulse';
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
      warning.className = 'rounded-2xl bg-panel p-4 border border-textSoft/20 text-sm text-warning';
      warning.textContent = normalized;
      feedLoadStateEl.appendChild(warning);
    }

    function stopFeedInfiniteScroll() {
      if (feedObserver) {
        feedObserver.disconnect();
      }
    }

    function updateFeedSearchStatus(total = null) {
      if (!feedSearchStatus) return;
      const query = String(feedSearchQuery || '').trim();
      if (!query) {
        feedSearchStatus.textContent = '';
        return;
      }
      if (!Number.isFinite(Number(total))) {
        feedSearchStatus.textContent = `Поиск: «${query}».`;
        return;
      }
      feedSearchStatus.textContent = `Поиск: «${query}». Найдено постов: ${Math.max(0, Number(total))}.`;
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
      if (feedIsLoading) {
        if (reset) {
          feedPendingReset = true;
        }
        return;
      }
      if (!reset && !feedHasMore) return;
      feedIsLoading = true;
      if (reset) {
        feedPendingReset = false;
      }
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
        if (feedSearchQuery) {
          params.set('q', feedSearchQuery);
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
        updateFeedSearchStatus(payload.total);

        await Promise.all(freshPosts.map((post) => loadCommentsForPost(post).catch(() => {
          post.comments = [];
        })));
        renderFeed();
        if (!feedHasMore) {
          stopFeedInfiniteScroll();
        }
      } catch (error) {
        console.error(error);
        updateFeedSearchStatus();
        setFeedError(`Не удалось загрузить посты. Проверьте доступность API: ${FEED_API_BASE}.`);
        showAppNotification(error.message || 'Ошибка загрузки ленты.', 'error');
      } finally {
        setFeedLoadingSkeleton(false);
        feedIsLoading = false;
        if (feedPendingReset) {
          feedPendingReset = false;
          loadPosts({ reset: true });
        }
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
      if (postDraftMediaState.error) {
        showAppNotification(postDraftMediaState.error, 'error');
        return;
      }
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
        showAppNotification('Для публикации заполните профиль публикации: имя и хотя бы email или телефон. После сохранения публикация продолжится автоматически.', 'info');
        return;
      }

      storePendingPostDraft('');
      setButtonBusyState(publishBtn, true, 'Публикация...');
      try {
        const selectedFile = postDraftMediaState.selectedFile;
        const payloadBody = { author, text, guest_profile: guestProfile };
        const hasSelectedImage = Boolean(selectedFile);
        if (hasSelectedImage) {
          payloadBody.image_base64 = await fileToBase64Payload(selectedFile);
          payloadBody.image_mime_type = selectedFile.type;
        }
        const response = await fetch(`${FEED_API_BASE}/api/feed/posts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payloadBody),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          if (hasSelectedImage && response.status === 413) {
            throw new Error('Фото слишком большое для публикации. Выберите изображение меньшего размера.');
          }
          if (hasSelectedImage && response.status === 400) {
            const responseError = String(payload.error || '').trim();
            if (isImageValidationErrorMessage(responseError)) {
              throw new Error(`Не удалось опубликовать фото. ${responseError}`);
            }
            throw new Error(resolveModerationErrorMessage(responseError || 'Ошибка публикации (HTTP 400)'));
          }
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
        clearSelectedPostImage();
        applyPublishPrecheckHint();
        storePendingPostDraft('');
        await loadPosts({ reset: true });
      } catch (error) {
        console.error(error);
        showAppNotification(error.message || 'Не удалось опубликовать пост', 'error');
      } finally {
        setButtonBusyState(publishBtn, false, '', 'Опубликовать');
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
          article.className = 'rounded-2xl bg-panel p-4 border border-textSoft/20 animate-fadeInUp';

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
        empty.className = 'rounded-2xl bg-panel p-4 border border-textSoft/20 text-sm text-textSoft';
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
	      const requestedTab = Object.prototype.hasOwnProperty.call(profileTabScreens, tab) ? tab : PROFILE_TAB_FALLBACK;
	      const allowedTabs = new Set(getAllowedProfileTabs(getCurrentRole()));
	      const activeTab = allowedTabs.has(requestedTab) ? requestedTab : PROFILE_TAB_FALLBACK;

	      profileMenuButtons.forEach((btn) => {
	        const isActive = btn.dataset.profileTab === activeTab;
	        btn.classList.toggle('active', isActive);
	        btn.setAttribute('aria-selected', String(isActive));
	        if (btn.disabled || btn.hidden) {
	          btn.tabIndex = -1;
	        } else {
	          btn.tabIndex = isActive ? 0 : -1;
	        }
	      });
	      Object.entries(profileTabScreens).forEach(([name, screen]) => {
	        const isActive = name === activeTab;
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
        const isActive = btn.dataset.role === role;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-pressed', String(isActive));
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
      if (driverDocumentsSection) {
        const showDriverDocuments = role === 'driver';
        driverDocumentsSection.classList.toggle('hidden', !showDriverDocuments);
        driverDocumentsSection.toggleAttribute('hidden', !showDriverDocuments);
        driverDocumentsSection.setAttribute('aria-hidden', String(!showDriverDocuments));
        if (!showDriverDocuments) {
          toggleDocumentForm(false);
        }
      }
	      updateProfileTabButtonAccess(role);
	      const allowedTabs = new Set(getAllowedProfileTabs(role));
	      const currentActiveTab = getActiveProfileTab();
	      if (!allowedTabs.has(currentActiveTab)) {
	        setActiveProfileTab(PROFILE_TAB_FALLBACK);
	      }
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

      setButtonBusyState(saveProfileBtn, true, 'Сохранение...');
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
          isVerified: Boolean(payload.is_verified),
          verificationState: String(payload.verification_state || payload.verificationState || '').trim(),
          verificationRejectionReason: String(payload.verification_rejection_reason || payload.verificationRejectionReason || '').trim(),
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
        showAppNotification('Профиль публикации сохранён.', 'success');
      } catch (error) {
        console.error(error);
        showAppNotification(error.message || 'Не удалось сохранить профиль публикации', 'error');
      } finally {
        setButtonBusyState(saveProfileBtn, false, '', 'Сохранить профиль публикации');
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
      const storedProfile = getStoredGuestProfile();
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
      renderProfileTrustSignals(storedProfile);
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
    newPostImageInput?.addEventListener('change', handlePostImageChange);
    clearPostImageBtn?.addEventListener('click', clearSelectedPostImage);
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
    feedSearch?.addEventListener('input', (event) => {
      const raw = String(event?.target?.value || '').trim();
      if (raw && raw.length < 2) {
        feedSearchQuery = '';
        if (feedSearchStatus) {
          feedSearchStatus.textContent = `Введите ещё ${2 - raw.length} символ(а), чтобы включить поиск.`;
        }
      } else {
        feedSearchQuery = raw;
      }

      if (feedSearchDebounceTimer) {
        window.clearTimeout(feedSearchDebounceTimer);
      }
      feedSearchDebounceTimer = window.setTimeout(() => {
        loadPosts({ reset: true });
      }, 220);
    });
    saveProfileBtn.addEventListener('click', saveGuestProfile);
    profileVerificationResubmitBtn?.addEventListener('click', submitProfileForResubmission);
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
    const initialRole = ['driver', 'passenger', 'guest'].includes(savedRole) ? savedRole : 'guest';
    const initialTab = VALID_MAIN_TABS.includes(savedActiveTab) ? savedActiveTab : 'feed';

    updateSelectedPostImageUi();
    ensureFeedInfiniteScroll();
    loadPosts({ reset: true });
    renderDocs();
    loadDriverDocuments();
    hydrateProfileForm();
    hydrateThemeStyle();
    setRole(initialRole);
    setActiveProfileTab('overview');
    setActiveScreen(initialTab);
    updateGuestProfileStatus();
    applyPublishPrecheckHint();
