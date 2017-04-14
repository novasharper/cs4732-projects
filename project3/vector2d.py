from __future__ import division, print_function, absolute_import, unicode_literals

import math
import operator

def limit(vector, lim):
    """
    limit a vector to a given magnitude
    this is an 'in place' function, modifies the vector supplied.
    """
    if abs(vector) > lim:
        vector.normalize()
        vector *= lim

# Some magic here.  If _use_slots is True, the classes will derive from
# object and will define a __slots__ class variable.  If _use_slots is
# False, classes will be old-style and will not define __slots__.
#
# _use_slots = True:   Memory efficient, probably faster in future versions
#                      of Python, "better".
# _use_slots = False:  Ordinary classes, much faster than slots in current
#                      versions of Python (2.4 and 2.5).
_use_slots = False

# Implement _use_slots magic.
class _EuclidMetaclass(type):
    def __new__(cls, name, bases, dct):
        if _use_slots:
            return type.__new__(cls, name, bases + (object,), dct)
        else:
            del dct['__slots__']
            return types.ClassType.__new__(types.ClassType, name, bases, dct)
__metaclass__ = _EuclidMetaclass


class Vector2(object):
    __slots__ = ['x', 'y']

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __copy__(self):
        return self.__class__(self.x, self.y)

    copy = __copy__

    def __repr__(self):
        return 'Vector2(%.4f, %.4f)' % (self.x, self.y)

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        else:
            assert hasattr(other, '__len__') and len(other) == 2
            return self.x == other[0] and self.y == other[1]

    def __neq__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self.x != 0 or self.y != 0

    def __len__(self):
        return 2

    def __getitem__(self, key):
        return (self.x, self.y)[key]

    def __setitem__(self, key, value):
        l = [self.x, self.y]
        l[key] = value
        self.x, self.y = l

    def __iter__(self):
        return iter((self.x, self.y))

#    def __getattr__(self, name):
#        try:
#            return tuple([(self.x, self.y)['xy'.index(c)] for c in name])
#        except ValueError:
#            raise AttributeError(name)

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x,
                           self.y + other.y)
        else:
            assert hasattr(other, '__len__') and len(other) == 2
            return Vector2(self.x + other[0],
                           self.y + other[1])
    __radd__ = __add__

    def __iadd__(self, other):
        if isinstance(other, Vector2):
            self.x += other.x
            self.y += other.y
        else:
            self.x += other[0]
            self.y += other[1]
        return self

    def __sub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x,
                           self.y - other.y)
        else:
            assert hasattr(other, '__len__') and len(other) == 2
            return Vector2(self.x - other[0],
                           self.y - other[1])

    def __rsub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(other.x - self.x,
                           other.y - self.y)
        else:
            assert hasattr(other, '__len__') and len(other) == 2
            return Vector2(other.x - self[0],
                           other.y - self[1])

    def __mul__(self, other):
        assert type(other) in (int, float)
        return Vector2(self.x * other,
                       self.y * other)

    __rmul__ = __mul__

    def __imul__(self, other):
        assert type(other) in (int, float)
        self.x *= other
        self.y *= other
        return self

    def __div__(self, other):
        assert type(other) in (int, float)
        return Vector2(operator.div(self.x, other),
                       operator.div(self.y, other))

    def __rdiv__(self, other):
        assert type(other) in (int, float)
        return Vector2(operator.div(other, self.x),
                       operator.div(other, self.y))

    def __floordiv__(self, other):
        assert type(other) in (int, float)
        return Vector2(operator.floordiv(self.x, other),
                       operator.floordiv(self.y, other))

    def __rfloordiv__(self, other):
        assert type(other) in (int, float)
        return Vector2(operator.floordiv(other, self.x),
                       operator.floordiv(other, self.y))

    def __truediv__(self, other):
        assert type(other) in (int, float)
        return Vector2(operator.truediv(self.x, other),
                       operator.truediv(self.y, other))

    def __rtruediv__(self, other):
        assert type(other) in (int, float)
        return Vector2(operator.truediv(other, self.x),
                       operator.truediv(other, self.y))

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    __pos__ = __copy__

    def __abs__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    magnitude = __abs__

    def clear(self):
        self.x = 0
        self.y = 0

    def magnitude_squared(self):
        return self.x ** 2 + self.y ** 2

    def normalize(self):
        d = self.magnitude()
        if d:
            self.x /= d
            self.y /= d
        return self

    def normalized(self):
        d = self.magnitude()
        if d:
            return Vector2(self.x / d, self.y / d)
        return self.copy()

    def dot(self, other):
        assert isinstance(other, Vector2)
        return self.x * other.x + self.y * other.y

    def cross(self):
        return Vector2(self.y, -self.x)

    def reflect(self, normal):
        # assume normal is normalized
        assert isinstance(normal, Vector2)
        d = 2 * (self.x * normal.x + self.y * normal.y)
        return Vector2(self.x - d * normal.x, self.y - d * normal.y)
    
    def rot(self, isdeg=False):
        rot = math.atan2(self.y, self.x)
        if isdeg:
            rot = math.degrees(rot)
        return rot
