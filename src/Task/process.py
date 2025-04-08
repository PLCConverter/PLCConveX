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

def preprocess_tasks(root: ET.Element) -> None:
    if root.tag != "task":
        logger.error("Root tag is not 'task'. Failed to extract task.")
        return

    
def deal_task(root: ET.Element) -> None:
    if root.tag != "task":
        logger.error("Root tag is not 'task'. Failed to extract task.")
        return

    task = Task.parse(root)
    logger.debug(task.interval)

    # convert the time representation
    task.interval = task.interval.replace("PT", "T#")
    # Beremiz: set the typename to be the same as pouInsance name
    for pou_instance in task.pouInstances:
        # find if '.' is in the name
        if '.' in pou_instance.name:
            logger.warning(f"'{pou_instance.name}' maybe platform specific, please check")
            # prompt the user to check the name
            # user must input y to continue
            # default to 'y'
            user_input = input(f"'{pou_instance.name}' maybe platform specific, please check. Do you want to continue? (y/n) [y]: ")
            if user_input == '':
                user_input = 'y'
            if user_input != 'y':
                logger.error("User input is not 'y', exiting...")
                sys.exit(1)
            else:
                pou_instance.name = pou_instance.name.replace(".", "_")

        pou_instance.typeName = pou_instance.name
        pou_instance.name = "INST_" + pou_instance.name

    return task     

def main(input_file = DEFAULT_INPUT_FILE, output_file = DEFAULT_OUTPUT_FILE):
    # create a <resource> element for output XML's root
    out_root = ET.Element('resource')

    tree = ET.parse(input_file)
    root = tree.getroot()

    task_elements = root.findall(".//task")
    if not task_elements:
        logger.warning("No task elements found")
        return None
    
    for task_element in task_elements:
        task = deal_task(task_element)
        if task is None:
            logger.warning("No task found")
            return None
        out_root.append(task.to_xml())

    # write to file
    logger.info(f"Writing to {output_file}")
    ET.ElementTree(out_root).write(output_file, encoding='utf-8', xml_declaration=False)    