# Языки и паритет

У Project Corpus два равноправных пользовательских языка: английский и русский.

- README, client guides, project-instruction template, основной template Corpus,
  FAQ, security guidance, contribution guidance, code of conduct, changelog и
  publishing checklist имеют английскую и русскую версию.
- Установщик создаёт английский или русский Corpus через --language en или
  --language ru.
- Имена файлов протокола, инструментов, JSON-ключей, аргументов командной строки,
  status-констант и authorization-значений остаются на английском, чтобы у всех
  клиентов был один интерфейс.
- При изменении пользовательского поведения обновляйте обе языковые версии в
  одном pull request.
- Автоматические тесты проверяют, что оба template Corpus содержат одинаковые
  authority-файлы и инварианты протокола. Они не заменяют человеческую проверку
  перевода.

Для английского используйте README.md, для русского — README.ru.md.

