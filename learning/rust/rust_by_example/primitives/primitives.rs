// --- Scalar Types ---
// signed integers:     i8, i16, i32, i64, i128 and isize (pointer size)
// unsigned integers:   u8, u16, u32, u64, u128 and usize (pointer size)
// floating point:      f32, f64 (double)
// char:                unicode scalar values (4 bytes each)
// bool:                true or false
// unit type ():       empty tuple

// --- Compound Types ---
// arrays: [1, 2, 3] - all of same type
// tuples: (1, true) - can have different type in each spot

fn main() {
    // type annotated
    let logical: bool = true;
    let a_float: f64 = 1.0; // regular annotation
    let an_integer = 5i32; // suffix annotation

    // default annotation (or inference)
    // default float = f64, int = i32
    let default_float = 3.0;  // `f64`
    let default_integer = 7;  // `i32`

    // can be inferred from context
    let mut inferred_type = 12;
    // compiler sees this and works out that inferred_type is i64
    inferred_type = 4294967296i64;

    // mutable variable => value can be changed
    let mut mutable = 12;  // `i32`
    mutable = 21;

    // Error! type of variable cannot be changed however.
    mutable = true;

    // Variables can be overwritten by shadowing
    // variables within a scope can be shadowed using the same name.
    // I susect this kills the lifetime of the previous mutable variable and creates a new lifetime
    // for this one:
    let mutable = true;
}
