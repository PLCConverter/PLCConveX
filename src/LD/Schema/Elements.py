import sys
sys.path.append('..')
sys.path.append('../..')
from LD.Utils.counter import increment, get_value, set_value
import xml.etree.ElementTree as ET

from Logs.colorLogger import get_color_logger
logger = get_color_logger("Schema/Elements.py")

"""
<variable name="con1">
  <type>
    <BOOL/>
  </type>
  <initialValue>
    <simpleValue value="true"/>
  </initialValue>
</variable>
"""
class SimpleValue:
    def __init__(self, element=None):
        if element is not None:
            self.value = element.attrib.get('value')

    def __repr__(self):
        return f"SimpleValue(value={self.value})"

    def to_xml(self):
        element = ET.Element('simpleValue')
        element.set('value', self.value)
        return element

class InitialValue:
    def __init__(self, element=None, simpleValue=None):
        if element is not None:
            self.simpleValue = SimpleValue(element.find('simpleValue'))
        else:
            self.simpleValue = simpleValue

    def __repr__(self):
        return f"InitialValue(simpleValue={self.simpleValue})"

    def to_xml(self):
        element = ET.Element('initialValue')
        element.append(self.simpleValue.to_xml())
        return element
    
class Variable:
    def __init__(self, name=None, address=None, formalParameter=None, varType=None):
        self.name = name
        self.address = address
        self.formalParameter = formalParameter
        self.varType = varType
        self.type = None
        self.initialValue = None
        self.connectionPointIn = None
        self.connectionPointOut = None
    def __repr__(self):
        return f"Variable(name={self.name}, formalParameter={self.formalParameter}, varType={self.varType}, type={self.type})"
    def to_xml(self):
        if self.name is not None:
            var_element = ET.Element('variable')
            var_element.set('name', self.name)
            if self.type is not None:
                type_element = ET.SubElement(var_element, 'type')
                type_element.append(self.type.to_xml())
        elif self.formalParameter is not None:
            var_element = ET.Element('variable')
            var_element.set('formalParameter', self.formalParameter)
            if self.connectionPointIn is not None:
                var_element.append(self.connectionPointIn.to_xml('connectionPointIn'))
            if self.connectionPointOut is not None:
                var_element.append(self.connectionPointOut.to_xml('connectionPointOut'))
        return var_element

class Type:
    def __init__(self, element=None, typeName=None):
        if element is not None:
            if element.tag.lower() == "derived":
                self.typeName = "derived"
                self.derivedName = element.attrib.get("name")
            else:
                self.typeName = element.tag
                self.derivedName = None
        else:
            self.typeName = typeName
            self.derivedName = None

    def __repr__(self):
        if self.typeName == "derived":
            return f"Type(derivedName={self.derivedName})"
        return f"Type(typeName={self.typeName})"

    def to_xml(self):
        if self.typeName == "derived":
            element = ET.Element("derived")
            element.set("name", self.derivedName if self.derivedName else "")
            return element
        else:
            return ET.Element(self.typeName)
        
class Connection:
    def __init__(self, refLocalId, formalParameter=None):
        self.refLocalId = refLocalId
        self.formalParameter = formalParameter
        self.positions = []
    def __repr__(self):
        return f"Connection(refLocalId={self.refLocalId}, formalParameter={self.formalParameter}, positions={self.positions})"
    def to_xml(self):
        connection_element = ET.Element('connection')
        connection_element.set('refLocalId', self.refLocalId)
        if self.formalParameter:
            connection_element.set('formalParameter', self.formalParameter)
        for pos in self.positions:
            connection_element.append(pos.to_xml())
        return connection_element
    
def parse_position(element):
    x = element.get('x', '0')
    y = element.get('y', '0')
    return Position(x, y)

def parse_connectionPointOut(element):
    formalParameter = element.get('formalParameter')
    cpo = ConnectionPointOut(formalParameter=formalParameter)
    relPos_el = element.find('relPosition')
    if relPos_el is not None:
        cpo.relPosition = RelPosition(relPos_el.get('x', '0'), relPos_el.get('y', '0'))
    expr_el = element.find('expression')
    if expr_el is not None and expr_el.text is not None:
        cpo.expression = Expression(expr_el.text)
    return cpo

