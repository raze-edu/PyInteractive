class Geo:
    __slots__ = ()
    def __init__(self, *args):
        args = ([arg for arg in args] + [0, 0])[:2]
        [self.__setattr__(k, v) for k, v in zip(self.__slots__, args)]
    
    def __iter__(self):
        return iter((self.__getattribute__(slot) for slot in self.__slots__))
    
    def __add__(self, other):
        if isinstance(other, Geo):
            return self.__class__(*(a + b for a, b in zip(self, other)))
        else:
            raise TypeError("other must be a Point")

    def __sub__(self, other):
        if isinstance(other, Geo):
            return self.__class__(*(a - b for a, b in zip(self, other)))
        else:
            raise TypeError("other must be a Point")

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(*(a * other for a, b in zip(self, other)))
        elif isinstance(other, Geo):
            return self.__class__(*(a * b for a, b in zip(self, other)))
        else:
            raise TypeError("other must be a number")

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return self.__class__(*(a / other for a, b in zip(self, other)))
        elif isinstance(other, Geo):
            return self.__class__(*(a / b for a, b in zip(self, other)))
        else:
            raise TypeError("other must be a number")

    def __neg__(self):
        return self.__class__(*(-a for a in self))

    def __abs__(self):
        return math.hypot(self.x, self.y)

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y
        else:
            raise TypeError("other must be a Point")

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"Point({self.x}, {self.y})"
    
    def __str__(self):
        return f"({self.x}, {self.y})"

    def __tuple__(self):
        return (int(self.x), int(self.y))

class Point(Geo):
    __slots__ = ('x', 'y')

class Line:
    __slots__ = ('p1', 'p2')
    def __init__(self, p1:Point, p2:Point):
        self.p1 = p1
        self.p2 = p2

    def __iter__(self):
        return iter((self.__getattribute__(slot) for slot in self.__slots__))

    @property
    def center(self):
        return (self.p1 + self.p2) / 2

    @property
    def length(self):
        return abs(self.p1 - self.p2)

    @property
    def vector(self):
        return self.p2 - self.p1


class Size(Geo):
    __slots__ = ('w', 'h')

    @property
    def center(self):
        return Point(self.w / 2, self.h / 2)

    @property
    def area(self):
        return self.w * self.h

    def __gt__(self, other):
        return self.w > other.w and self.h > other.h

class Rect:
    __slots__ = 'pos', 'size'
    def __init__(self, pos:Point, size:Size):
        self.pos = pos
        self.size = size

    def __gt__(self, other):
        return self.size > other.size
        
    @property
    def top_left(self):
        return self.pos
    
    @property
    def top_right(self):
        return Point(self.pos.x + self.size.w, self.pos.y)
    
    @property
    def bottom_left(self):
        return Point(self.pos.x, self.pos.y + self.size.h)
    
    @property
    def bottom_right(self):
        return Point(self.pos.x + self.size.w, self.pos.y + self.size.h)

    @property
    def center(self) -> Point:
        return self.pos + self.size / 2
    
    @center.setter
    def center(self, value:Point) -> None:
        self.pos = value - self.size / 2

    @property
    def top(self):
        return Line(self.top_left, self.top_right)
    
    @property
    def bottom(self):
        return Line(self.bottom_left, self.bottom_right)
    
    @property
    def left(self):
        return Line(self.top_left, self.bottom_left)
    
    @property
    def right(self):
        return Line(self.top_right, self.bottom_right)
    
    @property
    def width(self):
        return self.size.w

    @property
    def height(self):
        return self.size.h            
    
    def get_absolute_of_relative(self, other) -> Point:
        if isinstance(other, (Point,Size)):
           return other * self.size
    
    def center_align(self, other):
        if other > self:
            self.center = other.center
        else:
            other.center = self.center

if __name__ == "__main__":
    a = Point(1, 2)
    b = Point(3, 4)
    print(a + b)