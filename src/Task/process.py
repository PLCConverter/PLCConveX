import sys
sys.path.append("..")

import xml.etree.ElementTree as ET

from Logs.colorLogger import get_color_logger
logger = get_color_logger("Task/process.py")

DEFAULT_INPUT_FILE = "Task/Inputs/tasks.xml"
DEFAULT_OUTPUT_FILE = "Task/Outputs/tasks.xml"

"""
      <task name="ETHERCAT" interval="PT0.004S" priority="0">
        <pouInstance name="ETHERCAT.EtherCAT_Task" typeName="">
          <documentation>
            <xhtml xmlns="http://www.w3.org/1999/xhtml" />
          </documentation>
        </pouInstance>
        <pouInstance name="Axis_Ctrl" typeName="">
          <documentation>
            <xhtml xmlns="http://www.w3.org/1999/xhtml" />
          </documentation>
        </pouInstance>
"""
class Task:
    def __init__(self, name, interval, priority):
        self.name = name
        self.interval = interval
        self.priority = priority
        self.pouInstances = []
    
    def add_pou_instance(self, pou_instance):
        self.pouInstances.append(pou_instance)
    
    def to_xml(self):
        task_element = ET.Element('task')
        task_element.set('name', self.name)
        task_element.set('interval', self.interval)
        task_element.set('priority', self.priority)
        for pou_instance in self.pouInstances:
            task_element.append(pou_instance.to_xml())
        return task_element
    
    @classmethod
    def parse(cls, element):
        name = element.get('name')
        interval = element.get('interval')
        priority = element.get('priority')
        task = cls(name, interval, priority)
        for pou_instance_element in element.findall('pouInstance'):
            task.add_pou_instance(PouInstance.parse(pou_instance_element))
        return task

class PouInstance:
    def __init__(self, name, typeName):
        self.name = name
        self.typeName = typeName
    
    def to_xml(self):
        pou_instance_element = ET.Element('pouInstance')
        pou_instance_element.set('name', self.name)
        pou_instance_element.set('typeName', self.typeName)
        return pou_instance_element
    
    @classmethod
    def parse(cls, element):
        name = element.get('name')
        typeName = element.get('typeName')
        return cls(name, typeName)
    
def main(input_file = DEFAULT_INPUT_FILE, output_file = DEFAULT_OUTPUT_FILE):
    tree = ET.parse(input_file)
    root = tree.getroot()

    task_elements = root.find("task")