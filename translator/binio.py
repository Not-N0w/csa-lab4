def write_im(code, path):
    with open(path, "wb") as f:
        f.write(bytes(code))


def write_dm(dm, path):
    if dm:
        size = max(dm) + 1
        buf = bytearray(size)
        for addr, byte in dm.items():
            buf[addr] = byte & 0xFF
    else:
        buf = bytearray()
    with open(path, "wb") as f:
        f.write(bytes(buf))


def read_im(path):
    with open(path, "rb") as f:
        return list(f.read())


def read_dm(path):
    with open(path, "rb") as f:
        data = f.read()
    return {i: b for i, b in enumerate(data)}