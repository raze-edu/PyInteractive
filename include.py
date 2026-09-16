from bitarray import bitarray as ba
from bitarray.util import int2ba as i2b, ba2int as b2i
from random import randint as rng
from math import cos, sin, pi, radians as rad, degrees as deg
from pathlib import Path
from json import loads, dumps
from enum import Enum
import weakref

LOGIC_TABLE_BIN = Path('logic_table.bin')
COMPONENT_LIB_FILE = Path('component_lib.json')

"""# Bits"""

class Bits(ba):
    @classmethod
    def random(cls, length:int):
        return cls(i2b(rng(0,2**length-1), length=length))

    @classmethod
    def from_int(cls, value:int, length:int=0):
        length = length if length > 0 else value.bit_length()
        return cls(i2b(value, length))

    def write_file(self, path:str|Path, padding=1):
        path = Path(path)
        path.write_bytes(self.padding_to(padding).tobytes())

    @classmethod
    def from_file(cls, path:str|Path):
        path = Path(path)
        return cls(path.read_bytes()).unpadding()

    def padding_to(self, n_bytes:int=1):
        pad_size = 8 * n_bytes
        pad = Bits('0' * (pad_size - 1) + '1')
        print(len(self), pad_size, len(self) % pad_size)
        pad = pad if len(self) == 0 else pad[len(self) % pad_size:]
        return pad + self

    def unpadding(self):
        for i, v in enumerate(self):
            if v == 1:
                self = self[i+1:]
                break
        return self

    def __int__(self):
        return b2i(self)

    @property
    def bool_array(self):
        return [bool(v) for v in self]

    def split(self, n_bits:list[int]):
        arr = []
        for i, v in enumerate(n_bits):
            arr.append(self[sum([0]+n_bits[:i]):sum([0]+n_bits[:i])+v])
        return arr

    @staticmethod
    def range(bits:int):
        return [Bits.from_int(i, bits) for i in range(2**bits)]

'''t = Bits.random(128)
print(t.split([5, 8, 10, 22]))
print(Bits([True, True, False]))
temp = Bits.random(10)
print(temp)
print(temp, temp.padding_to(), temp.padding_to().unpadding())
print(temp.__int__(), temp[:5].bool_array)
temp.write_file('test.bin')
print(Bits.from_file('test.bin'))'''

"""# Helper"""

NODE_ID_BITS = 8
COMPONENT_ID_BITS = 8

def get_unique_id(parent_id, existing:list, n_bits:int):
    id = parent_id + Bits.random(n_bits)
    while id in existing:
        id = parent_id + Bits.random(n_bits)
    return id

def circ_dist_2_deg(circle_radius:int, distance):
    return distance / (2 * pi * circle_radius) * 360

class Direction(Enum):
    N = 0
    E = 90
    S = 180
    W = 270
    NE = 45
    SE = 135
    SW = 225
    NW = 315

class Color:
    __slots__ = 'R', 'G', 'B', 'A'
    def __init__(self, *args, **kwargs):
        [self.__setattr__(self.__slots__[i], v) for i, v in enumerate(args)]
        [self.__setattr__(k, kwargs.get(k, v)) for k, v in zip(self.__slots__, [0, 0, 0, 255])]

    def __add__(self, other):
        return Color(*[self.__getattribute__(k) + other.__getattribute__(k) for k in self.__slots__])

    def __sub__(self, other):
        return Color(*[self.__getattribute__(k) - other.__getattribute__(k) for k in self.__slots__])

    def __mul__(self, other):
        return Color(*[self.__getattribute__(k) * other for k in self.__slots__])

    def __truediv__(self, other):
        return Color(*[0 if self.__getattribute__(k) == 0 else self.__getattribute__(k) / other for k in self.__slots__])

    def __tuple__(self):
        return tuple([int(self.__getattribute__(k)) for k in self.__slots__])

    def create_fade_to(self, other, steps):
        temp = other - self
        return [self + (temp * (1 / steps) * i) for i in range(1, steps+1)]

