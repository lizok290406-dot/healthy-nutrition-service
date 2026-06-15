# Техническое задание: NutriTrack — Умный сервис отслеживания питания

## 1. Цель проекта

NutriTrack решает проблему несистемного подхода к питанию. Сервис позволяет
пользователям вести персональный дневник питания, рассчитывать индивидуальную
норму калорий по научным формулам (Миффлин — Сан Жеор) и отслеживать динамику
веса с помощью интерактивных графиков.

## 2. Роли пользователей

| Роль | Возможности |
|------|-------------|
| **Гость** | Просмотр каталога продуктов, поиск через API, главная страница |
| **Авторизованный пользователь** | Ведение дневника питания, расчёт TDEE/BMI, аналитика, запись веса |
| **Администратор** | Управление всеми данными через Django Admin |

## 3. Модели данных

### FoodCategory (Категория продуктов)
- `name` — CharField, название категории
- `icon` — CharField, эмодзи-иконка
- `color` — CharField, HEX-цвет
- `description` — TextField

### FoodItem (Продукт)
- `name` — CharField
- `category` — ForeignKey → FoodCategory
- `calories`, `proteins`, `carbohydrates`, `fats`, `fiber` — FloatField
- `description` — TextField
- `image` — ImageField
- `is_api_data` — BooleanField

### UserProfile (Профиль пользователя)
- `user` — OneToOneField → User
- `age`, `weight`, `height` — числовые параметры
- `gender` — CharField (choices)
- `activity_level` — CharField (choices)
- `goal` — CharField (choices: похудение/поддержание/набор)
- **Методы:** `calculate_bmr()`, `calculate_tdee()`, `calculate_bmi()`

### MealLog (Дневник питания)
- `user` — ForeignKey → User
- `food_item` — ForeignKey → FoodItem
- `meal_type` — CharField (завтрак/обед/ужин/перекус)
- `amount` — FloatField (граммы)
- `date` — DateField
- **Свойства:** `total_calories`, `total_proteins`, `total_carbohydrates`, `total_fats`

### WeightLog (Дневник веса)
- `user` — ForeignKey → User
- `weight` — FloatField
- `date` — DateField

## 4. Ключевой функционал

- **Дневник питания**: пользователь выбирает продукт и указывает количество (г),
  система автоматически пересчитывает нутриенты пропорционально
- **Расчёт нормы**: по формуле Миффлина — Сан Жеора с учётом активности и цели
- **Каталог с фильтрацией**: поиск по названию, категории, макс. калорийности,
  сортировка через Django ORM (Q-объекты, агрегации)
- **API-поиск**: интеграция с Nutritionix API для поиска продуктов в реальном
  времени (AJAX), демо-режим при отсутствии ключей
- **Аналитика (Pandas + Plotly)**: расчёт среднего/макс./мин. калорий за 30
  дней, интерактивные графики динамики веса и калорий

## 5. Технический стек

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.10, Django 4.2 |
| ORM | Django ORM, ForeignKey, OneToOne, Q/F объекты, агрегации |
| Аналитика | Pandas 2.x |
| Визуализация | Plotly 5.x (интерактивные графики) |
| Внешний API | Nutritionix API (requests) |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Формы | Django Forms / ModelForms с валидацией |
| Хостинг | PythonAnywhere |

## 6. Изменения в ходе реализации

Добавлен AJAX-поиск через Nutritionix API с демо-режимом.
Добавлена модель WeightLog для отслеживания динамики веса.
Добавлен калькулятор калорий как отдельная страница.