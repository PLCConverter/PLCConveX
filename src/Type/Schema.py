import sys
sys.path.append("../")


import xml.etree.ElementTree as ET
from LD.Schema.Elements import Type, Variable



""" typical schema for a data type 
<dataTypes>
      <dataType name="_sDT">
        <baseType>
          <struct>
            <variable name="year">
              <type>
                <DINT/>
              </type>
            </variable>
            <variable name="month">
              <type>
                <DINT/>
              </type>
            </variable>
            <variable name="day">
              <type>
                <DINT/>
              </type>
            </variable>
            <variable name="hour">
              <type>
                <DINT/>
              </type>
            </variable>
            <variable name="minute">
              <type>
                <DINT/>
              </type>
            </variable>
            <variable name="second">
              <type>
                <DINT/>
              </type>
            </variable>
          </struct>
        </baseType>
      </dataType>
    <dataTypes>
"""
class Struct:
    def __init__(self):
        self.variables = []
    def add_variable(self, variable):
        self.variables.append(variable)
    def to_xml(self):
        struct_element = ET.Element('struct')
        for variable in self.variables:
            struct_element.append(variable.to_xml())
        return struct_element
    @classmethod
    def parse(cls, element):
        struct = cls()
        for variable_element in element.findall('variable'):
            struct.add_variable(Variable.parse(variable_element))
        return struct
    
class BaseType:
    def __init__(self):
        self.struct = None
    def to_xml(self):
        baseType_element = ET.Element('baseType')
        if self.struct is None:
            raise ValueError("Struct is not set")
        baseType_element.append(self.struct.to_xml())
        return baseType_element
    @classmethod
    def parse(cls, element):
        baseType = cls()
        baseType.struct = Struct.parse(element.find('struct'))
        return baseType
    
class DataType:
    def __init__(self, name):
        self.name = name
        self.baseType = None
    def to_xml(self):
        dataType_element = ET.Element('dataType')
        dataType_element.set('name', self.name)
        if self.baseType is None:
            raise ValueError("Base type is not set")
        dataType_element.append(self.baseType.to_xml())
        return dataType_element
    @classmethod
    def parse(cls, element):
        name = element.get('name')
        dataType = cls(name)
        dataType.baseType = BaseType.parse(element.find('baseType'))
        return dataType

class DataTypes:
    def __init__(self):
        self.dataTypes = []
    def add_dataType(self, dataType):
        self.dataTypes.append(dataType)
    def to_xml(self):
        dataTypes_element = ET.Element('dataTypes')
        for dataType in self.dataTypes:
            dataTypes_element.append(dataType.to_xml())
        return dataTypes_element
    @classmethod
    def parse(cls, element):
        dts = cls()
        for dataType_element in element.findall('dataType'):
            dts.add_dataType(DataType.parse(dataType_element))
        return dts