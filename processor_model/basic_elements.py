from abc import ABC, abstractmethod


class Source(ABC):
    @abstractmethod
    def get(self):
        pass


class Register(Source):
    def __init__(self, size=32):
        self.size = size
        self.value = 0
        self.source = None

    def set_source(self, source):
        self.source = source

    def get_source_value(self):
        if self.source is None:
            raise Exception("Register source is not set")
        return self.source.get()

    def get(self):
        return self.value & ((1 << self.size) - 1)


class Mux(Source):
    def __init__(self):
        self.options = {}
        self.signal = ""

    def set_options(self, options):
        self.options = options

    def set_signal(self, signal):
        self.signal = signal

    def reset(self):
        self.signal = ""

    def get(self):
        if self.signal not in self.options:
            raise Exception("Unknown mux signal: " + self.signal)
        return self.options[self.signal].get()


class ALU(Source):
    MASK = 0xFFFFFFFF

    def __init__(self, nzvc_reg):
        self.op1 = None
        self.op2 = None
        self.signal = ""
        self.lb = True
        self.nzvc_reg = nzvc_reg

    def set_op1(self, op1):
        self.op1 = op1

    def set_op2(self, op2):
        self.op2 = op2

    def set_signal(self, signal):
        self.signal = signal

    def set_lb(self, lb):
        self.lb = lb

    def _raw(self):
        a = self.op1.get()
        b = self.op2.get()
        s = self.signal
        if s == "alu_add": return a + b
        if s == "alu_sub" or s == "alu_cmp": return b - a
        if s == "alu_mul": return a * b
        if s == "alu_div": return (b // a) if a != 0 else 0
        if s == "alu_not": return ~a
        if s == "alu_or": return a | b
        if s == "alu_and": return a & b
        if s == "alu_xor": return a ^ b
        if s == "alu_asl": return b << (a & 31)
        if s == "alu_asr":
            sign = b | (~self.MASK) if (b & 0x80000000) else b
            return sign >> (a & 31)
        if s == "alu_lsl": return b << (a & 31)
        if s == "alu_lsr": return (b & self.MASK) >> (a & 31)
        if s == "alu_pass": return a
        if s == "alu_inc_lb": return a + (4 if self.lb else 1)
        if s == "alu_dec_lb": return a - (4 if self.lb else 1)
        raise Exception("Unknown ALU signal: " + self.signal)

    def get(self):
        return self._raw() & self.MASK

    def get_nzvc(self):
        res = self.get()
        n = "1" if res & 0x80000000 else "0"
        z = "1" if res == 0 else "0"
        return int(n + z + "00", 2)


class MemoryUnit(Source):
    def __init__(self, delay=5):
        self.ready = False
        self.data = {}
        self.addr_source = None
        self.size_source = None
        self.inner_counter = -1
        self.delay = delay
        self.pending_write = None
        self.read_size = 4

    def set_data(self, data):
        if isinstance(data, list):
            self.data = {i: (v & 0xFF) for i, v in enumerate(data)}
        else:
            self.data = {a: (v & 0xFF) for a, v in data.items()}

    def set_addr_source(self, source):
        self.addr_source = source

    def set_size_source(self, source):
        self.size_source = source

    def _size(self):
        return self.size_source() if self.size_source else 4

    def start_read(self):
        if self.inner_counter == -1:
            self.inner_counter = 0
            self.pending_write = None
            self.read_size = self._size()
            self.ready = False

    def start_write(self, value):
        if self.inner_counter == -1:
            self.inner_counter = 0
            self.pending_write = (value & 0xFFFFFFFF, self._size())
            self.ready = False

    def tick(self):
        if self.inner_counter == -1:
            return
        self.inner_counter += 1
        if self.inner_counter >= self.delay:
            if self.pending_write is not None:
                value, size = self.pending_write
                addr = self.addr_source.get()
                for i in range(size):
                    self.data[addr + i] = (value >> (8 * (size - 1 - i))) & 0xFF
            self.ready = True
            self.inner_counter = -1

    def is_ready(self):
        return self.ready

    def _consume(self):
        self.ready = False
        self.inner_counter = -1
        self.pending_write = None

    def get(self):
        if not self.ready:
            raise Exception("Memory unit is not ready")
        addr = self.addr_source.get()
        val = 0
        for i in range(self.read_size):
            val = (val << 8) | self.data.get(addr + i, 0)
        self._consume()
        return val


class IOPort:
    def __init__(self, delay=5):
        self.in_buffer = []
        self.out_buffer = []
        self.in_word = 0
        self.rdy = False
        self.delay = delay
        self.counter = -1

    def start_read(self):
        if self.counter == -1:
            self.counter = 0
            self.rdy = False
            self.in_word = self.in_buffer.pop(0) if self.in_buffer else 0

    def start_write(self, word):
        if self.counter == -1:
            self.counter = 0
            self.rdy = False
            self.out_buffer.append(word & 0xFFFFFFFF)

    def tick(self):
        if self.counter != -1:
            self.counter += 1
            if self.counter >= self.delay:
                self.rdy = True
                self.counter = -1

    def is_ready(self):
        return self.rdy

    def get_word(self):
        return self.in_word

    def feed(self, words):
        self.in_buffer = list(words)


class IODevice(Source):
    def __init__(self, n=3, delay=5):
        self.ports = [IOPort(delay) for _ in range(n)]
        self.port_source = None

    def set_port_source(self, source):
        self.port_source = source

    def _port(self):
        idx = int(self.port_source.get()) & 0xFF
        return self.ports[idx] if idx < len(self.ports) else None

    def tick(self):
        for p in self.ports:
            p.tick()

    def start_read(self):
        p = self._port()
        if p:
            p.start_read()

    def start_write(self, word):
        p = self._port()
        if p:
            p.start_write(word)

    def is_ready(self):
        p = self._port()
        return p.is_ready() if p else False

    def get(self):
        p = self._port()
        return p.get_word() if p else 0


class Sum(Source):
    def __init__(self):
        self.signal = ""
        self.op1 = None
        self.op2 = None

    def set_op1(self, op1):
        self.op1 = op1

    def set_op2(self, op2):
        self.op2 = op2

    def set_signal(self, signal):
        self.signal = signal

    def get(self):
        if self.signal == "sum_shrt":
            return (self.op1.get() + self.op2.get()) & 0xFFFFFFFF
        if self.signal == "sum_load":
            return self.op2.get() & 0xFFFFFFFF
        raise Exception("Unknown sum signal: " + self.signal)


class NumberSource(Source):
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value