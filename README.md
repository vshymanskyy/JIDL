# JIDL

A `JSON`-based, simple and extensible `Interface Definition Language`

## Types

- `Bool` - `0/1`
- `Int8`, `UInt8`, `Int16`, `UInt16`, ... - fixed-width integers
- `Float32`, `Float64` - fixed-width IEEE 754 floats
- `String` - a NULL-terminated string
- `Binary` - a fixed-size array of bytes

### Generic Attributes

- `@doc` - documentation (included as a comment in the output)
- `@id` - RPC `UID` associated with the entity
- `@attrs` - an array of `boolean` attribures to be set to `True` (to simplify the IDL notation)

### Function Attributes

- `@oneway` - RPC server will skip sending any response
- `@no_impl` - RPC server skips calling the actual function implementation
- `@timeout` - client-side timeout of an RPC call

`C/C++` specific attributes:

- `@c:ret_status` - client-side RPC shim will return the status of the RPC call (applicable to functions without return value)
- `@c:error_val` - client-side RPC shim will return this value in case of RPC failure (applicable to functions that return a value)

### Args Attributes

- `@dir` - argument direction: `in`, `out` or `inout`
- `@flex` - only applies to `Binary`. The `length` of binary data will not be explicitly encoded, but will be calculated based on the total length of the RPC message. It can only be applied if all other fields of the message are fixed-width
