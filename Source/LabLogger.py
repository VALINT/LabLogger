import pyvisa
import time

def StupidLog():
    rm = pyvisa.ResourceManager()
    rm.list_resources()
    ins = rm.open_resource("ASRL3::INSTR")
    while 1:
        cap = ins.query_ascii_values(":FETC?")
        print(cap)
        time.sleep(1)

if __name__ == "__main__":
    StupidLog()