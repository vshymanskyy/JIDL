#!/usr/bin/env python3

__author__    = "Volorymyr Shymanskyy"
__copyright__ = "Copyright 2023, Volodymyr Shymanskyy"
__license__   = "Apache-2.0"
__version__   = "0.1.0"

import jidl
import jinja2
from pathlib import Path

jinja = jinja2.Environment(undefined=jinja2.StrictUndefined)
jinja.trim_blocks = True
jinja.lstrip_blocks = True

ctypes = {
  "Bool":     "bool",
  "Int8":     "int8_t",
  "Int16":    "int16_t",
  "Int32":    "int32_t",
  "Int64":    "int64_t",
  "UInt8":    "uint8_t",
  "UInt16":   "uint16_t",
  "UInt32":   "uint32_t",
  "UInt64":   "uint64_t",
  "Float32":  "float",
  "Float64":  "double",
  "Binary":   "buffer_t",
  "String":   "char*",
}

def c_type(t):
    if t is None:
        return "void"
    t = t["type"]
    if t in ctypes:
        return ctypes[t]
    raise Exception(f"Unknown type {t}")

def call_ser(b,acc,t,n):
    if t in ctypes:
        if t == "String":
            t = "cstring"
        else:
            t = ctypes[t].replace("_t","")
        return f"{b}{acc}write_{t}({n});"
    raise Exception(f"No serializer for {t}")

def call_deser(b,acc,t,n):
    if t in ctypes:
        if t == "String":
            t = "cstring"
        else:
            t = ctypes[t].replace("_t","")
        return f"{b}{acc}read_{t}({n});"
    raise Exception(f"No deserializer for {t}")

#
# Helpers
#

def skip_attrs(d):
    return { k: v for k, v in d.items() if not k.startswith('@') }

#
# Generators
#

tmpl_shim_func = jinja.from_string("""
static inline
{{function_ret}} rpc_{{interface_name}}_{{function_name}}({{ func_args|join(', ') }}) {
  MessageBuffer _rpc_buff(rpc_output_buff, sizeof(rpc_output_buff));
{% if attr_oneway %}
  _rpc_buff.write_uint16(RPC_OP_ONEWAY);
  _rpc_buff.write_uint16(RPC_UID_{{interface_name|upper}}_{{function_name|upper}});
{% else %}
  _rpc_buff.write_uint16(RPC_OP_INVOKE);
  _rpc_buff.write_uint16(RPC_UID_{{interface_name|upper}}_{{function_name|upper}});
  _rpc_buff.write_uint16(++_rpc_seq);
{% endif %}
{% if serialize_args|length > 0 %}

  // Serialize inputs
  {{ serialize_args|join('\n  ') }}
{% endif %}

  // RPC call
  rpc_send_msg(&_rpc_buff);

{% if not attr_oneway %}
  {% if ret_type %}
  {{function_ret}} _rpc_ret_val;
  memset(&_rpc_ret_val, 0, sizeof(_rpc_ret_val));

  {% endif %}
  MessageBuffer _rsp_buff(NULL, 0);
  RpcStatus _rpc_status = rpc_wait_result(_rpc_seq, &_rsp_buff{{attr_timeout}});
{% if deserialize_args|length > 0 %}
  if (_rpc_status == RPC_STATUS_OK) {
    // Deserialize outputs
    {{ deserialize_args|join('\n    ') }}
  }
{% else %}
  {% if not attr_ret_status %}
  (void)(_rpc_status);
  {% endif %}
{% endif %}

  {% if attr_ret_status %}
  return _rpc_status;
  {% else %}
  // TODO; indicate error
  {% if ret_type %}
  return _rpc_ret_val;
  {% endif %}
  {% endif %}
{% else %}
  // Oneway => skip response
{% endif %}
}
""")

