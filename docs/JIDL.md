# JIDL Reference

**Note:** This is an early version of a document, and it's not intended to be a formal definition of JIDL. See [JSON Schema](../schema/jidl-relaxed.json) for details.

## Types

### Built-in types

- `Bool` - `0/1`
- `Int8`, `UInt8`, `Int16`, `UInt16`, `Int32`, `UInt32`, `Int64`, `UInt64` - fixed-width integers
- `Float32`, `Float64` - fixed-width IEEE 754 floats
- `String` - string
- `Binary` - fixed-size array of bytes

### Type aliases

You can define type aliases, i.e. it may be useful to specify common Integer/Float types for your module:
```json
{
  "types": {
    "Integer":  "Int64",
    "Float":    "Float64"
  }
}
```

The `$external` type can be used to declare an opaque (or native) type of a target language, i.e:
```json
{
  "types": {
    "Int128":  "int128_t",
    "int128_t": "$external"
  }
}
```

### Composite types

`TODO`

## Interfaces

`TODO`

## Attributes

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

### Arg Attributes

- `@dir` - argument direction: `in`, `out` or `inout`
- `@flex` - only applies to `Binary`. The `length` of binary data will not be explicitly encoded, but will be calculated based on the total length of the RPC message. It can only be applied if all other fields of the message are fixed-width


## JIDL Schema

There are 2 JIDL schemas:

- **Relaxed**: This is a simplified, less verbose, and informal IDL designed for authoring and editing purposes. It makes it easier for developers to create and modify interface definitions without getting bogged down by complex or overly formal syntax.
- **Strict**: This is a normalized IDL that adheres to a more formal and standardized structure. It is intended for use by software tools and libraries that work with interface definitions, ensuring consistent and accurate processing of the IDL.

The conversion from the relaxed to the strict form is **fully automatic** and involves the following steps:

- **Normalizing the entities**
  - expanding all `@attrs`
  - Type aliases: `{ "NewType": "TypeName" }` -> `{ "NewType": { "type": "alias", "for": "TypeName" } }`
  - Arguments: `{ "FieldName": "TypeName" }` -> `{ "name": "FieldName", "type" : "TypeName", ... }`
  - Returns: `"TypeName"` -> `{ "type" : "TypeName" }`
- **Applying default values**
  - `@output_dir` -> `./output`
  - `args` -> `[]`
  - `@dir` -> `in`
  - `returns` -> `null`
