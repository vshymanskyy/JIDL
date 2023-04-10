__author__    = "Volorymyr Shymanskyy"
__copyright__ = "Copyright 2023, Volodymyr Shymanskyy"
__license__   = "Apache-2.0"
__version__   = "0.1.0"

import json
import jsonschema
from pathlib import Path

script_path = Path(__file__).resolve().parent
schema_path = script_path / ".." / "schema"

# Load the IDL schema
with open(schema_path / "jidl-relaxed.json", "r") as f:
    idl_schema_relaxed = json.load(f)
with open(schema_path / "jidl-strict.json", "r") as f:
    idl_schema_strict = json.load(f)


def skip_attrs(d):
    return { k: v for k, v in d.items() if not k.startswith('@') }


def prepend_keys(d, keys):
    new_items = {k: v for k, v in keys.items() if k not in d}
    new_items.update(d)
    d.clear()
    d.update(new_items)

def normalize_idl(idl):
    def expand_attrs(obj):
        if "@attrs" in obj:
            for attr in obj["@attrs"]:
                obj[f"@{attr}"] = True
            del obj["@attrs"]

    if "@output_dir" not in idl:
        idl["@output_dir"] = "./output"

    if "types" not in idl:
        idl["types"] = {}

    if "interfaces" not in idl:
        idl["interfaces"] = {}

    for name, data in idl["types"].items():
        if isinstance(data, str):
            idl["types"][name] = { "type": "alias", "for": data }
        expand_attrs(data)

    for interface in idl["interfaces"].values():
        expand_attrs(interface)
        for func_name, func in skip_attrs(interface).items():
            if "@TODO" in func:
                del interface[func_name]
                continue

            expand_attrs(func)
            if "args" not in func:
                func["args"] = []
            for arg in func["args"]:
                expand_attrs(arg)
                if "name" not in arg:
                    # Find name
                    [name] = [key for key, val in arg.items() if not key.startswith("@")]
                    prepend_keys(arg, { "name": name, "type": arg[name] })
                    if name != "type":
                        del arg[name]
                if "@dir" not in arg:
                    arg["@dir"] = "in"

            if "returns" not in func:
                func["returns"] = None
            elif isinstance(func["returns"], str):
                func["returns"] = { "type" : func["returns"] }
            else:
                expand_attrs(func["returns"])

def save_strict(idl):
    from compact_json import Formatter, EolStyle

    formatter = Formatter()
    formatter.indent_spaces = 2
    formatter.max_inline_complexity = 1
    formatter.json_eol_style = EolStyle.LF

    with open("_strict.idl.json", "w") as f:
        f.write(formatter.serialize(idl))

def process(idl):
    def handleValidationError(e):
        print(f"{e.json_path}: {e.message}")
        print(f"Schema rule:\n{'.'.join(e.schema_path)}")
        sys.exit(1)

    try:
        jsonschema.validate(instance=idl, schema=idl_schema_relaxed)
    except jsonschema.ValidationError as e:
        handleValidationError(e)

    # Normalize
    normalize_idl(idl)
    save_strict(idl)

    try:
        jsonschema.validate(instance=idl, schema=idl_schema_strict)
    except jsonschema.ValidationError as e:
        print()
        print("  -> Strict schema validation failed after normalization! <-")
        print("  This is most probably a JIDL bug, please report it via GitHub Issues")
        print()
        handleValidationError(e)

    return idl

def load(f):
    return process(json.load(f))

def loads(data):
    return process(json.loads(f))
