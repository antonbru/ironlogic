# Как написать бота для IronLogic

Бот IronLogic - это обычный Python-файл. Робот конфигурируется объектом `Robot`, поведение задаётся функцией `on_tick(r)`, которая вызывается каждый такт боя.

## Структура файла

```python
# Мой первый робот
from ironlogic_api import Robot

# Конфигурация робота (железо)
robot = Robot(
    name="МойРобот",
    front="eye",        # глаз смотрит вперёд
    right="eye",        # глаз справа
    back="eye",         # глаз сзади
    left="cannon",      # пушка слева
    radar=True,         # радар видит врага на расстоянии
)

radar_on = False

# Программа поведения - вызывается каждый такт
def on_tick(r):
    global radar_on
    if not radar_on:
        r.radar_on()
        radar_on = True
        return
    target = r.radar("ROBOT", 20)
    if target is not None:
        dist, direction = target
        if direction == "left" and dist <= 1:
            r.shoot("left")          # враг вплотную слева - точный выстрел!
            return
        if direction == "front" and dist <= 1:
            r.turn("right")          # враг вплотную спереди - берём на прицел
            return
        if direction == "front":
            if r.eye("front") in ("EMPTY", "AMMO"):
                r.move("forward")    # враг впереди - едем на него
            else:
                r.turn("right")      # стена/яма - объезжаем
            return
        r.turn(direction if direction in ("left", "right") else "left")
        return
    if r.eye("front") in ("EMPTY", "AMMO"):
        r.move("forward")
        return
    if r.eye("front") in ("STONE", "PIT"):
        r.turn("right")
        return
    r.wait()
```

Обязательные элементы:
- объект `robot = Robot(...)` на уровне модуля;
- функция `def on_tick(r)`.

## Конфигурация Robot

Параметры:
- `name` - имя робота (показывается в бою);
- `front`, `right`, `back`, `left` - слоты железа: `"eye"`, `"cannon"` или `"empty"`;
- `radar` - есть ли радар (`True`/`False`).

## Сенсоры (чтение)

| Метод | Возврат | Описание |
|---|---|---|
| r.eye(dir) | str | Имя типа соседней клетки или UNKNOWN, если нет глаза |
| r.radar(kind, radius) | (int, str) или None | Ближайший объект: (расстояние, направление) |
| r.health() | int | Текущее здоровье |
| r.energy() | int | Текущая энергия |
| r.ammo() | int | Текущие патроны |
| r.tick() | int | Номер текущего такта (с 0) |
| r.facing() | str | N / E / S / W |
| r.pos() | (int, int) | Координаты (x, y) |
| r.radar_active() | bool | Включён ли радар |

Направления для `eye` и `shoot`: "front", "right", "back", "left".
Для `move`: "forward", "backward".

## Действия (одно за такт)

| Метод | Возврат | Описание |
|---|---|---|
| r.move(dir) | bool | forward/backward (с учётом cooldown от пушек) |
| r.turn(dir) | bool | left/right |
| r.shoot(dir) | bool | front/right/back/left, нужна пушка, патроны и энергия |
| r.wait() | bool | Пропустить такт |
| r.radar_on() / r.radar_off() | bool | Включить/выключить радар |

Первое действие в такте - финальное. Последующие попытки возвращают False.

## Константы типов клеток

Имена (строки): EMPTY, STONE, PIT, REACTOR, AMMO, RECHARGE, ROBOT, FRIEND, PROJECTILE, UNKNOWN.

## Ошибки

- Ошибки компиляции (синтаксис, нет robot/on_tick, неверные слоты) - робот не допускается к бою, ошибки показываются с номером строки.
- Ошибки времени исполнения (деление на 0, рекурсия глубже 50, превышение бюджета 500 инструкций за такт) - такт завершается wait(), ошибка пишется в лог.
- Пытаться стрелять/двигаться без ресурсов - не ошибка, а неуспешное действие (такт потрачен).

## Примеры в examples/

- kickme.py - ничего не делает (r.wait()).
- wanderer.py - едет вперёд, при препятствии поворачивает, стреляет во врага.
- turret.py - 4 пушки, неподвижен, стреляет по всем сторонам.
- hunter.py - радар ищет врага, едет к нему и стреляет.
- scavenger.py - собирает патроны и стоит на розетках.

Скопируйте пример в bots/ и доработайте под свою стратегию:
`cp examples/wanderer.py bots/my_robot.py`