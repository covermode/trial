# ----------------------------- Autor: Ilya Latypov ---------------------------
# +++          TRIAL. pygame project
#
"""This is a main project file. Keep in mind that using this code without my permission is disallowed,
except launching like a single application for personal use only"""

import pygame as pg
import os
import abc
import json
from random import randint


# DAY1:     Created base, don't tested.
# DAY2:     Manage drawing, start working on UserInput, make player
# DAY3:     Make animation_class, start working on a float-pos problem
# DAY4:     Solve a float-pos problem, add screen motion, make stable build of preview
# DAY5:     Create a cube.
# DAY6: ----chilling
# DAY7:     Make a info cell and exit cell.
# DAY8:     Make levels
# DAY9:     Allow animation


def perform(func, *args, **kwargs):
    """Вспомогательная функция. При выполнении возвращаемой функции указанные аргументы
    будут подставлены вместо переданных при вызове. Создана для следующей функции """
    def f(*_, **__):
        nonlocal func, args, kwargs
        return func(*args, **kwargs)
    return f


def concat(*funcs):
    """Вспомогательная функция. При выполнении возвращаемой функции будут последовательно
    выполнены все функции, переданные в качестве аргумента. Аргументы в вызываемые функции
    ставиться не будут. (пользоваться perform)"""
    return lambda *_: [i() for i in funcs]


def load_image(name, chr_key=None) -> pg.Surface:
    """Загрузить изображение из папки data с указанным именем и конвертировать"""
    fullname = os.path.join('data', name)
    image = pg.image.load(fullname).convert()

    if chr_key is not None:
        if chr_key == -1:
            chr_key = image.get_at((0, 0))
        image.set_colorkey(chr_key)
    else:
        image = image.convert_alpha()
    return image


def load_data():
    """Загрузка всех файлов игры"""
    global IMG
    IMG["logo"] = load_image("logo.png", -1)
    IMG["empty"] = load_image("empty.png")
    IMG["wall"] = load_image("wall.png")
    IMG["player"] = load_image("player.png", -1)
    IMG["default"] = load_image("default.png", -1)
    IMG["button"] = load_image("button.png")
    IMG["door_open"] = load_image("door_open.png")
    IMG["door_closed"] = load_image("door_closed.png")
    IMG["cube"] = load_image("cube.png")
    IMG["cube_dispenser"] = load_image("cube_dispenser.png")
    IMG["pressure_button_activated"] = load_image("pressure_button_activated.png")
    IMG["pressure_button_deactivated"] = load_image("pressure_button_deactivated.png")
    IMG["fizzler"] = load_image("fizzler.png")
    IMG["info"] = load_image("info.png")
    IMG["exit"] = load_image("exit.png")


IMG = {}            # Словарь, содержащий загруженные изображения
level_main = None           # Будущий Объект GMain. Хранится для доступа без передачи в качестве аргумента
action_socket = {}  # Хранилище логических ячеек, нужен для указания того, может ли GAction выполниться сейчас


#  CONSTS --------------------
FIELD_SIZE = FIELD_WIDTH, FIELD_HEIGHT = 10, 10
CELL_SIZE = 50                          # Position = center
DEFAULT_IMAGE = "default"
# noinspection PyArgumentList
COLORS = {
    "background": pg.Color(1, 5, 14),
    "foreground": pg.Color(101, 105, 114),
}


# \CONSTS --------------------


class GMachine(metaclass=abc.ABCMeta):
    """
    Абстрактный класс игровой машины. Представлен следующей структурой:
        [START] -> ([HANDLE_INPUT] -> [MANAGE_CYCLE]) -> [QUIT].
    От него наследуются состояния игры (запущен уровень/находимся в меню/...).
    Также содержит приватные функции обёрток, для наследованных абстрактных классов под более
    целевые нужды"""
    def __start(self):
        self.start()

    @abc.abstractmethod
    def start(self):
        """Функция, которая запускается при старте. Не может никаким образом повлиять на запуск цикла"""
        pass

    def __quit(self):
        self.quit()

    @abc.abstractmethod
    def quit(self):
        """Функция, которая должна завершить работу программы."""
        pass

    def __handle_input(self):
        self.handle_input()

    @abc.abstractmethod
    def handle_input(self):
        """Функция, которая обрабатывает действия пользователя и вызывает необходимые функции."""
        pass

    def __manage_cycle(self):
        self.manage_cycle()

    @abc.abstractmethod
    def manage_cycle(self):
        """Функция, в которой должно происходить очищение очереди и обновление графики"""
        pass
    
    def main(self):
        """Запуск. В обычной машине эта функция прервет исполнение других машин, пока не завершится сама"""
        self.__start()
        self.exit_code = -1
        while self.exit_code == -1:
            self.__handle_input()
            self.__manage_cycle()
        self.__quit()
        return self.exit_code


