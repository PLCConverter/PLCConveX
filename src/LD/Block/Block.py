class Position:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)
    def __repr__(self):
        return f"Position(x={self.x}, y={self.y})"

class RelPosition:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)
    def __repr__(self):
        return f"RelPosition(x={self.x}, y={self.y})"

class ConnectionPointIn:
    def __init__(self):
        self.relPosition = None
        self.connection = None
    def __repr__(self):
        return f"ConnectionPointIn(relPosition={self.relPosition}, connection={self.connection})"
    
class ConnectionPointOut:
    def __init__(self, formalParameter):
        self.formalParameter = formalParameter
        self.relPosition = None
    def __repr__(self):
        return f"ConnectionPointOut(formalParameter={self.formalParameter}, relPosition={self.relPosition})"
    
class InVariable:
    def __init__(self, localId, height, width, negated):
        self.localId = localId
        self.height = int(height)
        self.width = int(width)
        self.negated = negated == 'true'
        self.position = None
        self.connectionPointOut = None
        self.expression = None
    def __repr__(self):
        return f"InVariable(localId={self.localId}, height={self.height}, width={self.width}, negated={self.negated}, position={self.position}, connectionPointOut={self.connectionPointOut}, expression={self.expression})"


            
class Block:
    def __init__(self, localId, typeName, height, width):
        self.localId = localId
        self.typeName = typeName
        self.height = int(height)
        self.width = int(width)
        self.position = None
        self.inputVariables = []
        self.outputVariables = []
        self.inOutVariables = []
    def __repr__(self):
        return f"Block(localId={self.localId}, typeName={self.typeName}, height={self.height}, width={self.width}, position={self.position}, inputVariables={self.inputVariables}, outputVariables={self.outputVariables})"

class ConnectionPointIn:
    def __init__(self):
        self.relPosition = None
        self.connection = None
    def __repr__(self):
        return f"ConnectionPointIn(relPosition={self.relPosition}, connection={self.connection})"

  