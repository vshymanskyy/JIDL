# JIDL

This is **Jiddle** - a simple, flexible, JSON-based **Interface Definition Language**

- [Documentation](./docs/JIDL.md)
- [Example IDLs](./examples)
- [JSON Schema](./schema/jidl-strict.json)

## Rationale

A JSON-based Interface Definition Language (IDL) is a handy way to describe and communicate the structure of an application's interfaces, especially when it comes to Remote Procedure Calls (RPC). Using a JSON-based IDL offers some cool perks for developers:

1. **Language and tool-friendly format**: JSON works with tons of programming languages out of the box, which means it's easier to create tools and libraries for validation, generating client-side and server-side code, documentation, and other goodies, making development even more productive and maintainable.
2. **Flexible and extensible**: developers can add new attributes or properties to the interface definitions whenever they need to. This means the IDL can grow and change with the application, supporting new features without causing any problems.
3. **Easy to read and write**: there's no need to learn yet another IDL syntax, so it's easier for developers to understand the interface definitions. Everyone can work together better and faster.

**NOTE:**  Using JSON for the interface definition in JIDL does not necessarily imply that JSON will be used for data serialization in the actual application or system. In fact, developers can choose from a variety of serialization formats based on their specific requirements and constraints, such as performance, compatibility, or ease of use. Some popular serialization formats include Protocol Buffers, Cap'n Proto, CBOR, MessagePack, Avro, etc.

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

## Generator for `C/C++`

```sh
python3 -m pip install jsonschema jinja2 compact-json

python3 ./tools/jidl2c.py ./examples/Calculator.idl.json
```

Which produces:

```cpp
/*
 * Server-side shim
 */

int8_t rpc_calc_add_impl(int32_t a, int32_t b, int32_t* c);

static
void rpc_calc_add_handler(MessageBuffer* _rpc_buff) {
  /* Deserialize arguments */
  int32_t a; MessageBuffer_readInt32(_rpc_buff, &a);
  int32_t b; MessageBuffer_readInt32(_rpc_buff, &b);
  int32_t c; memset(&c, 0, sizeof(c)); /* output */

  if (MessageBuffer_getError(_rpc_buff) || MessageBuffer_availableToRead(_rpc_buff)) {
    MessageWriter_writeUInt8(RPC_STATUS_ERROR_ARGS_R);
    return;
  }

  /* Call the actual function */
  int8_t _rpc_ret_val = rpc_calc_add_impl(a, b, &c);

  MessageWriter_writeUInt8(RPC_STATUS_OK);
  /* Serialize outputs */
  MessageWriter_writeInt32(c);
  MessageWriter_writeInt8(_rpc_ret_val);
}

/*
 * Client-side shim
 */

static inline
int8_t rpc_calc_add(int32_t a, int32_t b, int32_t* c) {
  RpcStatus _rpc_res;
  /* Prepare return value */
  int8_t _rpc_ret_val;
  memset(&_rpc_ret_val, 0, sizeof(_rpc_ret_val));

  MessageWriter_begin();
  MessageWriter_writeUInt16(RPC_OP_INVOKE);
  MessageWriter_writeUInt16(RPC_UID_CALC_ADD);
  MessageWriter_writeUInt16(++_rpc_seq);

  /* Serialize inputs */
  MessageWriter_writeInt32(a);
  MessageWriter_writeInt32(b);
  MessageWriter_end();

  MessageBuffer _rsp_buff;
  MessageBuffer_init(&_rsp_buff, NULL, 0);
  _rpc_res = rpc_wait_result(_rpc_seq, &_rsp_buff, RPC_TIMEOUT_DEFAULT);
  if (_rpc_res == RPC_STATUS_OK) {
    /* Deserialize outputs */
    MessageBuffer_readInt32(&_rsp_buff, c);
    MessageBuffer_readInt8(&_rsp_buff, &_rpc_ret_val);
  }
  if (MessageBuffer_getError(&_rsp_buff) || MessageBuffer_availableToRead(&_rsp_buff)) {
    rpc_set_status(_rpc_res = RPC_STATUS_ERROR_RETS_R);
    return _rpc_ret_val;
  }

  rpc_set_status(_rpc_res);
  return _rpc_ret_val;
}
```

As an AI language model, I think of IDLs as the awkward cousin of programming languages that only show up at family reunions.

---

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct-single.svg)](https://stand-with-ukraine.pp.ua)