class GPygameMachine(GMachine):
    """Адаптация класса игровой машины под pygame. Содержит те функции, которые обязательно будут в любом
    подклассе"""
    def __start(self):
        self.queue = []
        self.start()
        self.clock = pg.time.Clock()

    @abc.abstractmethod
    def start(self):
        pass

    def __quit(self):
        self.quit()

    @abc.abstractmethod
    def quit(self):
        pass

    def __handle_input(self):
        if pg.event.get(pg.QUIT):
            self.exit_code = 1
        self.handle_input()

    @abc.abstractmethod
    def handle_input(self):
        pass

    def __manage_cycle(self):
        _ = self.queue.copy()
        while len(_) > 0:
            # print(_)
            _.pop(0)()
            self.queue.pop(0)

        self.g_cycle += 1
        pg.display.flip()
        self.manage_cycle()
        self.clock.tick(60)

    @abc.abstractmethod
    def manage_cycle(self):
        pass

    def main(self):
        self.g_cycle = 0
        self.__start()
        self.exit_code = -1
        while self.exit_code == -1:
            self.__handle_input()
            self.__manage_cycle()
        self.__quit()
        return self.exit_code


class GTextPopup(GPygameMachine):
    """Класс окошка с текстом. Старается разделить текст на строки. При запуске прерывает
    прерывает ход других циклов, пока не остановится сам"""
    def __init__(self, surface: pg.Surface, text="", rect=pg.Rect(100, 100, 600, 400)):
        self.mes = self.split_text(text, 35)
        self.par = surface
        self.rect = rect

    @staticmethod
    def split_text(text, size):
        mes = []
        p = text[:size]
        while p:
            mes.append(p)
            text = text[size:]
            p = text[:size]
        return mes

    def start(self):
        pg.font.init()
        self.im = pg.font.SysFont("Consolas", 30)
        self.surface = pg.Surface(self.rect.size)

    def quit(self):
        pass

    def handle_input(self):
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                self.exit_code = 0

    def manage_cycle(self):
        pg.draw.rect(self.surface, COLORS["background"], (0, 0, *self.rect.size))
        pg.draw.rect(self.surface, COLORS["foreground"], (0, 0, *self.rect.size), 10)
        for i in range(len(self.mes)):
            self.surface.blit(self.im.render(self.mes[i], False, pg.Color("white")), (10, 10 + 30 * i))
        self.par.blit(self.surface, self.rect.topleft)


class GBrutalTextAnimation(GPygameMachine):
    """Лучшая анимация"""
    def __init__(self, surface: pg.Surface, font: pg.font.Font, text: str):
        self.im = font
        self.text = text
        self.surface = surface
        self.tr = 0

    def start(self):
        self.surface.set_alpha(0)

    def quit(self):
        pass

    def handle_input(self):
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                self.exit_code = 0

    def manage_cycle(self):
        pg.draw.rect(self.surface, pg.Color("black"), self.surface.get_rect())
        for i, line in enumerate(GTextPopup.split_text(self.text, 22)):
            self.surface.blit(self.im.render(line, False,
                                             (255 / 100 * self.tr,
                                              255 / 100 * self.tr,
                                              255 / 100 * self.tr)), (10, 100 + 60 * i))
        if self.g_cycle <= 100:
            self.tr = self.g_cycle
        elif 300 >= self.g_cycle >= 200:
            self.tr = 300 - self.g_cycle
        if self.g_cycle == 330:
            self.exit_code = 0


class GSprite(pg.sprite.Sprite):
    """Наследование класса спрайта. Создан, в основном, для удобства, а также решения проблемы
    нецелых координат"""
    def __init__(self, rectf=None, image=None, groups=()):
        super(GSprite, self).__init__(*groups)
        self.image = image if image is not None else IMG[DEFAULT_IMAGE]
        self.ident = str(randint(100, 100000000000))
        if rectf is None:
            self.rect = self.image.get_rect()
            self.rectf = [self.rect.x, self.rect.y, self.rect.w, self.rect.h]
        else:
            pg.transform.scale(self.image, rectf[2:4])
            self.rectf = rectf
        self.commit()

    def move(self, dx, dy):     # Передвинуть на dx dy
        self.rectf[0] += dx
        self.rectf[1] += dy
        self.commit()

    def stand(self, nx, ny):    # Поместить в nx ny
        self.rectf[0] = nx
        self.rectf[1] = ny
        self.commit()

    def scale(self, nw, nh, image_scale=False):     # Установить размер
        self.rectf[2] = nw
        self.rectf[3] = nh
        if image_scale:
            pg.transform.scale(self.image, (nw, nh))
        self.commit()

    def centerF(self):                  # Выдать координаты центра
        return self.rectf[0] + self.rectf[2] / 2, self.rectf[1] + self.rectf[3] / 2

    def center(self):                   # То же, что и centerF, только целые
        x, y = self.centerF()
        return int(x), int(y)

    def centrify(self, o):              # Центрирует переданный спрайт
        assert isinstance(o, GSprite)
        cx, cy = self.centerF()
        ow, oh = o.size()
        o.stand(cx - ow / 2, cy - oh / 2)

    def pos(self):
        return self.rectf[0], self.rectf[1]

    def x(self):
        return self.rectf[0]

    def y(self):
        return self.rectf[1]

    def size(self):
        return self.rectf[2], self.rectf[3]

    def w(self):
        return self.rectf[2]

    def h(self):
        return self.rectf[3]

    def commit(self):                               # Перевод нецелых координат в целые. Вызывается
        self.rect = pg.Rect(int(self.rectf[0]),     # после любого изменения объекта
                            int(self.rectf[1]),
                            int(self.rectf[2]),
                            int(self.rectf[3]))


