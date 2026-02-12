use anyhow::{Context, Result};
use wasmtime::*;

/// Project Moonlight: The Rust Bridge ("Zheng")
/// "Speed is Safety."
fn main() -> Result<()> {
    println!("Moonlight Bridge: Initializing the Beast...");

    // 1. Setup Wasm Engine
    let engine = Engine::default();
    let mut store = Store::new(&engine, ());

    // Path to the MoonBit Kernel Wasm artifact
    let wasm_path = "../core/target/wasm/release/build/lib/lib.wasm";

    println!("Moonlight Bridge: Loading kernel from '{}'...", wasm_path);

    let module = Module::from_file(&engine, wasm_path)
        .with_context(|| format!("Failed to load MoonBit Kernel Wasm at '{}'. Did you run 'moon build' in core/?", wasm_path))?;

    // 2. Linker & Imports
    let linker = Linker::new(&engine);
    
    // 3. Instantiate
    let instance = linker.instantiate(&mut store, &module)
        .context("Failed to instantiate Wasm module")?;

    // 4. Zero-Copy Handshake (Safe Mode)
    // We use safe accessor functions to prevent memory corruption.

    // Function to set a single byte in the buffer
    let set_byte = instance
        .get_typed_func::<(i32, i32), ()>(&mut store, "set_input_byte")
        .context("MoonBit kernel must export 'set_input_byte'")?;

    // Function to update the write head
    let set_head = instance
        .get_typed_func::<i32, ()>(&mut store, "set_write_head")
        .context("MoonBit kernel must export 'set_write_head'")?;

    // Get the processing function
    let process_func = instance
        .get_typed_func::<(), i32>(&mut store, "process_tensor_stream")
        .context("MoonBit kernel must export 'process_tensor_stream'")?;

    println!("Moonlight Bridge: Connected to Kinetic Core.");

    // 5. The Hot Loop (Simulated Neuro-Symbolic Stream)
    
    let iterations = 5;
    println!("Moonlight Bridge: Starting {} kinetic cycles...", iterations);

    let mut write_pos = 0;
    let cap = 1024;
    let batch_size = 32;

    for i in 0..iterations {
        // Safe Memory Access
        // We write 3 bytes (Vec3) into the buffer using the accessor.

        let val_x = 200; // Trigger threshold
        let val_y = 200;
        let val_z = 200;

        // Write X
        set_byte.call(&mut store, (write_pos, val_x))?;
        write_pos = (write_pos + 1) % cap;

        // Write Y
        set_byte.call(&mut store, (write_pos, val_y))?;
        write_pos = (write_pos + 1) % cap;

        // Write Z
        set_byte.call(&mut store, (write_pos, val_z))?;
        write_pos = (write_pos + 1) % cap;

        // Optimization: Sync Head and Process in Batches
        // Reduces boundary crossings from O(N) to O(N/batch_size)
        if (i + 1) % batch_size == 0 || i == iterations - 1 {
            // Sync Write Head
            set_head.call(&mut store, write_pos)?;

            // Trigger Kinetic Core
            let processed = process_func.call(&mut store, ())?;

            // Distribute processed bytes to cycles in this batch
            let num_cycles_in_batch = if (i + 1) % batch_size == 0 { batch_size } else { (i + 1) % batch_size };
            let mut remaining = processed;
            for j in 0..num_cycles_in_batch {
                let cycle_idx = i + 1 - num_cycles_in_batch + j;
                let take = if remaining >= 3 { 3 } else { remaining };
                println!("[Cycle {}] Kernel Processed: {} bytes. (Neuronal Validation: ACTIVE)", cycle_idx, take);
                remaining -= take;
            }
        }
    }

    println!("Moonlight Bridge: Mission Complete.");
    Ok(())
}
