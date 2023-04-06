# JIDL

This is **Jiddle** - a `JSON`-based, simple and extensible `Interface Definition Language`

- [Documentation](./docs/JIDL.md)
- [Example IDLs](./examples)
- [JSON Schema](./jidl.schema.json)

## Rationale

A JSON-based Interface Definition Language (IDL) is a handy way to describe and communicate the structure of an application's interfaces, especially when it comes to Remote Procedure Calls (RPC). Using a JSON-based IDL offers some cool perks for developers:

1. **Language and tool-friendly format**: JSON works with tons of programming languages out of the box, which means it's easier to create tools for validation, conversion and code generation.
2. **Easy to read and write**: there's no need to learn yet another IDL syntax, so it's easier for developers to understand the interface definitions. Everyone can work together better and faster.
3. **Flexible and extensible**: developers can add new attributes or properties to the interface definitions whenever they need to. This means the IDL can grow and change with the application, supporting new features without causing any problems.

By using a JSON-based IDL, developers can take advantage of these benefits to create interfaces more effectively and efficiently. Plus, it's easier to work with tools and libraries that generate client-side and server-side code, documentation, and other goodies, making development even more productive and maintainable.

## Example IDL file

```json
{
  "module": "Calculator",
  "interfaces" : {
    "calc": {
      "@id": 1,
      "add": {
        "@doc": "Calculates c = a + b",
        "args": [
          { "name": "a", "type": "Int32" },
          { "name": "b", "type": "Int32" },
          { "name": "c", "type": "Int32", "@dir": "out" }
        ],
        "returns": "Int8"
      }
    }
  }
}
```

## `C/C++` RPC shims generation

```sh
pip install jsonschema jinja2

python3 jidl2c.py ./examples/Calculator.idl.json
```

Which produces:

```cpp
/* Server-side shim */
static inline
void rpc_calc_add_handler(MessageBuffer* _rpc_buff) {
  // Deserialize inputs
  int32_t a; _rpc_buff->read_int32(&a);
  int32_t b; _rpc_buff->read_int32(&b);
  int32_t c;

  // Call the actual function
  int8_t _rpc_ret_val = calc_add(a, b, &c);

  // Serialize outputs
  _rpc_buff->reset();
  _rpc_buff->write_int32(c);
  _rpc_buff->write_int8(_rpc_ret_val);
}

/* Client-side shim */
static inline
int8_t rpc_calc_add(int32_t a, int32_t b, int32_t *c) {
  //...

  // Serialize inputs
  _rpc_buff.write_int32(a);
  _rpc_buff.write_int32(b);

  // RPC call
  rpc_send_msg(&_rpc_buff);

  int8_t _rpc_ret_val;
  memset(_rpc_ret_val, 0, sizeof(_rpc_ret_val));

  MessageBuffer _rsp_buff(NULL, 0);
  RpcStatus _rpc_status = rpc_wait_result(_rpc_seq, &_rsp_buff);
  if (_rpc_status == RPC_STATUS_OK) {
    // Deserialize outputs
    _rsp_buff.read_int32(c);
    _rsp_buff.read_int8(&_rpc_ret_val);
    return _rpc_ret_val;
  }

  return _rpc_ret_val;
}
```
