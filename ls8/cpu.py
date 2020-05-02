"""CPU functionality."""

import sys
ADD = 0b10100000
LDI = 0b10000010
PRN = 0b01000111
HLT = 0b00000001
MUL = 0b10100010
PUSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
RET = 0b00010001
CMP = 0b10100111
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        # Register
        self.reg = [0] * 8
        # Program Counter, the address in memory of the current instruction
        self.pc = 0
        # Instruction Register
        self.ir = None
        # Stack pointer
        self.reg[7] = 0xf4
        # Flag Register
        self.fl = 0b0
        
        # Branch table
        self.branchtable = {
            LDI: self.LDI,
            PRN: self.PRN, 
            HLT: self.HLT,
            MUL: lambda oper_a, oper_b: self.alu("MUL", oper_a, oper_b),
            ADD: lambda oper_a, oper_b: self.alu("ADD", oper_a, oper_b),
            PUSH: self.PUSH,
            POP: self.POP,
            CALL: self.CALL,
            RET: self.RET,
            CMP: lambda oper_a, oper_b: self.alu("CMP", oper_a, oper_b),
            JMP: self.JMP,
            JEQ: self.JEQ,
            JNE: self.JNE
        }

    def load(self, filepath):
        """Load a program into memory."""

        # Next address in memory to insert value into
        address = 0

        # Open program to run
        with open(filepath) as program:
            # Iterate over each line in the program
            for line in program:
                # Shorten line down to binary length
                shortend_line = line[:8]
                # Filter out all characters except for digits
                cleaned_line = ''.join(filter(str.isdigit, shortend_line))
            
                # Check if the cleaned line is valid in length
                if len(cleaned_line) is 8:
                    # Insert instruction into memory
                    self.ram_write(int(cleaned_line, 2), address)
                    # Increment to next address
                    address += 1
            
            # execute program in memory
            self.run()
            
    def ram_read(self, address):
        """Accepts an address and to read and returns the value stored ram"""
        return self.ram[address]

    def ram_write(self, value, address):
        """Accepts a value to write, and an address to write to in ram"""
        self.ram[address] = value

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        #elif op == "SUB": etc
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == "CMP":
            if self.reg[reg_a] < self.reg[reg_b]:
                self.fl = 0b00000100
            elif self.reg[reg_a] > self.reg[reg_b]: 
                self.fl = 0b00000010
            elif self.reg[reg_a] == self.reg[reg_b]:
                self.fl = 0b00000001
        else:
            raise Exception("Unsupported ALU operation")
    
    @property
    def stack_pointer(self):
        return self.reg[7]

    @stack_pointer.setter
    def stack_pointer(self, value):
        self.reg[7] = value

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()
 
    def LDI(self):
        # Create reference of register address
        register_address = self.ram[self.pc + 1]
        # Create reference of register value
        register_value = self.ram[self.pc + 2]
        # Select register address and assign it a value
        self.reg[register_address] = register_value

    def PRN(self):
        # Retrieve value from register 
        value = self.reg[self.ram_read(self.pc + 1)]
        # Print value
        print(f"Print: {value}")

    def HLT(self):
        # Throw SystemExit exception
        quit()
    
    def PUSH(self):
        # Decrement stack pointer
        self.stack_pointer -= 1
        # Copy value from register and place it into the stack
        self.ram[self.stack_pointer] = self.ram[self.pc + 1]
    
    def POP(self):
         # Copy value from stack and place it into register
        self.ram[self.pc + 1] = self.ram[self.stack_pointer]
        # Increment stack pointer
        self.stack_pointer += 1
    
    def CALL(self):
        self.stack_pointer -= 1
        self.ram[self.stack_pointer] = self.ram[self.pc + 1]
        self.pc = self.reg[self.pc + 1]

    def RET(self):
        self.pc = self.ram[self.stack_pointer]
        self.stack_pointer += 1
    
    def JMP(self):
        self.pc = self.reg[self.ram[self.pc + 1]]
    
    def JEQ(self):
        if self.fl == 1:
            self.JMP()
        else:
            self.pc += 2

    def JNE(self):
        if self.fl is not 1:
            self.JMP()
        else:
            self.pc += 2

    def run(self):
        """Run the CPU."""
        while True:
            # Retrieve op code from memory and store it in the istruction register
            self.ir = self.ram_read(self.pc)
            sets_pc = (self.ir & 0b00010000) >> 4
            # Create reference of potential operands
            oper_a = self.ram[self.pc + 1]
            oper_b = self.ram[self.pc + 2]
            # Bitshift and MASK op code to check if it requires the ALU
            is_alu_op = (self.ir & 0b00100000) >> 5

            if is_alu_op:
                self.branchtable[self.ir](oper_a, oper_b)
            else:
                self.branchtable[self.ir]()

            if not sets_pc:
                self.pc += ((self.ir & 0b11000000) >> 6) + 1
        
