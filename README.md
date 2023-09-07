# cursor-tg-bot

Настроить команды бота можно напрямую через API Телеграма:
```bash
curl -d \
'{"commands": [{"command": "enable", "description": "Включить бота"},{"command": "add_remove_subscription", "description": "Добавить или убрать рассылку"}]}' \
-X POST https://api.telegram.org/bot<BOT_TOKEN> (https://api.telegram.org/bot<BOT_TOKEN>/setMyCommands)/setMyCommands
```
Важно! Задавать команды таким образом стоит только при первом запуске бота, когда пользователи еще не подключены. Если сделать это после, то команды не будут отображаться у пользователей, которые начали диалог с ботом ранее. Это чинится перезапуском бота со стороны пользователя.