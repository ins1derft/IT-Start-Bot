# Расхождения документации и реализации (snapshot)

Снимок собран: **2025-12-12**  
Ветка: **main**  
HEAD: **558fa85** (см. `git log -n 1`)

Цель: зафиксировать расхождения между требованиями/документацией (`docs/*`, README) и фактической реализацией в кодовой базе (backend, TG‑бот, admin frontend).

Легенда статусов:
- ✅ реализовано
- ⚠️ частично реализовано / реализовано иначе
- ❌ не реализовано
- 🟨 документация утверждает иначе (docs ↔ код)

---

## Расхождения (чек‑лист)

### Документация ↔ код (не совпадает заявленный статус/описание)

- [x] **GAP-001 ✅ Roadmap по парсерам актуализирован**: раздел “Этап 4. Парсеры” в `docs/roadmap.md` теперь соответствует текущему коду (external executable, retry 15/45, дедуп, автотеги, `parsing_result`).
  - Docs: `docs/roadmap.md:52`
  - Code: `src/itstart_core_api/parsing_service.py:95`, `src/itstart_core_api/parsing_service.py:151`, `src/itstart_core_api/parsing_service.py:220`

- [x] **GAP-002 ✅ Управление пользователями админки реализовано**: страница пользователей больше не заглушка — доступен список/создание/редактирование/блокировка.
  - Docs: `docs/roadmap.md:41`
  - UI: `src/itstart_admin/src/pages/admin-users/UsersPage.tsx:1`
  - Hooks: `src/itstart_admin/src/hooks/use-admin-users.ts:1`
  - Dialogs: `src/itstart_admin/src/components/admin-users/CreateUserDialog.tsx:1`, `src/itstart_admin/src/components/admin-users/EditUserDialog.tsx:1`

- [x] **GAP-003 ✅ Role-based UI работает**: после логина роль берётся с backend (`/auth/me`), UI-ограничения по ролям соответствуют реальной роли пользователя.
  - Docs: `docs/roadmap.md:41`
  - API: `src/itstart_core_api/auth.py:149`
  - UI: `src/itstart_admin/src/hooks/use-auth.ts:36`

- [x] **GAP-004 ✅ OpenAPI схема доступна**: добавлен `docs/openapi.json`, а также схема доступна в админке по `/openapi.json` (проксируется в core-api).
  - Docs: `src/itstart_admin/README.md:158`
  - Repo: `docs/openapi.json:1`
  - Nginx: `src/itstart_admin/nginx.conf:37`

- [x] **GAP-005 ✅ Health endpoint согласован**: `/healthz` добавлен (в дополнение к `/health`).
  - Docs: `docs/todo.md:14` (упоминание “healthz”)
  - Tests: `tests/test_healthz.py:7`
  - Code: `src/itstart_core_api/api.py:11`

- [x] **GAP-006 ✅ Frontend статистики соответствует backend контракту**:
  - UI использует `active_users/delta` из API и корректно отображает “ошибки парсеров” как список по `parser_id`.
    - UI: `src/itstart_admin/src/pages/stats/StatsPage.tsx:34`, `src/itstart_admin/src/pages/stats/StatsPage.tsx:135`
    - API: `src/itstart_core_api/stats.py:58`, `src/itstart_core_api/stats.py:86`

- [x] **GAP-007 ✅ “Расписание рассылки по типам” работает**: Celery-задачи передают `publication_type`, а рассылка фильтрует публикации по типу.
  - Docs: `docs/roadmap.md:71` (рассылки по `publication_schedule`)
  - Code (планирование задач по типам): `src/itstart_core_api/celery_app.py:58`, `src/itstart_core_api/celery_app.py:175`
  - Code (фильтрация по типу): `src/itstart_core_api/tasks.py:120`, `src/itstart_core_api/tasks.py:134`

- [x] **GAP-008 ✅ “Покрытие ≥80%” выполняется**:
  - Docs: `docs/todo.md:15`
  - CI: `.github/workflows/ci.yml:34` (`--cov-fail-under=80`)
  - Факт: текущий локальный прогон `pytest` даёт Total **80%** (см. `coverage.xml:1`)

---

### Требования ТЗ/User Stories/Устава ↔ реализация (не реализовано/частично)

- [ ] **GAP-009 ❌ 2FA recovery codes не реализованы** (есть в User Stories).
  - Docs: `docs/ТЗ. User stories.docx` (раздел 7.2 “Резервные коды восстановления”)
  - Code: `src/itstart_core_api/auth.py:179` (есть setup/confirm/disable, но recovery codes отсутствуют)

