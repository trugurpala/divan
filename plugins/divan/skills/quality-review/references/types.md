# Types and Contracts

- Avoid primitive obsession when a domain identifier, status, money value, or mode has distinct semantics.
- Prefer unions or discriminated states over unrelated boolean flags.
- Make illegal states difficult to represent.
- Keep DTO, database, and domain representations distinct when their contracts differ.
- Do not mix exceptions, nulls, booleans, and error objects randomly for equivalent operations.
- Validate untrusted input at system boundaries; do not confuse compile-time types with runtime validation.
