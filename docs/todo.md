# TODO (shortlist)

- [x] SQLAlchemy models + репозитории для всех сущностей (Publication, Tag, TgUser, Subscriptions, UserPreferences, Parser, ParsingResult, AdminUser).
- [x] Pydantic схемы для чтения + базовые тесты.
- [ ] Auth (refresh/сессии, TOTP), интегр. тесты refresh/2FA. (login + rate-limit done)
- [ ] Admin users CRUD + аудит; тесты ролей/доступа.
- [ ] Publications/Tags CRUD с фильтрами и статусами, причина отклонения; интегр. тесты.
- [ ] Parsers CRUD + schedule; поля last_parsed_at; тесты enum parser_type.
- [ ] Stats endpoints и экспорт CSV/XLSX; контрактные тесты.
- [ ] Bot: парсер аргументов, FSM /subscribe, /unsubscribe, /preferences, поисковые команды; модульные тесты на парсинг и FSM.
- [ ] Celery задачи: рассылки, дедлайны, cleanup; тесты на идемпотентность/планирование.
- [ ] PGP шифрование contact_info_encrypted; юнит-тесты шифр/дешифр.
- [ ] Метрики Prometheus и Sentry контекст; smoke-тест метрик/healthz.
- [ ] Покрытие ≥80% доменной логики (pytest+coverage).
- [ ] CI: сборка Docker образов (core-api, tg-bot), прогон тестов/линтов, публикация артефактов.