def parse_connectionPointIn(element):
    cpi = ConnectionPointIn()
    relPos_el = element.find('relPosition')
    if relPos_el is not None:
        cpi.relPosition = RelPosition(relPos_el.get('x', '0'), relPos_el.get('y', '0'))
    for connection_el in element.findall('connection'):
        conn = Connection(
            refLocalId=connection_el.get('refLocalId'),
            formalParameter=connection_el.get('formalParameter')
        )
        for pos_el in connection_el.findall('position'):
            conn.positions.append(parse_position(pos_el))
        cpi.connections.append(conn)
    return cpi

# -----------------------------
# Classes with Integrated Parsing
# -----------------------------

class Position:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)
    def to_xml(self):
        position = ET.Element('position')
        position.set('x', str(self.x))
        position.set('y', str(self.y))
        return position
    def __repr__(self):
        return f"Position(x={self.x}, y={self.y})"

class Interface:
    def __init__(self):
        self.inputVars = []
        self.localVars = []
        self.outputVars = []
        self.externalVars = []
    def __repr__(self):
        return f"Interface(localVars={self.localVars})"
    def to_xml(self):
        interface_element = ET.Element('interface')
        if self.inputVars:
            inputVars_element = ET.SubElement(interface_element, 'inputVars')
            for var in self.inputVars:
                inputVars_element.append(var.to_xml())
        if self.localVars:
            localVars_element = ET.SubElement(interface_element, 'localVars')
            for var in self.localVars:
                localVars_element.append(var.to_xml())
        if self.outputVars:
            outputVars_element = ET.SubElement(interface_element, 'outputVars')
            for var in self.outputVars:
                outputVars_element.append(var.to_xml())
        if self.externalVars:
            externalVars_element = ET.SubElement(interface_element, 'externalVars')
            for var in self.externalVars:
                externalVars_element.append(var.to_xml())
        return interface_element
    @classmethod
    def parse(cls, element):
        interface = cls()  # Create a new Interface instance
        for var_section in ['inputVars', 'localVars', 'outputVars', 'externalVars']:
            section_el = element.find(var_section)
            if section_el is not None:
                var_list = []
                for var_el in section_el.findall('variable'):
                    var_name = var_el.get('name')
                    var = Variable(name=var_name)
                    type_el = var_el.find('type')
                    if type_el is not None:
                        type_child = list(type_el)
                        if type_child:
                            var.type = Type(element=type_child[0])
                    var_list.append(var)
                setattr(interface, var_section, var_list)
        return interface

class POU:
    def __init__(self, name, pouType):
        self.name = name
        self.pouType = pouType
        self.interface = None
        self.body = None
    def __repr__(self):
        return f"POU(name={self.name}, pouType={self.pouType}, interface={self.interface}, body={self.body})"
    def to_xml(self):
        pou_element = ET.Element('pou')
        pou_element.set('name', self.name)
        pou_element.set('pouType', self.pouType)
        if self.interface is not None:
            pou_element.append(self.interface.to_xml())
        if self.body is not None:
            pou_element.append(self.body.to_xml())
        return pou_element

class LD:
    def __init__(self):
        self.elements = []
    def __repr__(self):
        return f"LD(elements={self.elements})"
    def to_xml(self):
        ld_element = ET.Element('LD')
        for elem in self.elements:
            ld_element.append(elem.to_xml())
        return ld_element
    @classmethod
    def parse(cls, ld_element):
        ld_obj = cls()
        for child in ld_element:
            if child.tag == 'leftPowerRail':
                ld_obj.elements.append(LeftPowerRail.parse(child))
            elif child.tag == 'rightPowerRail':
                ld_obj.elements.append(RightPowerRail.parse(child))
            elif child.tag == 'contact':
                ld_obj.elements.append(Contact.parse(child))
            elif child.tag == 'comment':
                ld_obj.elements.append(Comment.parse(child))
            elif child.tag == 'block':
                ld_obj.elements.append(Block.parse(child))
            elif child.tag == 'inVariable':
                ld_obj.elements.append(InVariable.parse(child))
            elif child.tag == 'outVariable':
                ld_obj.elements.append(OutVariable.parse(child))
            elif child.tag == 'coil':
                ld_obj.elements.append(Coil.parse(child))
        return ld_obj

