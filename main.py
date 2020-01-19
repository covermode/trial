# ----------------------------- Autor: Ilya Latypov ---------------------------
# +++          TRIAL. pygame project
#

import pygame as pg
import os
import abc
from random import randint


# DAY1:     Created base, don't tested.
# DAY2:     Manage drawing, start working on UserInput, make player
# DAY3:     Make animation_class, start working on a float-pos problem
# DAY4:     Solve a float-pos problem, add screen motion, make stable build of preview
# DAY5:     Create a cube.
# DAY6: ----chilling
# DAY7:     Make a info cell and exit cell.
# DAY8:TODO Make levels


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
me = None           # Будущий Объект GMain. Хранится для доступа без передачи в качестве аргумента
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
    От него наследуются состояния игры (запущен уровень/находимся в меню/...)"""
    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def quit(self):
        pass

    @abc.abstractmethod
    def handle_input(self):
        """Функция, которая обрабатывает действия пользователя и вызывает необходимые функции."""
        pass

    @abc.abstractmethod
    def manage_cycle(self):
        """Функция, которая очищает очередь и обновляет графику."""
        pass
    
    def main(self):
        self.start()
        self.exit_code = -1
        while self.exit_code == -1:
            self.handle_input()
            self.manage_cycle()
        self.quit()
        return self.exit_code


class GPygameMachine(GMachine):
    def events(self):
        evs = pg.event.get()
        for i in evs:
            if i.type == pg.QUIT:
                self.exit_code = 1
        return evs

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def quit(self):
        pass

    @abc.abstractmethod
    def handle_input(self):
        pass

    @abc.abstractmethod
    def manage_cycle(self):
        pass


class GTextPopup(GPygameMachine):
    def __init__(self, surface: pg.Surface, text="", rect=pg.Rect(100, 100, 800, 600)):
        self.mes = text
        self.par = surface
        self.rect = rect

    def start(self):
        pg.font.init()
        self.im = pg.font.SysFont("Consolas", 30)
        self.surface = pg.Surface(self.rect.size)

    def quit(self):
        pass

    def handle_input(self):
        for event in self.events():
            if event.type == pg.KEYDOWN:
                self.exit_code = 0

    def manage_cycle(self):
        pg.draw.rect(self.surface, COLORS["background"], (0, 0, *self.rect.size))
        pg.draw.rect(self.surface, COLORS["foreground"], (0, 0, *self.rect.size), 10)
        self.surface.blit(self.im.render(self.mes, False, pg.Color("white")), (10, 10))
        self.par.blit(self.surface, self.rect.topleft)
        pg.display.flip()


class GSprite(pg.sprite.Sprite):
    """Наследование класса спрайта. Создан, в основном, для удобства, а также решения проблемы
    нецелых координат"""
    def __init__(self, rectf=None, image=None, groups=()):
        super(GSprite, self).__init__(*groups)
        self.image = image if image is not None else IMG[DEFAULT_IMAGE]
        self.ident = str(randint(100, 100000000000))
        if rectf is None:
            self.rectf = self.image.get_rect()
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

    def centerF(self):
        return self.rectf[0] + self.rectf[2] / 2, self.rectf[1] + self.rectf[3] / 2

    def center(self):
        x, y = self.centerF()
        return int(x), int(y)

    def centrify(self, o):
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
        if not action_socket[self.socket]:
            action_socket[self.socket] = True
            self.action(*args, **kwargs)

    def socket_receive(self):
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
        self.time += 1
        self.do()
        if self.time < self.dur:
            me.queue.append(self.cycle)
        else:
            action_socket[self.socket] = False
            self.on_end()

    def start(self):
        me.queue.append(self.cycle)


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
    """Экспериментальный и непроверенный класс анимации плавного изменения изображения спрайта"""
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
        obj.move(self.dx, self.dy)

    def update(self, target: GSprite, screen_size):
        x, y = target.pos()
        w, h = target.size()
        self.dx = -(x + w // 2 - screen_size[0] // 2)
        self.dy = -(y + h // 2 - screen_size[1] // 2)


class Cell(GSprite):
    """Класс клетки клетчатого поля. Является в некотором роде абстрактным и
    явно использоваться не должен. Имеет словарь свойств (используются игрой) и
    массив connect. Он используется для коммуникации м-у клетками. Для отправки сигнала
    всем клеткам используется send(), при получении вызывается receive(). Остальные
    функции вызываются игрой"""
    def __init__(self, image=None):
        super(Cell, self).__init__(image=image)
        self.params = {
            "walkable": True,
            "activatable": False,
            "takeables": [],
        }
        self.connect = []
        self.state = 0
        self.field_pos = None

    def setup(self, field_pos):
        field_pos: Field.FieldMatrix.MatrixPos
        self.field_pos = field_pos
        self.add(*self.field_pos.owner().mt_groups)

    def send(self, positive=True):
        for c in self.connect:
            if positive:
                c.on_positive_receive()
            else:
                c.on_negative_receive()

    def on_stand(self):
        pass

    def on_leave(self):
        pass

    def on_cube_set(self):
        pass

    def on_cube_take(self):
        pass

    def on_activation(self):
        pass

    def on_positive_receive(self):
        pass

    def on_negative_receive(self):
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
        "F": perform(FizzlerCell),
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
        self.send(True)


class DoorCell(Cell):       # Класс клетки двери, которая меняет свое состояние при получении сигнала
    def __init__(self, closed=True):
        if closed:
            super(DoorCell, self).__init__(IMG["door_closed"])
        else:
            super(DoorCell, self).__init__(IMG["door_open"])
        self.params["walkable"] = False
        self.state = True

    def on_positive_receive(self):
        self.state = False
        self.params["walkable"] = True
        self.image = IMG["door_open"]

    def on_negative_receive(self):
        self.state = True
        self.params["walkable"] = False
        self.image = IMG["door_closed"]


class DispenserCell(Cell):
    def __init__(self, takeable, auto_new=True, auto_first=True, image=None):
        assert isinstance(takeable, Takeable)
        super(DispenserCell, self).__init__(image)
        takeable.on_death = concat(takeable.on_death, self.on_item_death)
        self.item = takeable
        self.auto_new = auto_new
        self.auto_first = auto_first

    def create_new(self):
        self.item.create(self.field_pos)

    def on_item_death(self):
        pass


class CubeDispenserCell(DispenserCell):
    def __init__(self, auto_new_cube=True, auto_first_cube=True):
        super(CubeDispenserCell, self).__init__(Cube((me.all_sprites, me.takeable_group)),
                                                auto_new=auto_new_cube,
                                                auto_first=auto_first_cube,
                                                image=IMG["cube_dispenser"])
        self.act = GAction("CUBE_DISPENSER_{}".format(self.ident), self.create_new)

    def on_positive_receive(self):
        self.act.exec()

    def on_item_death(self):
        self.act.socket_receive()
        if self.auto_new:
            self.on_positive_receive()


class PressureButtonCell(Cell):
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

    def check(self):
        if self.standing or self.takeable_lying:
            self.image = IMG["pressure_button_activated"]
            self.send(True)
        else:
            self.image = IMG["pressure_button_deactivated"]
            self.send(False)


class FizzlerCell(Cell):
    def __init__(self):
        super(FizzlerCell, self).__init__(IMG["fizzler"])
        self.state = True

    def on_stand(self):
        if self.state and me.player.hold is not None:
            me.player.release().die()

    def on_positive_receive(self):
        self.state = False
        self.image = IMG["door_open"]

    def on_negative_receive(self):
        self.state = True
        self.image = IMG["fizzler"]


class InfoCell(Cell):
    def __init__(self):
        super(InfoCell, self).__init__(IMG["info"])
        self.text = ""
        self.params["activatable"] = True

    def on_activation(self):
        it = GTextPopup(me.screen, self.text)
        if it.main() == 1:
            me.exit_code = 1
        pass


class ExitCell(Cell):
    def __init__(self):
        super(ExitCell, self).__init__(IMG["exit"])

    def on_stand(self):
        me.exit_code = 0


class Takeable(GSprite):
    def __init__(self, image=None, groups=()):
        super(Takeable, self).__init__(image=image, groups=groups)
        self.kill()
        self.field_pos = None

    def create(self, field_pos):
        assert isinstance(field_pos, FieldPos)
        self.add(me.takeable_group)
        self.field_pos = field_pos
        self.stand(self.field_pos.get().x() + randint(0, self.field_pos.get().w() - self.w()),
                   self.field_pos.get().y() + randint(0, self.field_pos.get().h() - self.h()))
        self.image.set_alpha(255)
        field_pos.get().params["takeables"].append(self)
        self.on_create()

    def clone(self):
        return Takeable(self.image, self.groups())

    def take(self):
        global me
        if me.player.hold is not None:
            raise Exception("Trying to take a Takeable while holding another Takeable")
        me.player.hold = self
        self.field_pos.get().params["takeables"].remove(self)
        me.player.centrify(self)
        me.takeable_group.remove(self)
        me.player_group.add(self)
        self.field_pos.get().on_cube_take()
        self.on_take()

    def die(self):
        if me.player.hold == self:
            raise Exception("Trying to kill Takeable while player holding it")
        else:
            self.field_pos.get().params["takeables"].remove(self)
            self.image.set_alpha(0)
            self.field_pos = None
            self.kill()
            self.on_death()

    def on_take(self):
        pass

    def on_release(self):
        pass

    def on_positive_receive(self):
        pass

    def on_negative_receive(self):
        pass

    def on_death(self):
        pass

    def on_create(self):
        pass


class Cube(Takeable):
    def __init__(self, groups=()):
        super(Cube, self).__init__(IMG["cube"], groups=groups)


class Field(GSprite):
    """Класс игрвого клетчатого поля. Реализует расстановку клеток, также вычислению
    абсолютной позиции предмета в клетке, также генерацию уровня из текстового файла
    """
    def __init__(self, matrix=None, groups=()):
        super(Field, self).__init__(rectf=None, image=None, groups=groups)
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
        def __init__(self, field, _list: list):
            self._field = field
            self._items = _list
            if len(_list) == 0 or len(_list[0]) == 0:
                raise AttributeError("Invalid matrix size")

        class MatrixPos:
            def __init__(self, field, *p):
                assert isinstance(field, Field)
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

            def get(self) -> Cell:
                return self._mt[self._r, self._c]

            def set(self, value: Cell):
                self._mt[self._r, self._c] = value

            def change(self, dr: int, dc: int):
                self._r += dr
                self._c += dc
                if not (0 <= self._r < self._mt.row_count() and 0 <= self._c < self._mt.column_count()):
                    raise IndexError("Matrix indexes out of range!")

            def stand(self, nr: int, nc: int):
                self._r = nr
                self._c = nc
                if not (0 <= self._r < self._mt.row_count() and 0 <= self._c < self._mt.column_count()):
                    raise IndexError("Matrix indexes out of range!")

            def pos(self):
                return self._r, self._c

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
            return iter([self.MatrixPos(self._field, (i, k))
                         for i in range(self.row_count())
                         for k in range(self.column_count())])

        def __str__(self):
            return ", \n".join(["[" + ", ".join(map(str, i)) + "]" for i in self._items])

        def __repr__(self):
            return str(self)

    def FieldPos(self, r, c):
        return self.FieldMatrix.MatrixPos(self, (r, c))

    def set_view(self, pos):
        log("Replacing my view...", "set_view", "field")
        self.stand(*pos)

    def draw_cells(self):
        for pos in self.mt:
            pos.get().stand(*self.place(pos.pos()))
        # for r, row in enumerate(self.mt):
        #     for c, item in enumerate(row):
        #         item.stand(*self.place((c, r)))

    def place(self, point):
        x, y = self.pos()
        return x + point[1] * CELL_SIZE, y + point[0] * CELL_SIZE

    @staticmethod
    def Load(file_name, *groups):
        """Интерпретирует текстовый вид уровня в сам уровень с помощью имеющегося синтаксиса
        TODO документация по синтаксису"""
        inp = open(file_name, "r").read().split("\n\n")

        mt = [[GetCell(c) for c in row] for row in inp[0].split("\n")]
        inp = inp[1].split("\n")
        for i in range(1, int(inp[0]) + 1):
            points = [tuple(map(int, i.split(","))) for i in inp[i].split(" ")]
            for p in range(1, len(points)):
                mt[points[0][0]][points[0][1]].connect.append(mt[points[p][0]][points[p][1]])
        for i in range(int(inp[0]) + 1, len(inp)):
            pos, mes = inp[i].split(" ", 1)
            r, c = map(int, pos.split(","))
            assert isinstance(mt[r][c], InfoCell)
            # noinspection PyUnresolvedReferences
            mt[r][c].text = mes

        return Field(mt, *groups)


FieldPos = Field.FieldMatrix.MatrixPos


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

    def release(self) -> Takeable:
        if self.hold is None:
            raise Exception("Trying to release object while nothing is holding")
        self.field_pos.get().params["takeables"].append(self.hold)
        self.hold.field_pos = self.field_pos
        self.hold.stand(self.field_pos.get().x() + randint(0, self.field_pos.get().w() - self.hold.w()),
                        self.field_pos.get().y() + randint(0, self.field_pos.get().h() - self.hold.h()))

        me.takeable_group.add(self.hold)
        me.player_group.remove(self.hold)
        _ = self.hold
        self.hold = None
        self.field_pos.get().on_cube_set()
        if len(self.field_pos.get().params["takeables"]) > 2:
            log("too many takeables at once", "change_cell", "WARNING")
        return _


class GMain(GPygameMachine):
    """Класс Main, занимающийся исполнением уровней. Пока игра содержит лишь один уровень
    - вызывается по умолчанию. Содержит очередь функций, счетчик цикла, а также группы спрайтов"""
    def __init__(self, *args):
        self.exit_code = 1
        self.g_cycle = 0
        self.args = args
        self.queue = []
        self.all_sprites = pg.sprite.Group()
        self.player_group = pg.sprite.Group()
        self.cell_group = pg.sprite.Group()
        self.takeable_group = pg.sprite.Group()

    def start(self):
        log("Started starting up...", "Start machine", "main")
        pg.init()
        self.window_size = self.window_width, self.window_height = 1280, 720

        # self.screen = pg.display.set_mode(self.window_size, pg.FULLSCREEN)
        self.screen = pg.display.set_mode(self.window_size)
        load_data()

        self.field = Field.Load(r"C:\Olymp\yandee\PROJECT_BOX\Trial\data\testlevel.txt",
                                (self.all_sprites, self.cell_group))
        self.field.set_view(((self.window_width - CELL_SIZE * self.field.width) // 2,
                             (self.window_height - CELL_SIZE * self.field.height) // 2))
        self.camera = GCamera()
        self.player = Player(self.field.FieldPos(5, 2), self.all_sprites, self.player_group)
        self.player.stand(*self.field.place((self.player.field_pos.r(), self.player.field_pos.c())))

        self.clock = pg.time.Clock()
        log("Successfully started up", "Start machine", "main")

    def quit(self):
        log("Started quiting...", "Quit machine", "main")
        pg.quit()
        log("Successfully quited", "Quit machine", "main")

    def handle_input(self):
        for event in self.events():
            if event.type == pg.QUIT:
                log("Exit_button pressed", "Cycle {}".format(str(self.g_cycle)), "main")
                self.exit_code = 0
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

    def manage_cycle(self):
        self.g_cycle += 1

        _ = self.queue.copy()
        while len(_) > 0:
            # print(_)
            _.pop(0)()
            self.queue.pop(0)

        # noinspection PyArgumentList
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
        pg.display.flip()
        self.clock.tick(60)


def log(mes, sender=None, father=None, say=print):
    if father is not None:
        if sender is None:
            sender = str(father).upper()
        else:
            sender = "{}/{}".format(str(father).upper(), str(sender))
    if sender is not None:
        mes = "[{}] ".format(str(sender)) + mes
    say(mes)


def main(*args):
    global me
    me = GMain(*args)
    return me.main()


if __name__ == "__main__":
    import sys
    sys.exit(main(*sys.argv))
