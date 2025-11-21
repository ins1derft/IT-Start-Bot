# TODO (shortlist)

- [x] SQLAlchemy models + репозитории для всех сущностей (Publication, Tag, TgUser, Subscriptions, UserPreferences, Parser, ParsingResult, AdminUser).
- [x] Pydantic схемы для чтения + базовые тесты.
- [x] Auth: login/refresh/change-password + rate-limit + TOTP setup/confirm/disable + VPN/white-list IP; интегр. тесты готовы.
- [x] Admin users: аудит операций; enforce role scope (admin full, moderator — только публикации); e2e тесты доступа.
- [x] Publications: фильтры (дата/тип/теги/статус), decline+reason, approve-and-send; статусы добавлены; осталось editor_id отображение и [UPD] рассылка.
- [x] Tags: предзаполнить базовые значения по категориям (из ТЗ), добавить e2e с публикациями (сидинг готов).
- [x] Parsers CRUD/enable/disable + аудит; осталось schedule/beat.
- [x] Stats endpoints (users/tags/parsers/publications) и экспорт CSV; XLSX — в работе.
- [x] Bot: парсер аргументов, FSM (/subscribe step input), /unsubscribe, /preferences, поисковые команды; модульные тесты на парсинг/логика. Осталось: уведомления, block handling, формат [UPD], канал, Redis кеш.
- [ ] Celery задачи: рассылки, дедлайны, cleanup; тесты на идемпотентность/планирование.
- [ ] PGP шифрование contact_info_encrypted; юнит-тесты шифр/дешифр.
- [ ] Метрики Prometheus и Sentry контекст; smoke-тест метрик/healthz.
- [ ] Покрытие ≥80% доменной логики (pytest+coverage).
- [ ] CI: сборка Docker образов (core-api, tg-bot), прогон тестов/линтов, публикация артефактов.
