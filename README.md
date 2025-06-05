## About
This repository provides a tool for PLC code conversion. Specifically, it converts the whole PLC project from CODESYS(exported as PLCopen XML) to a project file that can be loaded into openPLC or Beremiz. For now, it only supports LD and ST languages, and some features in CODESYS are not supported, such as action block in ST.

## How to deploy

You should install `uv` first, with suitable python environment (version 3.8 or above).

### Windows 
```shell
uv venv 
.venv\Scripts\activate
uv sync
```

### Linux
```bash
uv venv
source venv/bin/activate
uv sync
```

## How to use
First, you should guarantee that your CODESYS (or other IDE based on CODESYS, like inoProshop) is capable of exporting PLCopen XML. (Version 3.2 or above is recommended)

Then, you can run the following command to convert your PLC project:

### Windows 
```shell
.venv\Scripts\activate
cd src
uv run poe pipeline -i <input_file_path>
```

The default result path is `data/Outputs/plc.xml`, you can directly open it with openPLC or Beremiz.