class LeftPowerRail:
    def __init__(self, localId, height, width):
        self.localId = localId
        self.height = int(height)
        self.width = int(width)
        self.position = None
        self.connectionPointOut = None
    def __repr__(self):
        return f"LeftPowerRail(localId={self.localId}, height={self.height}, width={self.width}, position={self.position}, connectionPointOut={self.connectionPointOut})"
    def to_xml(self):
        lpr_element = ET.Element('leftPowerRail')
        lpr_element.set('localId', self.localId)
        lpr_element.set('height', str(self.height))
        lpr_element.set('width', str(self.width))
        if self.position is not None:
            lpr_element.append(self.position.to_xml())
        if self.connectionPointOut is not None:
            cpo_element = self.connectionPointOut.to_xml('connectionPointOut')
            lpr_element.append(cpo_element)
        return lpr_element
    @classmethod
    def parse(cls, element):
        localId = element.get('localId')
        height = element.get('height', '100')
        width = element.get('width', '5')
        lpr = cls(localId, height, width)
        pos_el = element.find('position')
        if pos_el is not None:
            lpr.position = parse_position(pos_el)
        cpo_el = element.find('connectionPointOut')
        if cpo_el is not None:
            lpr.connectionPointOut = parse_connectionPointOut(cpo_el)
        try:
            id_val = int(localId)
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return lpr

class RightPowerRail:
    def __init__(self, localId, height, width):
        self.localId = localId
        self.height = int(height)
        self.width = int(width)
        self.position = None
        self.connectionPointIn = None
    def __repr__(self):
        return f"RightPowerRail(localId={self.localId}, height={self.height}, width={self.width}, position={self.position}, connectionPointIn={self.connectionPointIn})"
    def to_xml(self):
        rpr_element = ET.Element('rightPowerRail')
        rpr_element.set('localId', self.localId)
        rpr_element.set('height', str(self.height))
        rpr_element.set('width', str(self.width))
        if self.position is not None:
            rpr_element.append(self.position.to_xml())
        if self.connectionPointIn is not None:
            rpr_element.append(self.connectionPointIn.to_xml('connectionPointIn'))
        return rpr_element
    @classmethod
    def parse(cls, element):
        localId = element.get('localId')
        height = element.get('height', '20')
        width = element.get('width', '30')
        rpr = cls(localId, height, width)
        pos_el = element.find('position')
        if pos_el is not None:
            rpr.position = parse_position(pos_el)
        cpi_el = element.find('connectionPointIn')
        if cpi_el is not None:
            rpr.connectionPointIn = parse_connectionPointIn(cpi_el)
        try:
            id_val = int(localId)
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return rpr

class Contact:
    attrib_list = {
        'localId': (None, str),
        'negated': ('false', lambda x: 'true' if x.lower() == 'true' else 'false'),
        'width': ('40', int),
        'height': ('40', int),
        'storage': (None, str),
    }
    def __init__(self, **kwargs):
        for key, (default, conv) in self.attrib_list.items():
            value = kwargs.get(key, default)
            setattr(self, key, conv(value) if value is not None else None)
        self.position = None
        self.connectionPointIn = None
        self.connectionPointOut = None
        self.variable = None
    def __repr__(self):
        return f"Contact(localId={self.localId}, negated={self.negated}, width={self.width}, height={self.height}, position={self.position}, connectionPointIn={self.connectionPointIn}, connectionPointOut={self.connectionPointOut}, variable={self.variable})"
    def to_xml(self):
        contact_element = ET.Element('contact')
        for key, (default, conv) in self.attrib_list.items():
            value = getattr(self, key)
            if value is not None:
                contact_element.set(key, str(value))
        if self.position is not None:
            contact_element.append(self.position.to_xml())
        if self.connectionPointIn is not None:
            contact_element.append(self.connectionPointIn.to_xml('connectionPointIn'))
        if self.connectionPointOut is not None:
            contact_element.append(self.connectionPointOut.to_xml('connectionPointOut'))
        if self.variable is not None:
            var_element = ET.SubElement(contact_element, 'variable')
            var_element.text = self.variable
        return contact_element
    @classmethod
    def parse(cls, element):
        kwargs = {}
        for key, (default, conv) in cls.attrib_list.items():
            kwargs[key] = element.get(key, default)
        contact = cls(**kwargs)
        pos_el = element.find('position')
        if pos_el is not None:
            contact.position = parse_position(pos_el)
        cpi_el = element.find('connectionPointIn')
        if cpi_el is not None:
            contact.connectionPointIn = parse_connectionPointIn(cpi_el)
        cpo_el = element.find('connectionPointOut')
        if cpo_el is not None:
            contact.connectionPointOut = parse_connectionPointOut(cpo_el)
        variable_el = element.find('variable')
        if variable_el is not None:
            contact.variable = variable_el.text
        try:
            id_val = int(kwargs['localId'])
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return contact