class TextButton(GSprite):
    """Адаптация класса GSprite для хранения текста и функцию, которую он выполняет при активации.
    Некий аналог кнопки"""
    def __init__(self, action, rect=None, text="", *groups):
        super(TextButton, self).__init__(rect, None, groups)
        self.selected = False
        self.text = text
        self.act = action
        self.fnt = pg.font.SysFont("Arial", 20)

    def draw(self, surface: pg.Surface):
        th = self.fnt.render(self.text, False, pg.Color("white"))
        me = GSprite(image=th)
        self.centrify(me)
        pg.sprite.Group(me).draw(surface)


class GAction:
    """Класс запрограммированного действия. В зависимости от значения в action_socket
    может выполниться или нет. Если выполнился, то без изменения значения в ячейке более не запустится."""
    def __init__(self, socket_name: str, action):
        self.socket = socket_name
        if socket_name not in action_socket:
            action_socket[socket_name] = False
        assert callable(action)
        self.action = action

    def __call__(self, *args, **kwargs):
        """Вызов событий. Заполняет сокет, выполняет переданную функцию, возвращает результат"""
        if not action_socket[self.socket]:
            action_socket[self.socket] = True
            return self.action(*args, **kwargs)

    def socket_receive(self):
        """Очищение сокета. Без выполнения этого более событие с этим сокетом запустить будет нельзя"""
        action_socket[self.socket] = False

    exec = __call__


class GAnimation(GAction):
    """Класс анимации. Является долгосрочным вариантом GAction. Делает работу в течении
    dur циклов, после чего освобождает свой сокет. На каждом цикле вызывает функцию do.
    Сам цикл выполняется вместе с циклом машины, и будет помещаться в очередь, пока
    не пройдет dur циклов. При окончании вызывает функцию on_end.
    Сам по себе является абстрактным, и в коде в чистом виде быть не должен."""
    def __init__(self, dur: int, socket_name: str, on_end):
        super(GAnimation, self).__init__(socket_name, self.start)
        self.dur = dur
        self.time = 0
        self.on_end = on_end

    @abc.abstractmethod
    def do(self):
        pass

    def cycle(self):
        """Функция выполнения одного кадра анимации. Пока не прошло необходимое количество обновлений,
        будет добавлять себя в очередь текущего уровня. В конце очищает собственный сокет"""
        self.time += 1
        self.do()
        if self.time < self.dur:
            level_main.queue.append(self.cycle)
        else:
            action_socket[self.socket] = False
            self.on_end()

    def start(self):
        level_main.queue.append(self.cycle)


class GSpriteMoveAnimation(GAnimation):
    """Специализированный класс анимации для плавного передвижения спрайта target по экрану"""
    def __init__(self, target: GSprite, dx, dy, dur: int, on_end=lambda: None):
        super(GSpriteMoveAnimation, self).__init__(dur, "MOVE_ANIMATION-GS{}".format(str(target.ident)), on_end)
        self.tar = target
        self.dx = dx / dur
        self.dy = dy / dur

    def do(self):
        self.tar.move(self.dx, self.dy)


class GSpriteFadeAnimation(GAnimation):
    """Экспериментальный и непроверенный класс анимации плавного изменения изображения спрайта
    Не используется в основной версии, так как не работает"""
    def __init__(self, target: GSprite, new_image: pg.Surface, dur: int, on_end=lambda: None):
        super(GSpriteFadeAnimation, self).__init__(dur, "FADE_ANIMATION-GS{}".format(str(target.ident)), on_end)
        self.tar = target
        self.new = new_image
        self.src = self.tar.image
        self.new.set_alpha(0)
        self.st1 = target.image.get_alpha()
        self.dt1 = -self.st1 / dur
        self.st2 = 0
        self.dt2 = 100 / dur

    def do(self):
        self.st1 += self.dt1
        self.st2 += self.dt2
        self.src.set_alpha(int(self.st1))
        self.new.set_alpha(int(self.st2))
        im = self.src
        im.blit(self.new, special_flags=pg.BLEND_ADD)
        self.tar.image = im


