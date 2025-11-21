# TODO (shortlist)

- [x] SQLAlchemy models + репозитории для всех сущностей (Publication, Tag, TgUser, Subscriptions, UserPreferences, Parser, ParsingResult, AdminUser).
- [x] Pydantic схемы для чтения + базовые тесты.
- [x] Auth: login/refresh/change-password + rate-limit + TOTP setup/confirm/disable + VPN/white-list IP; интегр. тесты готовы.
- [ ] Admin users: аудит операций; enforce role scope (admin full, moderator — только публикации); e2e тесты доступа.
- [ ] Publications: фильтры (дата/тип/теги/статус), decline+reason, approve-and-send, editor_id, статусы модерации, [UPD] рассылка.
- [ ] Tags: предзаполнить базовые значения по категориям (из ТЗ), добавить e2e с публикациями.
- [ ] Parsers CRUD + schedule; поля last_parsed_at; тесты enum parser_type.
- [ ] Stats endpoints и экспорт CSV/XLSX; контрактные тесты.
- [ ] Bot: парсер аргументов, FSM /subscribe, /unsubscribe, /preferences, поисковые команды; модульные тесты на парсинг и FSM.
- [ ] Celery задачи: рассылки, дедлайны, cleanup; тесты на идемпотентность/планирование.
- [ ] PGP шифрование contact_info_encrypted; юнит-тесты шифр/дешифр.
- [ ] Метрики Prometheus и Sentry контекст; smoke-тест метрик/healthz.
- [ ] Покрытие ≥80% доменной логики (pytest+coverage).
- [ ] CI: сборка Docker образов (core-api, tg-bot), прогон тестов/линтов, публикация артефактов.