class Coil:
    attrib_list = {
        'localId': (None, str),
        'negated': ('false', lambda x: 'true' if x.lower() == 'true' else 'false'),
        'width': ('40', int),
        'height': ('40', int),
        'storage': (None, str),
    }
    def __init__(self, **kwargs):
        for key, (default, conv) in self.attrib_list.items():
            value = kwargs.get(key, default)
            setattr(self, key, conv(value) if value is not None else None)
        self.position = None
        self.connectionPointIn = None
        self.connectionPointOut = None
        self.variable = None
    def __repr__(self):
        return f"Coil(localId={self.localId}, negated={self.negated}, width={self.width}, height={self.height}, storage={self.storage}, position={self.position}, connectionPointIn={self.connectionPointIn}, connectionPointOut={self.connectionPointOut}, variable={self.variable})"
    def to_xml(self):
        coil_element = ET.Element('coil')
        for key, (default, conv) in self.attrib_list.items():
            value = getattr(self, key)
            if value is not None:
                coil_element.set(key, str(value))
        if self.position is not None:
            coil_element.append(self.position.to_xml())
        if self.connectionPointIn is not None:
            coil_element.append(self.connectionPointIn.to_xml('connectionPointIn'))
        if self.connectionPointOut is not None:
            coil_element.append(self.connectionPointOut.to_xml('connectionPointOut'))
        if self.variable is not None:
            var_element = ET.SubElement(coil_element, 'variable')
            var_element.text = self.variable
        return coil_element
    @classmethod
    def parse(cls, element):
        kwargs = {}
        for key, (default, conv) in cls.attrib_list.items():
            kwargs[key] = element.get(key, default)
        coil = cls(**kwargs)
        pos_el = element.find('position')
        if pos_el is not None:
            coil.position = parse_position(pos_el)
        cpi_el = element.find('connectionPointIn')
        if cpi_el is not None:
            coil.connectionPointIn = parse_connectionPointIn(cpi_el)
        cpo_el = element.find('connectionPointOut')
        if cpo_el is not None:
            coil.connectionPointOut = parse_connectionPointOut(cpo_el)
        variable_el = element.find('variable')
        if variable_el is not None:
            coil.variable = variable_el.text
        try:
            id_val = int(kwargs['localId'])
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return coil

class Comment:
    def __init__(self, localId, height, width):
        self.localId = localId
        self.height = int(height)
        self.width = int(width)
        self.position = None
        self.content = None
    def __repr__(self):
        content = ET.tostring(self.content, encoding="unicode") if self.content is not None else None
        return f"Comment(localId={self.localId}, height={self.height}, width={self.width}, position={self.position}, content={content})"
    def to_xml(self):
        comment_element = ET.Element('comment')
        comment_element.set('localId', self.localId)
        comment_element.set('height', str(self.height))
        comment_element.set('width', str(self.width))
        if self.position is not None:
            comment_element.append(self.position.to_xml())
        if self.content is not None:
            comment_element.append(self.content)
        return comment_element
    @classmethod
    def parse(cls, element):
        localId = element.get('localId')
        height = element.get('height', '20')
        width = element.get('width', '30')
        comment = cls(localId, height, width)
        pos_el = element.find('position')
        if pos_el is not None:
            comment.position = parse_position(pos_el)
        content_el = element.find('content')
        if content_el is not None:
            comment.content = content_el
        try:
            id_val = int(localId)
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return comment

class RelPosition:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)
    def __repr__(self):
        return f"RelPosition(x={self.x}, y={self.y})"
    def to_xml(self):
        relPos_element = ET.Element('relPosition')
        relPos_element.set('x', str(self.x))
        relPos_element.set('y', str(self.y))
        return relPos_element