- [ ] **GAP-010 ⚠️ VPN/Whitelist IP enforcement реализован только на логине**: требование “доступ к админке только через VPN/Whitelist” покрыто проверкой IP при `/auth/login`, но далее доступ определяется только JWT.
  - Docs: `docs/adr/0001-architecture.md:7`, `docs/Устав проекта.pdf` (3.2.3 “VPN/Whitelist IP”)
  - Code: `src/itstart_core_api/auth.py:99`

- [x] **GAP-011 ✅ Генерация временного пароля для нового админ‑пользователя реализована** (в User Stories).
  - Docs: `docs/ТЗ. User stories.docx` (1.3 “Генерация временного пароля”)
  - API: `src/itstart_core_api/admin_users.py:40` (пароль генерируется на backend и возвращается в ответе)
  - UI: `src/itstart_admin/src/components/admin-users/CreateUserDialog.tsx:1`

- [ ] **GAP-012 ❌ Пагинация публикаций отсутствует** (в User Stories явно требуется).
  - Docs: `docs/ТЗ. User stories.docx` (2.1 “Пагинация”)
  - Code: `src/itstart_core_api/publications.py:128` (нет limit/offset)

- [ ] **GAP-013 ⚠️ Редактирование публикаций реализовано не для “всех полей”**: сейчас patch поддерживает только `title/description/status/contact_info/deadline_at`.
  - Docs: `docs/ТЗ. User stories.docx` (2.3 “Редактирование всех полей … включая теги”)
  - API: `src/itstart_core_api/publications.py:191`
  - UI: `src/itstart_admin/src/components/publications/EditPublicationDialog.tsx:34`

- [ ] **GAP-014 ⚠️ [UPD] при изменении публикации не выполняется как в ТЗ**:
  - В сообщении есть префикс `[UPD]`, но он появляется только при отправке, и редактирование не инициирует автоматическую отправку для уже отправленных публикаций.
  - Docs: `docs/ТЗ. User stories.docx` (2.3/8.2 про авто‑уведомление “[UPD]”)
  - Code (форматирование): `src/itstart_core_api/tasks.py:27`
  - Code (отправляются только `new/ready`): `src/itstart_core_api/tasks.py:107`
  - Code (редактирование помечает `is_edited`, но не шлёт): `src/itstart_core_api/publications.py:219`

- [ ] **GAP-015 ❌ Команда `/settings` для управления уведомлениями о дедлайнах отсутствует** (требование устава/roadmap).
  - Docs: `docs/roadmap.md:67`, `docs/Устав проекта.pdf` (3.1.3 “/settings”)
  - Code: `src/itstart_tg_bot/bot.py:104` (в /help нет `/settings`, хендлеров нет)
  - Примечание: флаг `deadline_reminder` в БД есть, но UI/бот не даёт управлять (по умолчанию `True`): `src/itstart_core_api/repositories.py:140`

- [ ] **GAP-016 ⚠️ Inline‑кнопки по ТЗ не реализованы**: в боте используется reply‑keyboard, а не inline‑keyboard с callback’ами.
  - Docs: `docs/ТЗ. User stories.docx` (6.2 “Панель inline‑кнопок …”)
  - Code: `src/itstart_tg_bot/bot.py:54`

- [ ] **GAP-017 ❌ FSM storage в Redis не подключён** (roadmap требует Memory → Redis storage).
  - Docs: `docs/roadmap.md:66`
  - Code: `src/itstart_tg_bot/bot.py:78` (Dispatcher без Redis storage)

- [ ] **GAP-018 ⚠️ “Минимум 5 источников” для парсеров не выполнено**: в дефолтном сидировании 4 парсера (tbank/vk/nastachku/podlodka).
  - Docs: `docs/ТЗ. Агенты-парсеры.docx` (раздел “для MVP достаточно 5 любых источников”)
  - Code: `src/itstart_core_api/main.py:121`

- [ ] **GAP-019 ❌ Экспорт в Google Sheets отсутствует** (требование устава/roadmap).
  - Docs: `docs/roadmap.md:39`, `docs/Устав проекта.pdf` (3.1.6 “Google Sheets”)
  - Code: `src/itstart_core_api/export.py:21` (только `csv/xlsx`)

- [ ] **GAP-020 ⚠️ Ограничение “теги — только для admin” не enforced на backend**: UI прячет раздел для moderator, но API `/admin/tags` доступен любому аутентифицированному пользователю.
  - Docs: `docs/ТЗ. Админка.docx` (роли: moderator только публикации)
  - UI guard: `src/itstart_admin/src/router/index.tsx:27`
  - API: `src/itstart_core_api/tags.py:18`
