# humanize

Deterministic, English-specific formatting for Nift integers. The package has
no dependencies or resources and exports only the `humanize` facade.

```nift
@import("humanize")

humanize.integer(1234567)             // "1,234,567"
humanize.bytes(1536)                   // "1.5 KiB"
humanize.plural(2, "item")             // "2 items"
humanize.plural(2, "person", "people") // "2 people"
humanize.ordinal(23)                   // "23rd"
```

## Contract

- Every numeric argument must have Nift type `int`; strings, floats, booleans,
  null and collections are rejected rather than coerced.
- `integer(value)` inserts ASCII commas every three digits. A negative sign is
  preserved, including for the minimum signed 64-bit integer.
- `bytes(value)` uses IEC powers of 1024 and the symbols `B`, `KiB`, `MiB`,
  `GiB`, `TiB`, `PiB` and `EiB`. Bytes below 1024 are whole `B` values. Larger
  values have at most one fractional digit; exact `.0` is omitted.
- Byte fractions are rounded to the nearest tenth. Exact half-tenth ties round
  away from zero because rounding is applied to the magnitude before restoring
  a negative sign. Decimal-string long division keeps results deterministic at
  all signed 64-bit boundaries and does not use floating-point byte arithmetic.
- `plural(count, singular, optional_plural)` emits the comma-grouped count and
  an English word. Only exactly `1` is singular, so `0`, `-1`, and every other
  count use the plural. Without an explicit plural, `s` is appended.
- `ordinal(value)` uses English `st`, `nd`, `rd`, and `th` suffix rules based on
  the magnitude, including the `11` through `13` exceptions. Its number is
  comma-grouped and a negative sign does not affect the suffix.

Facade helpers are private. Named methods must be invoked through `humanize`;
method extraction is not part of the API.

## Test

```sh
python3 tests/test_humanize.py /path/to/nift /path/to/humanize
```

The suite covers direct package import, local `nift add` import from an external
consumer, facade privacy, malformed values, signed boundaries, unit boundaries,
rounding and repeated deterministic execution. It removes its temporary work
directories on success and failure.

## License

MIT
