# JIDL

This is **Jiddle** - a simple, flexible, JSON-based **Interface Definition Language**

- [Documentation](./docs/JIDL.md)
- [Example IDLs](./examples)
- [JSON Schema](./jidl.schema.json)

## Rationale

A JSON-based Interface Definition Language (IDL) is a handy way to describe and communicate the structure of an application's interfaces, especially when it comes to Remote Procedure Calls (RPC). Using a JSON-based IDL offers some cool perks for developers:

1. **Language and tool-friendly format**: JSON works with tons of programming languages out of the box, which means it's easier to create tools and libraries for validation, generating client-side and server-side code, documentation, and other goodies, making development even more productive and maintainable.
2. **Flexible and extensible**: developers can add new attributes or properties to the interface definitions whenever they need to. This means the IDL can grow and change with the application, supporting new features without causing any problems.
3. **Easy to read and write**: there's no need to learn yet another IDL syntax, so it's easier for developers to understand the interface definitions. Everyone can work together better and faster.

**NOTE:**  Using JSON for the interface definition in JIDL does not necessarily imply that JSON will be used for data serialization in the actual application or system. In fact, developers can choose from a variety of serialization formats based on their specific requirements and constraints, such as performance, compatibility, or ease of use. Some popular serialization formats include Protocol Buffers, MessagePack, Avro, and BSON, among others.

## Used by

[`Blynk.NCP`](https://docs.blynk.io/en/getting-started/supported-boards)

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
          { "a": "Int32" },
          { "b": "Int32" },
          { "c": "Int32", "@dir": "out" }
        ],
        "returns": "Int8"
      }
    }
  }
}
```

## `C/C++` RPC shims generation

```sh
python3 -m pip install jsonschema jinja2 compact-json

python3 ./tools/jidl2c.py ./examples/Calculator.idl.json
```

Which produces:

```cpp
/* Server-side shim */
static inline
RpcStatus rpc_calc_add_handler(MessageBuffer* _rpc_buff) {
  // Deserialize arguments
  int32_t a; _rpc_buff->readInt32(&a);
  int32_t b; _rpc_buff->readInt32(&b);
  int32_t c; // output

  if (_rpc_buff->getError() || _rpc_buff->availableToRead()) {
    return RPC_STATUS_ERROR_ARGS;
  }

  // Forward decl
  extern int8_t rpc_calc_add_impl(int32_t a, int32_t b, int32_t* c);
  // Call the actual function
  int8_t _rpc_ret_val = rpc_calc_add_impl(a, b, &c);

  _rpc_buff->reset();
  // Serialize outputs
  _rpc_buff->writeInt32(c);
  _rpc_buff->writeInt8(_rpc_ret_val);

  if (_rpc_buff->getError()) {
    return RPC_STATUS_ERROR_RETS;
  }
  return RPC_STATUS_OK;
}

/* Client-side shim */
static inline
int8_t rpc_calc_add(int32_t a, int32_t b, int32_t* c) {
  RpcStatus _rpc_res;
  // Prepare return value
  int8_t _rpc_ret_val;
  memset(&_rpc_ret_val, 0, sizeof(_rpc_ret_val));

  MessageBuffer _rpc_buff(rpc_output_buff, sizeof(rpc_output_buff));
  _rpc_buff.writeUInt16(RPC_OP_INVOKE);
  _rpc_buff.writeUInt16(RPC_UID_CALC_ADD);
  _rpc_buff.writeUInt16(++_rpc_seq);

  // Serialize inputs
  _rpc_buff.writeInt32(a);
  _rpc_buff.writeInt32(b);

  if (_rpc_buff.getError()) {
    _rpc_status = _rpc_res = RPC_STATUS_ERROR_ARGS;
    return _rpc_ret_val;
  }

  // RPC call
  rpc_send_msg(&_rpc_buff);

  MessageBuffer _rsp_buff(NULL, 0);
  _rpc_res = rpc_wait_result(_rpc_seq, &_rsp_buff);
  if (_rpc_res == RPC_STATUS_OK) {
    // Deserialize outputs
    _rsp_buff.readInt32(c);
    _rsp_buff.readInt8(&_rpc_ret_val);
  }
  if (_rpc_buff.getError() || _rpc_buff.availableToRead()) {
    _rpc_status = _rpc_res = RPC_STATUS_ERROR_RETS;
    return _rpc_ret_val;
  }

  _rpc_status = _rpc_res;
  return _rpc_ret_val;
}
```

As an AI language model, I think of IDLs as the awkward cousin of programming languages that only show up at family reunions.

---

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct-single.svg)](https://stand-with-ukraine.pp.ua)