class ConnectionPointOut:
    def __init__(self, formalParameter=None):
        self.formalParameter = formalParameter
        self.relPosition = None
        self.expression = None
    def __repr__(self):
        return f"ConnectionPointOut(formalParameter={self.formalParameter}, relPosition={self.relPosition}, expression={self.expression})"
    def to_xml(self, tag_name='connectionPointOut'):
        cpo_element = ET.Element(tag_name)
        if self.formalParameter:
            cpo_element.set('formalParameter', self.formalParameter)
        if self.relPosition is not None:
            cpo_element.append(self.relPosition.to_xml())
        return cpo_element

class ConnectionPointIn:
    def __init__(self):
        self.relPosition = None
        self.connections = []
    def __repr__(self):
        return f"ConnectionPointIn(relPosition={self.relPosition}, connections={self.connections})"
    def to_xml(self, tag_name='connectionPointIn'):
        cpi_element = ET.Element(tag_name)
        if self.relPosition is not None:
            cpi_element.append(self.relPosition.to_xml())
        for conn in self.connections:
            cpi_element.append(conn.to_xml())
        return cpi_element



class Block:
    attrb_list = {
        'localId': (None, str),
        'typeName': (None, str),
        'height': ('20', int),
        'width': ('30', int),
        'instanceName': (None, str),
    }
    def __init__(self, **kwargs):
        for key, (default, conv) in self.attrb_list.items():
            value = kwargs.get(key, default)
            setattr(self, key, conv(value) if value is not None else None)
        self.position = None
        self.inOutVariables = []
        self.inputVariables = []
        self.outputVariables = []
    def __repr__(self):
        return f"Block(localId={self.localId}, typeName={self.typeName}, instanceName={self.instanceName}, height={self.height}, width={self.width}, position={self.position}, inputVariables={self.inputVariables}, outputVariables={self.outputVariables})"
    def to_xml(self):
        block_element = ET.Element('block')
        block_element.set('localId', self.localId)
        block_element.set('typeName', self.typeName)
        block_element.set('height', str(self.height))
        block_element.set('width', str(self.width))
        if self.instanceName is not None:
            block_element.set('instanceName', self.instanceName)
        if self.position is not None:
            block_element.append(self.position.to_xml())
        inputVars_element = ET.SubElement(block_element, 'inputVariables')
        if self.inputVariables:
            for var in self.inputVariables:
                inputVars_element.append(var.to_xml())
        inOutVars_element = ET.SubElement(block_element, 'inOutVariables')
        if self.inOutVariables:
            for var in self.inOutVariables:
                inOutVars_element.append(var.to_xml())
        outputVars_element = ET.SubElement(block_element, 'outputVariables')
        if self.outputVariables:
            for var in self.outputVariables:
                outputVars_element.append(var.to_xml())
        return block_element
    @classmethod
    def parse(cls, element):
        kwargs = {}
        for key, (default, conv) in cls.attrb_list.items():
            kwargs[key] = element.get(key, default)
        block = cls(**kwargs)
        pos_el = element.find('position')
        if pos_el is not None:
            block.position = parse_position(pos_el)
        inputVars_el = element.find('inputVariables')
        if inputVars_el is not None:
            for var_el in inputVars_el.findall('variable'):
                var = Variable(formalParameter=var_el.get('formalParameter'))
                cp_in_el = var_el.find('connectionPointIn')
                if cp_in_el is not None:
                    var.connectionPointIn = parse_connectionPointIn(cp_in_el)
                block.inputVariables.append(var)
        outputVars_el = element.find('outputVariables')
        if outputVars_el is not None:
            for var_el in outputVars_el.findall('variable'):
                var = Variable(formalParameter=var_el.get('formalParameter'))
                cp_out_el = var_el.find('connectionPointOut')
                if cp_out_el is not None:
                    var.connectionPointOut = parse_connectionPointOut(cp_out_el)
                block.outputVariables.append(var)
        inoutVars_el = element.find('inOutVariables')
        if inoutVars_el is not None:
            for var_el in inoutVars_el.findall('variable'):
                var = Variable(formalParameter=var_el.get('formalParameter'))
                cp_in_el = var_el.find('connectionPointIn')
                if cp_in_el is not None:
                    var.connectionPointIn = parse_connectionPointIn(cp_in_el)
                cp_out_el = var_el.find('connectionPointOut')
                if cp_out_el is not None:
                    var.connectionPointOut = parse_connectionPointOut(cp_out_el)
                block.inOutVariables.append(var)
        try:
            id_val = int(kwargs['localId'])
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return block

    def get_expressions(self) -> list:
        # TBD: Don't know if inoutVariables have expressions
        exps = []
        for var in self.outputVariables:
            if var.connectionPointOut is not None and var.connectionPointOut.expression is not None:
                exp = var.connectionPointOut.expression.text
                logger.debug(f"Found expression: {exp}")
                exps.append(exp)
        return exps
    
