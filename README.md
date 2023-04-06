# JIDL

This is **jiddle** - a `JSON`-based, simple and extensible `Interface Definition Language`

- [Documentation](./docs/JIDL.md)
- [JSON Schema](./jidl.schema.json)

## Example

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

We can generate `C/C++` shims based on this IDL:

```
python3 jidl2c.py ./examples/Calculator.jidl
```

Which produces:

```cpp
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

//...

static inline
int8_t rpc_calc_add(int32_t a, int32_t b, int32_t *c) {
  //...

  // Serialize inputs
  _rpc_buff.write_int32(a);
  _rpc_buff.write_int32(b);
  _rpc_buff.write_int32(c);

  // RPC call
  rpc_send_msg(&_rpc_buff);

  int8_t _rpc_ret_val;
  memset(_rpc_ret_val, 0, sizeof(_rpc_ret_val));

  MessageBuffer _rsp_buff(NULL, 0);
  RpcStatus _rpc_status = rpc_wait_result(_rpc_seq, &_rsp_buff);
  if (_rpc_status == RPC_STATUS_OK) {
    // Deserialize outputs
    _rsp_buff.read_int32(&c);
    _rsp_buff.read_int8(&_rpc_ret_val);
    return _rpc_ret_val;
  }

  return _rpc_ret_val;
}

```
