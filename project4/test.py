#!/usr/bin/env python3

class A:
    def __init__(self, callback):
        self.callback = callback
    
    def do_callback(self):
        self.callback(self)

class C:
    def __init__(self):
        self.foo = "aaa"
    
    def gen_callback(self):
        def callback(self):
            self.barr = "bbb"
            return self.foo
        return lambda: callback(self)
    
    def gen_callable(self):
        return A(self.gen_callback())

c = C()
a = c.gen_callable()
#a.do_callback()
#print(c.foo, c.barr)

def foo(self):
    return self.barr

a2 = A(foo)
a2.barr = 'test'
print(a2.do_callback(), a2.barr)