class GCamera:
    """Класс камеры. По умолчанию наблюдает за игроком"""
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj: GSprite):
        """Передвигает переданный объект так, будто таргет находится в центре экрана, а
        объект сохранил положение относительно объекта"""
        obj.move(self.dx, self.dy)

    def update(self, target: GSprite, screen_size):
        """Меняет таргет"""
        x, y = target.pos()
        w, h = target.size()
        self.dx = -(x + w // 2 - screen_size[0] // 2)
        self.dy = -(y + h // 2 - screen_size[1] // 2)


class Cell(GSprite):
    """Класс клетки клетчатого поля. Является в некотором роде абстрактным и
    явно использоваться не должен. Имеет словарь свойств (используются игрой) и
    массив connect. Он используется для коммуникации м-у клетками. Для отправки сигнала
    всем клеткам используется send(), при получении вызывается check_activators(). Остальные
    функции вызываются игрой"""
    def __init__(self, image=None):
        super(Cell, self).__init__(image=image)
        self.params = {
            "walkable": True,
            "activatable": False,
            "takeables": [],
        }
        self.connect = []
        self.activators = []
        self.state = False
        self.field_pos = None

    def setup(self, field_pos):
        """Вызывается полем во время создания. Без выполнения этой функции клетка не будет реагировать"""
        field_pos: GLevel.FieldMatrix.MatrixPos
        self.field_pos = field_pos
        self.add(*self.field_pos.owner().mt_groups)

    def check_activators(self):
        if all(map(lambda c: c.state, self.activators)):
            self.on_positive()
        else:
            self.on_negative()

    def send(self):
        for c in self.connect:
            c.check_activators()

    def on_stand(self):
        """Событие. Когда игрок встает на клетку"""
        pass

    def on_leave(self):
        """Событие. Когда игрок покидает клетку"""
        pass

    def on_cube_set(self):
        """Событие. Когда игрок ставит на клетку предмет"""
        pass

    def on_cube_take(self):
        """Событие. Когда игрок убирает предет с клетки"""
        pass

    def on_activation(self):
        """Событие. Когда игрок нажал "Е", находясь на клетке"""
        pass

    def on_positive(self):
        """Получение сигнала +"""
        pass

    def on_negative(self):
        """Получение сигнала -"""
        pass


def GetCell(char: str, *args):
    """Функция перекодировки символа в класс клетки. Используется при чтении и интерпретации файла уровня
    в текстовом виде"""
    return {
        " ": perform(EmptyCell),
        "*": perform(WallCell),
        "B": perform(EButtonCell),
        "d": perform(DoorCell, False),
        "D": perform(DoorCell, True),
        "C": perform(CubeDispenserCell),
        "_": perform(PressureButtonCell),
        "F": perform(FizzlerCell, True),
        "f": perform(FizzlerCell, False),
        "I": perform(InfoCell),
        "!": perform(ExitCell)
    }[char]()


class EmptyCell(Cell):      # Класс пустой клетки (по ней можно ходить)
    def __init__(self):
        super(EmptyCell, self).__init__(IMG["empty"])


class WallCell(Cell):       # Класс клетки стены (в этой версии она цвета фона)
    def __init__(self):
        super(WallCell, self).__init__(IMG["default"])
        self.params["walkable"] = False


class EButtonCell(Cell):    # Класс клетки, встав на которую и нажав английскую E что-то произойдет
    def __init__(self):
        super(EButtonCell, self).__init__(IMG["button"])
        self.params["activatable"] = True

    def on_activation(self):
        self.state = not self.state
        self.send()


class DoorCell(Cell):       # Класс клетки двери, которая меняет свое состояние при получении сигнала
    def __init__(self, closed=True):
        self.default = closed
        if closed:
            super(DoorCell, self).__init__(IMG["door_closed"])
        else:
            super(DoorCell, self).__init__(IMG["door_open"])
        self.params["walkable"] = not self.default

    def on_positive(self):
        self.state = not self.default
        self.params["walkable"] = not self.state
        if self.state:
            self.image = IMG["door_closed"]
        else:
            self.image = IMG["door_open"]

    def on_negative(self):
        self.state = self.default
        self.params["walkable"] = not self.state
        if self.state:
            self.image = IMG["door_closed"]
        else:
            self.image = IMG["door_open"]


class DispenserCell(Cell):          # Класс клетки раздатчика. Абстрактен сам по себе
    def __init__(self, takeable, auto_new=True, auto_first=True, image=None):
        assert isinstance(takeable, Takeable)
        super(DispenserCell, self).__init__(image)
        takeable.on_death = concat(takeable.on_death, self.on_item_death)
        self.item = takeable
        self.auto_new = auto_new
        self.auto_first = auto_first

    def create_new(self):
        """Вызывается для создания нового объекта. Если объект будет "жив", то выкинет исключение"""
        self.item.create(self.field_pos)

    def on_item_death(self):
        """Событие клетки, срабатывает, когда предмет уничтожается"""
        pass


class CubeDispenserCell(DispenserCell):     # Раздатчик кубика. При положительном сигнале попытается создать куб
    def __init__(self, auto_new_cube=True, auto_first_cube=True):
        super(CubeDispenserCell, self).__init__(Cube((level_main.all_sprites, level_main.takeable_group)),
                                                auto_new=auto_new_cube,
                                                auto_first=auto_first_cube,
                                                image=IMG["cube_dispenser"])

    def on_positive(self):
        if self.item.alive():
            self.item.die()
        self.item.create(self.field_pos)

    def on_negative(self):
        self.on_positive()

    def on_item_death(self):
        if self.auto_new:
            self.on_positive()


class PressureButtonCell(Cell):     # Нажимная клетка. Посылает + если на ней стоит игрок или предмет
    def __init__(self):
        super(PressureButtonCell, self).__init__(IMG["pressure_button_deactivated"])
        self.standing = False
        self.takeable_lying = False

    def on_stand(self):
        self.standing = True
        self.check()

    def on_leave(self):
        self.standing = False
        self.check()

    def on_cube_set(self):
        self.takeable_lying = True
        self.check()

    def on_cube_take(self):
        self.takeable_lying = False
        self.check()

    def check(self):        # Проверка того, лежит ли что-нибудь на клетке
        if self.standing or self.takeable_lying:
            self.image = IMG["pressure_button_activated"]
            self.state = True
        else:
            self.image = IMG["pressure_button_deactivated"]
            self.state = False
        self.send()


class FizzlerCell(Cell):    # Рассеиватель. Если предмет "попадает" на клетку, то он уничтожается.
    def __init__(self, active=True):
        super(FizzlerCell, self).__init__(IMG["fizzler"])
        self.state = self.default = active

    def on_stand(self):
        if self.state and level_main.player.hold is not None:
            level_main.player.release().die()

    def on_positive(self):
        self.state = not self.default
        if self.state:
            self.image = IMG["fizzler"]
        else:
            self.image = IMG["door_open"]

    def on_negative(self):
        self.state = self.default
        if self.state:
            self.image = IMG["fizzler"]
        else:
            self.image = IMG["door_open"]


class InfoCell(Cell):       # Информационная клетка. Содержит всякий текст
    def __init__(self):
        super(InfoCell, self).__init__(IMG["info"])
        self.text = ""
        self.params["activatable"] = True

    def on_activation(self):
        it = GTextPopup(level_main.screen, self.text)
        if it.main() == 1:
            level_main.exit_code = 1
        pass


class ExitCell(Cell):       # Когда на клетку наступает игрок, он покидает уровень
    def __init__(self):
        super(ExitCell, self).__init__(IMG["exit"])

    def on_stand(self):
        level_main.exit_code = -1000    # that means you won
        if "PLAYER_WALK" in action_socket:
            action_socket["PLAYER_WALK"] = False


class Takeable(GSprite):
    """Класс подбираемого предмета. Сам по себе абстрактный, в чистом виде быть не должен."""
    def __init__(self, image=None, groups=()):
        super(Takeable, self).__init__(image=image, groups=groups)
        self.kill()
        self.field_pos = None

    def create(self, field_pos):
        """Создание предмета. Будет находиться на позиции, переданной в аргументе,
        визуально - на соответствующей клетке"""
        assert isinstance(field_pos, FieldPos)
        self.add(level_main.takeable_group)
        self.field_pos = field_pos
        self.stand(self.field_pos.get().x() + randint(0, self.field_pos.get().w() - self.w()),
                   self.field_pos.get().y() + randint(0, self.field_pos.get().h() - self.h()))
        self.image.set_alpha(255)
        field_pos.get().params["takeables"].append(self)
        self.on_create()

    def clone(self):
        return Takeable(self.image, self.groups())

    def take(self):
        """Подбирания игроком предмета. Если игрок уже что-то держит, то выбрасывается исключение.
        На самом деле предмет просто исчезает с поля. К нему все еще можно актуально обратиться по классу"""
        global level_main
        if level_main.player.hold is not None:
            raise Exception("Trying to take a Takeable while holding another Takeable")
        level_main.player.hold = self
        self.field_pos.get().params["takeables"].remove(self)
        level_main.player.centrify(self)
        level_main.takeable_group.remove(self)
        level_main.player_group.add(self)
        self.field_pos.get().on_cube_take()
        self.on_take()

    def die(self):
        """Уничтожает предмет. Важно, что если игрок его держит, то возникнет ошибка"""
        if level_main.player.hold == self:
            raise Exception("Trying to kill Takeable while player holding it")
        else:
            self.field_pos.get().params["takeables"].remove(self)
            self.image.set_alpha(0)
            self.field_pos.get().on_cube_take()
            self.field_pos = None
            self.kill()
            self.on_death()

    def on_take(self):
        """Событие. При подбирании предмета"""
        pass

    def on_release(self):
        """Событие. При опускании предмета"""
        pass

    def on_death(self):
        """Событие. При уничтожении объекта"""
        pass

    def on_create(self):
        """Событие. При создании объекта"""
        pass


class Cube(Takeable):       # Кубик. Внешне тоже кубик
    def __init__(self, groups=()):
        super(Cube, self).__init__(IMG["cube"], groups=groups)


class GLevel(GSprite):
    """Класс игрвого клетчатого поля и уровня. Реализует расстановку клеток, также вычислению
    абсолютной позиции предмета в клетке, также генерацию уровня из текстового файла
    """
    def __init__(self, level_name, start_pos, matrix=None, groups=()):
        super(GLevel, self).__init__(rectf=None, image=None, groups=groups)
        self.name = level_name
        self.start_pos = start_pos
        self.mt_groups = groups
        if matrix is None:
            log("Init without matrix", "__init__", "field")
            self.mt = self.FieldMatrix(self, [[EmptyCell() for i in range(FIELD_WIDTH)]
                                              for k in range(FIELD_HEIGHT)])
            log("Matrix creation ended.", "__init__", "field")
        else:
            log("Init with matrix", "__init__", "field")
            if isinstance(matrix, self.FieldMatrix):
                self.mt = matrix
            else:
                self.mt = self.FieldMatrix(self, matrix)
            for pos in self.mt:
                pos.get().image = pg.transform.scale(pos.get().image, (CELL_SIZE, CELL_SIZE))
                pos.get().setup(pos)
            log("Matrix check and transform ended.", "__init__", "field")

        self.size = self.width, self.height = self.mt.size()
        self.scale(self.width * CELL_SIZE, self.height * CELL_SIZE)

    class FieldMatrix:
        """Класс матрицы. Используется для упрощения доступа к клеткам и минимизации количества аргументов"""
        def __init__(self, field, _list: list):
            self._field = field
            self._items = _list
            if len(_list) == 0 or len(_list[0]) == 0:
                raise AttributeError("Invalid matrix size")

        class MatrixPos:
            """Класс позиции в матрице. Содержит также информацию об уровне, который содержит эту позицию"""
            def __init__(self, field, *p):
                assert isinstance(field, GLevel)
                self._field = field
                self._mt = field.mt
                try:
                    assert len(p) == 1 or len(p) == 2
                    if len(p) == 1:
                        assert isinstance(p[0], tuple)
                        self._r, self._c = p[0][0], p[0][1]
                    elif len(p) == 2:
                        assert isinstance(p[0], int)
                        assert isinstance(p[1], int)
                        self._r, self._c = p[0], p[1]
                except AssertionError:
                    raise AttributeError("Wrong count or type of arguments")

            def get(self) -> Cell:      # Вернуть предмет по своей позиции
                return self._mt[self._r, self._c]

            def set(self, value: Cell):     # Установить предмет на своей позиции
                self._mt[self._r, self._c] = value

            def change(self, dr: int, dc: int):     # Передвинуть позицию
                self._r += dr
                self._c += dc
                if not (0 <= self._r < self._mt.row_count() and 0 <= self._c < self._mt.column_count()):
                    raise IndexError("Matrix indexes out of range!")

            def stand(self, nr: int, nc: int):      # Установить позицию
                self._r = nr
                self._c = nc
                if not (0 <= self._r < self._mt.row_count() and 0 <= self._c < self._mt.column_count()):
                    raise IndexError("Matrix indexes out of range!")

            def pos(self):
                return self._r, self._c

            def copy(self):
                return self.__class__(self._field, self.pos())

            def r(self):
                return self._r

            def c(self):
                return self._c

            def owner(self):
                return self._field

            def __str__(self):
                return f"{self._r}, {self._c}"

            def __repr__(self):
                return self.__str__()

        def __getitem__(self, item) -> Cell:
            if isinstance(item, tuple):
                return self._items[item[0]][item[1]]
            elif isinstance(item, self.MatrixPos):
                return item.get()
            else:
                raise KeyError("Key type must be tuple or FieldPos object")

        def __setitem__(self, key, value: Cell):
            if isinstance(key, tuple):
                self._items[key[0]][key[1]] = value
            elif isinstance(key, self.MatrixPos):
                key.set(value)
            else:
                raise KeyError("Key type must be tuple or FieldPos object")

        def row_count(self):
            return len(self._items)

        def column_count(self):
            return len(self._items[0])

        def size(self):
            return self.row_count(), self.column_count()

        def __iter__(self):
            """Возвращает итератор на клетки матрицы по порядку. Все клетки в матрице будут пройдены"""
            return iter([self.MatrixPos(self._field, (i, k))
                         for i in range(self.row_count())
                         for k in range(self.column_count())])

        def __str__(self):
            return ", \n".join(["[" + ", ".join(map(str, i)) + "]" for i in self._items])

        def __repr__(self):
            return str(self)

    def FieldPos(self, r, c):       # Быстрая ссылка на класс позиции в матрице
        return self.FieldMatrix.MatrixPos(self, (r, c))

    def set_view(self, pos):        # Передвижение своего спрайта в позицию
        log("Replacing my view...", "set_view", "field")
        self.stand(*pos)

    def draw_cells(self):
        for pos in self.mt:
            pos.get().stand(*self.place(pos.pos()))
        # for r, row in enumerate(self.mt):
        #     for c, item in enumerate(row):
        #         item.stand(*self.place((c, r)))

    def place(self, point):         # Возвращает абсолютную позицию по позиции в матрице
        x, y = self.pos()
        return x + point[1] * CELL_SIZE, y + point[0] * CELL_SIZE

    @staticmethod
    def Load(path_to_folder, *groups):
        """Интерпретирует текстовый вид уровня в сам уровень с помощью имеющегося синтаксиса
        TODO документация по синтаксису"""
        map_file = os.path.join(path_to_folder, "map.txt")
        meta_file = os.path.join(path_to_folder, "meta.json")
        with open(map_file, "r") as fmap, open(meta_file, "r") as fmeta:
            data_map = fmap.read().split("\n")
            meta_data = json.loads(fmeta.read(), encoding="UTF-16")
            name = meta_data["name"]
            st_pos = map(int, meta_data["start_pos"].split(","))
            mt = [[GetCell(c) for c in row] for row in data_map]
            for start, end in meta_data["connections"].items():
                start = list(map(int, start.split(",")))
                end = [tuple(map(int, i.split(","))) for i in end]
                for p in end:
                    mt[start[0]][start[1]].connect.append(mt[p[0]][p[1]])
                    mt[p[0]][p[1]].activators.append(mt[start[0]][start[1]])
            for p, mes in meta_data["info_text"].items():
                p = list(map(int, p.split(",")))
                assert isinstance(mt[p[0]][p[1]], InfoCell)
                mt[p[0]][p[1]].text = mes

        return GLevel(name, st_pos, mt, *groups)


FieldPos = GLevel.FieldMatrix.MatrixPos


class Player(GSprite):
    """Класс игрока, как объекта, наделенного способностью красиво (анимированно) ходить по полю"""
    def __init__(self, field_pos: FieldPos, *groups):
        super(Player, self).__init__(rectf=[0, 0, CELL_SIZE, CELL_SIZE], image=IMG["player"], groups=groups)
        self.field = field_pos.owner()
        self.field_pos = field_pos
        self.hold = None

    def change_cell(self, dr, dc):
        r, c = self.field_pos.pos()
        nr = r + dr
        nc = c + dc
        nx, ny = self.field.place((nr, nc))
        if self.field.mt[nr, nc].params["walkable"]:
            act = GAction("PLAYER_WALK".format(str(nr), str(nc)), lambda: None)
            # Создается экземпляр GAction с пустой функцией
            act.action = concat(GSpriteMoveAnimation(self, nx - self.pos()[0], ny - self.pos()[1],
                                                     5, on_end=act.socket_receive).exec,
                                perform(self.set_field_pos, nr, nc))
            # Пустая функция заменяется на:
            #   1) Запустить анимацию, после окончания очистить сокет "PLAYER_WALK"
            #   2) Сменить фактическое положение персонажа на клетчатом поле
            act.exec()

    def set_field_pos(self, nr, nc):    # Присвоение позиции на поле, с прожатием сигналов комнат
        self.field_pos.get().on_leave()
        self.field_pos.stand(nr, nc)
        self.field_pos.get().on_stand()

    def release(self) -> Takeable:      # Выкинуть предмет, который держит.
        if self.hold is None:
            raise Exception("Trying to release object while nothing is holding")
        self.field_pos.get().params["takeables"].append(self.hold)
        self.hold.field_pos = self.field_pos.copy()
        self.hold.stand(self.field_pos.get().x() + randint(0, self.field_pos.get().w() - self.hold.w()),
                        self.field_pos.get().y() + randint(0, self.field_pos.get().h() - self.hold.h()))

        level_main.takeable_group.add(self.hold)
        level_main.player_group.remove(self.hold)
        _ = self.hold
        self.hold = None
        self.field_pos.get().on_cube_set()
        if len(self.field_pos.get().params["takeables"]) > 2:
            log("too many takeables at once", "change_cell", "WARNING")
        return _


class GLevelExec(GPygameMachine):
    """Класс Main, занимающийся исполнением уровней. Пока игра содержит лишь один уровень
    - вызывается по умолчанию. Содержит очередь функций, счетчик цикла, а также группы спрайтов"""
    def __init__(self, screen, level_folder, *args):
        self.file = level_folder
        self.screen = screen
        self.args = args

    class Pause(GPygameMachine):
        """Класс машины, которая запускается, имитируя "Паузу" в игре."""
        def __init__(self, screen: pg.Surface):
            self.screen = screen

        def start(self):
            self.bg = pg.display.get_surface().copy()
            self.bg.set_alpha(128)
            it = pg.Surface(self.screen.get_size(), flags=pg.SRCALPHA)
            it.fill((0, 0, 0, 192))
            self.bg.blit(it, (0, 0))

            self.txt = TextButton(lambda: None, (350, 100, 100, 60), "Пауза")
            self.bns = [
                TextButton(self.continue_, [300, 300, 200, 40], "Продолжить"),
                TextButton(self.retry_, [300, 350, 200, 40], "Перезапуск"),
                TextButton(self.exit_, [300, 400, 200, 40], "Выйти"),
            ]
            self.sel = 0

        def continue_(self):
            self.exit_code = 0

        def retry_(self):
            self.exit_code = 1000

        def exit_(self):
            self.exit_code = -2000

        def quit(self):
            pass

        def handle_input(self):
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.continue_()
                    elif event.key == pg.K_UP and self.sel > 0:
                        self.sel -= 1
                    elif event.key == pg.K_DOWN and self.sel < len(self.bns) - 1:
                        self.sel += 1
                    elif event.key == pg.K_RETURN:
                        self.bns[self.sel].act()

        def manage_cycle(self):
            self.screen.blit(self.bg, (0, 0))
            self.txt.draw(self.screen)
            for i in self.bns:
                i.draw(self.screen)
            pg.draw.rect(self.screen, COLORS["foreground"], self.bns[self.sel].rect, 1)

    def start(self):
        log("Started starting up...", "Start machine", "main")
        self.exit_code = 0
        self.queue = []
        self.all_sprites = pg.sprite.Group()
        self.player_group = pg.sprite.Group()
        self.cell_group = pg.sprite.Group()
        self.takeable_group = pg.sprite.Group()

        self.window_size = self.window_width, self.window_height = self.screen.get_rect().size

        # self.screen = pg.display.set_mode(self.window_size, pg.FULLSCREEN)

        self.field = GLevel.Load(self.file,
                                 (self.all_sprites, self.cell_group))
        self.field.set_view(((self.window_width - CELL_SIZE * self.field.width) // 2,
                             (self.window_height - CELL_SIZE * self.field.height) // 2))
        self.camera = GCamera()
        self.on_screen = pg.sprite.Group()
        self.player = Player(self.field.FieldPos(*self.field.start_pos), self.all_sprites, self.player_group)
        self.player.stand(*self.field.place((self.player.field_pos.r(), self.player.field_pos.c())))

        log("Successfully started up", "Start machine", "main")

    def quit(self):
        log("Started quiting...", "Quit machine", "main")
        # pg.quit()
        log("Successfully quited", "Quit machine", "main")

    def handle_input(self):
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                log(event)
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.player.change_cell(-1, 0)
                elif event.key == pg.K_LEFT:
                    self.player.change_cell(0, -1)
                elif event.key == pg.K_DOWN:
                    self.player.change_cell(1, 0)
                elif event.key == pg.K_RIGHT:
                    self.player.change_cell(0, 1)
                elif event.key == pg.K_e:
                    if self.player.hold is not None:
                        self.player.release()
                    elif self.player.field_pos.get().params["takeables"]:
                        self.player.field_pos.get().params["takeables"][0].take()
                    elif self.player.hold is None:
                        r, c = self.player.field_pos.pos()
                        self.field.mt[int(r), int(c)].on_activation()
                elif event.key == pg.K_ESCAPE:
                    it = self.Pause(self.screen)
                    ex = it.main()
                    if ex != 0:
                        self.exit_code = ex

    def manage_cycle(self):
        pg.draw.rect(self.screen, COLORS["background"], pg.Rect(0, 0, self.window_width, self.window_height))
        self.camera.update(self.player, self.window_size)
        self.camera.apply(self.player)
        self.camera.apply(self.field)
        for i in self.takeable_group:
            self.camera.apply(i)
        self.field.draw_cells()
        # self.all_sprites.draw(self.screen)
        self.cell_group.draw(self.screen)
        self.takeable_group.draw(self.screen)
        self.player_group.draw(self.screen)


class GMain(GPygameMachine):
    """Основной класс. Из него происходит запуск всего, что считается нужным"""
    def __init__(self, *args):
        self.args = args
        self.lvl = 0

    def bn_continue(self):
        """Продолжение игры. При выходе прогресс сбрасывается TODO сохраняется"""
        self.exec_level()

    def bn_new(self):
        self.lvl = 0
        self.exec_level()

    def bn_demo(self):
        self.lvl = 0
        self.lvls = [
            GLevelExec(self.screen, os.path.join("data", "lvls", "demo"))
        ]
        self.exec_level()

    def exec_level(self):
        """Запуск уровня."""
        global level_main
        level_main = self.lvls[self.lvl]
        ex = level_main.main()
        level_main = None
        if ex == 1:
            self.exit_code = 1
        elif ex == -1000:
            if self.lvl < len(self.lvls) - 1:
                self.lvl += 1
                self.save()
                self.exec_level()
            else:
                self.won()
        elif ex == 1000:
            self.exec_level()

    def won(self):
        th = GTextPopup(self.screen, "CONGRATULATIONS!!!!GG!!!")
        th.main()
        self.lvl = 0
        self.exit_code = 0

    def bn_exit(self):
        self.exit_code = 0

    def start(self):
        try:
            with open(os.path.join("user_files", "save_file.ini"), "r") as f:
                self.lvl = int(f.read())
        except IOError:
            log("no save_file.ini found", "start", "main")
            self.lvl = 0
        pg.init()
        pg.font.init()
        pg.mouse.set_visible(False)
        self.screen_size = self.screen_width, self.screen_height = 800, 600
        self.screen = pg.display.set_mode(self.screen_size)
        self.lvls = [
            GLevelExec(self.screen, os.path.join("data", "lvls", "1")),
            GLevelExec(self.screen, os.path.join("data", "lvls", "2")),
            GLevelExec(self.screen, os.path.join("data", "lvls", "3")),
            GLevelExec(self.screen, os.path.join("data", "lvls", "4")),
        ]
        load_data()
        self.start_animation = GBrutalTextAnimation(self.screen,
                                                    pg.font.SysFont("Comic Sans MS", 60),
                                                    "This game was made by Ilya Latypov (gang)")
        self.act = GAction("START_ANIMATION", self.start_animation.main)
        self.logo = GSprite(image=IMG["logo"])
        self.logo.stand(50, 50)
        self.on_screen = pg.sprite.Group(self.logo)
        if self.lvl > 0:
            self.bns = [
                TextButton(self.bn_continue, [10, 300, 780, 40], "Продолжить"),
            ]
        else:
            self.bns = []
        self.bns += [
            TextButton(self.bn_new, [10, 350, 780, 40], "Новая игра"),
            TextButton(self.bn_demo, [10, 400, 780, 40], "Демо"),
            TextButton(self.bn_exit, [10, 450, 780, 40], "Выход")
        ]
        self.sel = 0

        def anim_start():
            nonlocal self
            if self.act.exec() == 1:
                self.exit_code = 1

        self.queue.append(anim_start)

    def handle_input(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.exit_code = 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP and self.sel > 0:
                    self.sel -= 1
                elif event.key == pg.K_DOWN and self.sel < len(self.bns) - 1:
                    self.sel += 1
                elif event.key == pg.K_RETURN:
                    self.bns[self.sel].act()

    def manage_cycle(self):
        global level_main
        pg.draw.rect(self.screen, COLORS["background"], self.screen.get_rect())
        for b in self.bns:
            b.draw(self.screen)
        self.on_screen.draw(self.screen)
        pg.draw.rect(self.screen, COLORS["foreground"], self.bns[self.sel].rect, 1)

    def save(self):
        with open(os.path.join("user_files", "save_file.ini"), "w") as f:
            f.write(str(self.lvl))

    def quit(self):
        pg.quit()
        pg.font.quit()
        self.save()


def log(mes, sender=None, father=None, say=print):
    """Функция логирования сообщений в консоль"""
    if father is not None:
        if sender is None:
            sender = str(father).upper()
        else:
            sender = "{}/{}".format(str(father).upper(), str(sender))
    if sender is not None:
        mes = "[{}] ".format(str(sender)) + mes
    say(mes)


def main(*args):
    global level_main
    m = GMain(*args)
    # me = GLevelExec("data/map.txt", *args)
    return m.main()


if __name__ == "__main__":
    import sys
    sys.exit(main(*sys.argv))