class InVariable:
    def __init__(self, localId, height, width, negated):
        self.localId = localId
        self.height = int(height)
        self.width = int(width)
        self.negated = (negated == 'true')
        self.position = None
        self.connectionPointOut = None
        self.expression = None
    def __repr__(self):
        return f"InVariable(localId={self.localId}, height={self.height}, width={self.width}, negated={self.negated}, position={self.position}, connectionPointOut={self.connectionPointOut}, expression={self.expression})"
    def to_xml(self):
        inVar_element = ET.Element('inVariable')
        inVar_element.set('localId', self.localId)
        inVar_element.set('height', str(self.height))
        inVar_element.set('width', str(self.width))
        inVar_element.set('negated', 'true' if self.negated else 'false')
        if self.position is not None:
            inVar_element.append(self.position.to_xml())
        if self.connectionPointOut is not None:
            cpo_element = self.connectionPointOut.to_xml('connectionPointOut')
            inVar_element.append(cpo_element)
        if self.expression is not None:
            expr_element = ET.SubElement(inVar_element, 'expression')
            expr_element.text = self.expression.text
        return inVar_element
    @classmethod
    def parse(cls, element):
        localId = element.get('localId')
        height = element.get('height', '20')
        width = element.get('width', '30')
        negated = element.get('negated', 'false')
        inVar = cls(localId, height, width, negated)
        pos_el = element.find('position')
        if pos_el is not None:
            inVar.position = parse_position(pos_el)
        cpo_el = element.find('connectionPointOut')
        if cpo_el is not None:
            inVar.connectionPointOut = parse_connectionPointOut(cpo_el)
        expr_el = element.find('expression')
        if expr_el is not None and expr_el.text is not None:
            inVar.expression = Expression(expr_el.text)
        try:
            id_val = int(localId)
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return inVar

class OutVariable:
    def __init__(self, localId, height, width, negated):
        self.localId = localId
        self.height = int(height)
        self.width = int(width)
        self.negated = (negated == 'true')
        self.position = Position(0, 0)
        self.connectionPointIn = None
        self.expression = None
    def __repr__(self):
        return f"OutVariable(localId={self.localId}, height={self.height}, width={self.width}, negated={self.negated}, position={self.position}, connectionPointIn={self.connectionPointIn}, expression={self.expression})"
    def to_xml(self):
        outVar_element = ET.Element('outVariable')
        outVar_element.set('localId', str(self.localId))
        outVar_element.set('height', str(self.height))
        outVar_element.set('width', str(self.width))
        outVar_element.set('negated', 'true' if self.negated else 'false')
        if self.position is not None:
            outVar_element.append(self.position.to_xml())
        if self.connectionPointIn is not None:
            cpi_element = self.connectionPointIn.to_xml('connectionPointIn')
            outVar_element.append(cpi_element)
        if self.expression is not None:
            expr_element = ET.SubElement(outVar_element, 'expression')
            expr_element.text = self.expression.text
        return outVar_element
    @classmethod
    def parse(cls, element):
        localId = element.get('localId')
        height = element.get('height', '20')
        width = element.get('width', '30')
        negated = element.get('negated', 'false')
        outVar = cls(localId, height, width, negated)
        pos_el = element.find('position')
        if pos_el is not None:
            outVar.position = parse_position(pos_el)
        cpi_el = element.find('connectionPointIn')
        if cpi_el is not None:
            outVar.connectionPointIn = parse_connectionPointIn(cpi_el)
        expr_el = element.find('expression')
        if expr_el is not None and expr_el.text is not None:
            outVar.expression = Expression(expr_el.text)
        try:
            id_val = int(localId)
            global_max_id = get_value()
            if id_val > global_max_id:
                set_value(id_val)
        except Exception:
            pass
        return outVar

class Expression:
    def __init__(self, text):
        self.text = text
    def __repr__(self):
        return f"Expression(text={self.text})"