def gen_client_shim(interface_name, function_name, function):
    func_args = []
    serialize_args = []
    deserialize_args = []

    for arg in function["args"]:
        arg_name = arg["name"]
        arg_type = arg["type"]
        arg_dir  = arg["@dir"]
        if arg_dir == "in":
            func_args.append(f"const {c_type(arg)} {arg_name}")
            serialize_args.append(call_ser("_rpc_buff", ".", arg_type, arg_name))
        elif arg_dir == "out":
            func_args.append(f"{c_type(arg)}* {arg_name}")
            deserialize_args.append(call_deser("_rsp_buff", ".", arg_type, arg_name))
        elif arg_dir == "inout":
            func_args.append(f"{c_type(arg)}* {arg_name}")
            serialize_args.append(call_ser("_rpc_buff", ".", arg_type, arg_name))
            deserialize_args.append(call_deser("_rsp_buff", ".", arg_type, arg_name))

    attr_ret_status = function.get("@c:ret_status", False)
    attr_oneway = function.get("@oneway", False)
    attr_timeout = f", {function['@timeout']}" if "@timeout" in function else ""
    if attr_ret_status:
        function_ret = "RpcStatus"
    else:
        function_ret = c_type(function["returns"])

    ret_type = function["returns"]
    if ret_type:
        if attr_ret_status:
            raise Exception("@c:ret_status used on a function with a return value")
        deserialize_args.append(call_deser("_rsp_buff", ".", ret_type["type"], "&_rpc_ret_val"))

    else:
        ret_str = ""

    return tmpl_shim_func.render(**locals())

tmpl_handler_func = jinja.from_string("""
static inline
void rpc_{{interface_name}}_{{function_name}}_handler(MessageBuffer* _rpc_buff) {
{% if deserialize_args|length > 0 %}
  // Deserialize inputs
  {{deserialize_args|join('\n  ')}}
{% endif %}

{% if not attr_no_impl %}
  // Call the actual function
  {{ret_val}}{{interface_name}}_{{function_name}}({{ func_args|join(', ') }});
{% endif %}

  // Serialize outputs
  _rpc_buff->reset();
  {{serialize_args|join('\n  ')}}
}
""")

def gen_server_handler(interface_name, function_name, function):
    func_args = []
    deserialize_args = []
    serialize_args = []

    for arg in function["args"]:
        arg_name = arg["name"]
        arg_type = arg["type"]
        arg_dir  = arg["@dir"]
        if arg_dir == "in":
            func_args.append(f"{arg_name}")
            deserialize_args.append(f"{c_type(arg)} {arg_name}; " + call_deser("_rpc_buff", "->", arg_type, f"&{arg_name}"))
        elif arg_dir == "out":
            func_args.append(f"&{arg_name}")
            deserialize_args.append(f"{c_type(arg)} {arg_name};")
            serialize_args.append(call_ser("_rpc_buff", "->", arg_type, arg_name))
        elif arg_dir == "inout":
            func_args.append(f"&{arg_name}")
            deserialize_args.append(call_deser("_rpc_buff", "->", arg_type, f"&{arg_name}"))
            serialize_args.append(call_ser("_rpc_buff", "->", arg_type, arg_name))

    ret_val = ""
    ret_type = function["returns"]
    if ret_type:
        ret_val = f"{c_type(ret_type)} _rpc_ret_val = "
        serialize_args.append(call_ser("_rpc_buff", "->", ret_type["type"], "_rpc_ret_val"))

    attr_no_impl = function.get("@no_impl", False)

    return tmpl_handler_func.render(**locals())

tmpl_header = jinja.from_string("""
{% set guard = filename|upper|replace(".","_") %}
/* This file is auto-generated. DO NOT EDIT. */

#ifndef {{guard}}
#define {{guard}}

{{content}}

#endif // {{guard}}
""")

def gen_c(idl):

    output_dir = Path(idl["@output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    for interface_name, interface in idl["interfaces"].items():
        client_shims = []
        server_handlers = []

        for function_name, function in skip_attrs(interface).items():
            client_shims.append(
                gen_client_shim(interface_name, function_name, function)
            )
            server_handlers.append(
                gen_server_handler(interface_name, function_name, function)
            )

        # Write client-side shims
        filename = f"rpc_shim_{interface_name}.h"
        with open(output_dir / filename, "w") as f:
            content = "\n\n".join(client_shims)
            f.write(tmpl_header.render(**locals()))
            f.write("\n")

        # Write server-side handlers
        filename = f"rpc_handler_{interface_name}.h"
        with open(output_dir / filename, "w") as f:
            content = "\n\n".join(server_handlers)
            f.write(tmpl_header.render(**locals()))
            f.write("\n")

        print(f"Generated interface {interface_name}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='JIDL to C++ generator')
    parser.add_argument('file_in',                 metavar='IN_FILE',  help='input file')
    args = parser.parse_args()

    with open(args.file_in, 'r') as f:
        idl = jidl.load(f)

    gen_c(idl)