class Relative:
    def __init__(self, rel_size, rel_center_pos=(.5, .5), origin=None):
        self.size = rel_size
        self.pos = rel_center_pos
        self.origin = origin

    @property
    def width(self):
        return self.size[0] if self.origin is None else self.size[0] * self.origin.width

    @property
    def height(self):
        return self.size[1] if self.origin is None else self.size[1] * self.origin.height

    @property
    def x(self):
        return self.pos[0] * self.width if self.origin is None else (self.pos[0] * self.width) + self.origin.x

    @property
    def y(self):
        return self.pos[1] * self.height if self.origin is None else (self.pos[1] * self.height) + self.origin.y

    @property
    def rect(self):
        return self.x, self.y, self.width, self.height


    def circle_point(self, radius, angle, rel=True):
        if not rel:
            x, y = self.x, self.y - radius
        else:
            x, y = 0, -(self.height - self.y) * radius
        c, s = cos(rad(angle)), sin(rad(angle))
        return (x * c - y * s) + self.x, (x * s + y * c) + self.y

class Area:
    __slots__ = 'width', 'height'
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_rel_area(self, rel_w, rel_h):
        return self.__class__(self.width * rel_w, self.height * rel_h)

class RelPoint:
    __slots__ = 'x', 'y'
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return self.__class__(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return self.__class__(self.x - other.x, self.y - other.y)

    def __mul__(self, other:Area):
        return self.__class__(self.x * other.width, self.y * other.height)

    def __repr__(self):
        return f'RPos:[{self.x}|{self.y}]'

    def get_rel_point(self, *related):
        temp = self
        for r in related:
            temp = temp + r
        return temp

class Polygon(list):
    def __init__(self, origin:RelPoint, points:list[RelPoint]):
        super().__init__(points)
        self.origin = origin

    def __getitem__(self, index):
        return self.origin + super().__getitem__(index)

    def __iter__(self):
        return iter([p + self.origin for p in super().__iter__()])

    def get_absolut_points(self, area, rel=RelPoint(0, 0)):
        return [(v+rel)*area for v in self]

test = [Relative((1000, 1000), (.5, .5))]
test.append(Relative((.5, .5), (0, 1.0), origin=test[0]))
print(cos(90), 1*cos(rad(45))-0*sin(rad(45)), 1*sin(rad(45))+0*cos(rad(45)))
print(test[0].rect)
print(test[1].rect)
print(test[0].circle_point(1, 0))

r = Polygon(RelPoint(.5,.5), [RelPoint(-.1,-.1), RelPoint(.1, -.1), RelPoint(.1, .1)])
for item in r.get_absolut_points(Area(1000, 1000)):
    print(item)

"""# Connection & Node"""

class Connection(list):
    def __init__(self):
        super().__init__([[], [], [], []])

    @classmethod
    def from_build(cls, node_array:list, build:list):
        temp = cls()
        for v in build[0]:
            temp.add_rx(node_array[v])
        for v in build[1]:
            temp.add_tx(node_array[v])
        return temp

    @property
    def ids(self):
        return self[2] + self[3]

    @property
    def input_nodes_ids(self):
        return self[2]

    @property
    def output_nodes_ids(self):
        return self[3]

    @property
    def tx(self):
        return self[1]

    @property
    def rx(self):
        return self[0]

    @property
    def state(self):
        return any([s()() for s in self.tx])

    def check_for_node(self, node_id):
        return node_id in self.ids

    def run(self):
        state = self.state
        for s in self.rx:
            s()(state=state)

    def add_rx(self, rx):
        if rx.id not in self.ids:
            self[2].append(rx.id)
            self[0].append(rx.get_switch())

    def add_tx(self, tx):
        if tx.id not in self.ids:
            self[3].append(tx.id)
            self[1].append(tx.get_state())

def create_node_constructor():
    class Node:
        ids = []
        def __init__(self, parent_id=Bits('')):
            self.id = get_unique_id(parent_id, self.ids, NODE_ID_BITS)
            self.ids.append(self.id)
            self.state = False

        def state_is(self):
            return self.state

        def switch_to(self, state=None):
            self.state = not self.state if state is None else bool(state)

        def get_switch(self):
            # Return a weak reference to the bound method
            # This allows the Node instance to be garbage collected if no strong references remain.
            return weakref.WeakMethod(self.switch_to)


        def get_state(self):
            return weakref.WeakMethod(self.state_is)

        def clear_ids(self):
            self.ids = []

    return Node

Node = create_node_constructor()

"""# Components"""

class BaseComponent:
    ids = []
    def __init__(self, global_node, n_nodes:tuple):
        self.id = get_unique_id(Bits(''), self.ids, COMPONENT_ID_BITS)
        self.ids.append(self.id)
        self.nodes = [global_node(parent_id=self.id) for _ in range(n_nodes[0])], [global_node(parent_id=self.id) for _ in range(n_nodes[1])]

    @property
    def input_nodes_ids(self):
        return [n.id for n in self.input_nodes]

    @property
    def output_nodes_ids(self):
        return [n.id for n in self.output_nodes]

    @property
    def node_ids(self):
        return self.input_nodes_ids + self.output_nodes_ids

    #   INPUT PrOPERTYS
    @property
    def input_state(self) -> list[bool]:
        return [n.state_is() for n in self.input_nodes]

    @property
    def input_bits(self) -> Bits:
        return Bits(self.input_state)

    @property
    def input_int(self) -> int:
        return int(self.input_bits)

    @property
    def input_nodes(self):
        return self.nodes[0]

    #   OUTPUT PROPERTYS
    @property
    def output_state(self):
        return [n.state_is() for n in self.output_nodes]

    @property
    def output_bits(self):
        return Bits(self.output_state)

    @property
    def output_nodes(self):
        return self.nodes[1]

    @property
    def node_array(self):
        return self.nodes[0] + self.nodes[1]

    def set_input_state(self, state:list|Bits):
        [n.switch_to(bool(s)) for n, s in zip(self.input_nodes, state)]

class LogicTable(BaseComponent):
    def __init__(self, global_node, n_nodes:tuple, table:Bits):
        super().__init__(global_node, n_nodes)
        self.table = table

    def run(self):
        _in = self.input_int
        size = len(self.nodes[1])
        [n.switch_to(s) for n, s in zip(self.nodes[1], self.table[size * _in:size * (_in + 1)].bool_array)]


class SimComponent(BaseComponent):
    lib = None
    def __init__(self, global_node, n_nodes:tuple, components=[], connections=[]):
        super().__init__(global_node, n_nodes)
        self.private_node = create_node_constructor()
        self.component_names = components
        if self.lib:
            self.components = [self.lib.get(c, self.private_node) for c in components]
            self.connections = [Connection.from_build(self.node_full_array, c) for c in connections]
        else:
            self.components = []

    def run(self):
        for c in self.connections:
            c.run()
            print(c.state)
            for com in self.components:
                com.run()

    def create_logic_table(self):
        temp = Bits('')
        for b in Bits.range(len(self.nodes[0])):
            self.set_input_state(b)
            self.run()
            temp += self.output_bits
        return temp

    @property
    def node_components(self):
        temp = []
        for comp in self.components:
            temp += comp.node_array
        return temp

    @property
    def node_full_array(self):
        return self.node_array + self.node_components

    @property
    def node_ids(self):
        return [n.id for n in self.node_full_array]

    @property
    def get_connection_links(self):
        return [[[self.node_ids.index(n) for n in c.input_nodes_ids], [self.node_ids.index(n) for n in c.output_nodes_ids]] for c in self.connections]

    def set_connection_links(self, arr):
        for c, l in zip(self.connections, arr):
            [c.add_rx(self.node_full_array[i]) for i in l[0]]
            [c.add_tx(self.node_full_array[i]) for i in l[1]]

"""# Library"""

class SimComponentLibraryEntry:
    __slots__ = 'name', 'n_nodes', 'components', 'connections'
    def __init__(self, name, n_nodes, components, connections):
        self.name = name
        self.n_nodes = n_nodes
        self.components = components
        self.connections = connections
        self.create_entry()

    def create_entry(self):
        COMPONENT_LIB.Sim[self.name] = self.name, self.n_nodes, self.components, self.connections

    @classmethod
    def from_SimComponent(cls, name, sim_object:SimComponent):
        return cls(name, (len(sim_object.nodes[0]), len(sim_object.nodes[1])), sim_object.component_names, sim_object.get_connection_links)


class TableComponentLibraryEntry:
    __slots__ = 'name', 'n_nodes', 'table'
    def __init__(self, name, n_nodes, table):
        self.name = name
        self.n_nodes = n_nodes
        self.table = table
        self.create_entry()

    def create_entry(self):
        COMPONENT_LIB.Table[self.name] = self.name, self.n_nodes, self.table


    @classmethod
    def from_SimComponent(cls, name, sim_object:SimComponent):
        return cls(name, (len(sim_object.nodes[0]), len(sim_object.nodes[1])), sim_object.create_logic_table())


class COMPONENT_LIB:
    Table = dict()
    Sim = dict()

    @staticmethod
    def get(name, node=None):
        node = node if node is not None else create_node_constructor()
        if COMPONENT_LIB.Table.get(name, False):
            return LogicTable(node, COMPONENT_LIB.Table[name][1], COMPONENT_LIB.Table[name][2])
        elif COMPONENT_LIB.Sim.get(name, False):
            return SimComponent(node, COMPONENT_LIB.Sim[name][1], COMPONENT_LIB.Sim[name][2], COMPONENT_LIB.Sim[name][3])

    @staticmethod
    def show():
        return f'Table: {len(COMPONENT_LIB.Table)}\nSim: {len(COMPONENT_LIB.Sim)}'

    @staticmethod
    def save_lib():
        temp = dict(table=[], sim=[])
        bin_data = Bits('')
        for key, val in COMPONENT_LIB.Table.items():
            temp['table'].append([val[0], val[1], len(val[-1])])
            bin_data += val[-1]
        bin_data.write_file(LOGIC_TABLE_BIN)
        for key, val in COMPONENT_LIB.Sim.items():
            temp['sim'].append(val)
        COMPONENT_LIB_FILE.write_text(dumps(temp))


    @classmethod
    def load_lib(cls):
        bin_data = Bits.from_file(LOGIC_TABLE_BIN)
        temp = loads(COMPONENT_LIB_FILE.read_text())
        for t, b in zip(temp['table'], bin_data.split([t[-1] for t in temp['table']])):
            TableComponentLibraryEntry(t[0], t[1], b)
        for t in temp['sim']:
            SimComponentLibraryEntry(*t)

    def _sim_component(self):
        for key, val in self.Sim.items():
            print(key, val)

SimComponent.lib = COMPONENT_LIB

"""# Tests"""

TableComponentLibraryEntry('NOT', (1, 1), Bits('01'))
TableComponentLibraryEntry('AND', (2, 1), Bits('0001'))
TableComponentLibraryEntry('OR', (2, 1), Bits('0111'))
TableComponentLibraryEntry('XOR', (2, 1), Bits('0110'))

Node().clear_ids()
sc = SimComponent(Node, (2, 1), ['AND', 'NOT'], [Connection(), Connection(), Connection(), Connection()])

sc.connections[0].add_tx(sc.nodes[0][0])
sc.connections[0].add_rx(sc.components[0].nodes[0][0])
sc.connections[1].add_tx(sc.nodes[0][1])
sc.connections[1].add_rx(sc.components[0].nodes[0][1])
sc.connections[2].add_tx(sc.components[0].nodes[1][0])
sc.connections[2].add_rx(sc.components[1].nodes[0][0])
sc.connections[3].add_tx(sc.components[1].nodes[1][0])
sc.connections[3].add_rx(sc.nodes[1][0])

SimComponentLibraryEntry.from_SimComponent('NAND', sc)

print(sc.get_connection_links)
print([t.table for t in sc.components])

def test_sim(sim):
    for b in Bits.range(len(sim.nodes[0])):
        sc.set_input_state(b)
        print(sc.input_state, sc.components[0].output_state)
        sc.run()
        print(b, sc.output_bits)
    print(sc.create_logic_table())

print(COMPONENT_LIB.show())
COMPONENT_LIB.load_lib()
print(COMPONENT_LIB.show())

COMPONENT_LIB.save_lib()
#COMPONENT_LIB.load_lib()

test = COMPONENT_LIB.get('NAND')
test_sim(test)
