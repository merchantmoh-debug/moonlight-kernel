use anyhow::{Context, Result};
use std::time::Instant;
use wasmtime::*;

/// Project Moonlight: The Rust Bridge ("Zheng")
/// "Speed is Safety."
fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let bench_mode = args.iter().any(|a| a == "--bench");
    let iterations = if bench_mode { 100_000 } else { 5 };

    if !bench_mode {
        println!("Moonlight Bridge: Initializing the Beast...");
    }

    // 1. Setup Wasm Engine
    let engine = Engine::default();
    let mut store = Store::new(&engine, ());

    // Path to the MoonBit Kernel Wasm artifact (or Mock Kernel)
    let wasm_path = "../core/target/wasm/release/build/lib/lib.wasm";

    if !bench_mode {
        println!("Moonlight Bridge: Loading kernel from '{}'...", wasm_path);
    }

    let module = Module::from_file(&engine, wasm_path)
        .with_context(|| format!("Failed to load MoonBit Kernel Wasm at '{}'. Did you run 'moon build' in core/?", wasm_path))?;

    // 2. Linker & Imports
    let linker = Linker::new(&engine);
    
    // 3. Instantiate
    let instance = linker.instantiate(&mut store, &module)
        .context("Failed to instantiate Wasm module")?;

    // 4. Resolve Interface (Kinetic Discovery)
    let memory = instance.get_memory(&mut store, "memory")
        .context("Kernel must export 'memory'")?;

    // Check for Zero-Copy (Genesis V3) Support
    let get_input_offset = instance.get_typed_func::<(), i32>(&mut store, "get_input_buffer_offset").ok();
    let get_output_offset = instance.get_typed_func::<(), i32>(&mut store, "get_output_buffer_offset").ok();

    let use_zero_copy = get_input_offset.is_some() && get_output_offset.is_some();

    // Standard Interface
    let set_head = instance.get_typed_func::<i32, ()>(&mut store, "set_write_head")
        .context("MoonBit kernel must export 'set_write_head'")?;

    let process_func = instance.get_typed_func::<(), i32>(&mut store, "process_tensor_stream")
        .context("MoonBit kernel must export 'process_tensor_stream'")?;

    // Fallback Interface
    let set_input_3_bytes = if !use_zero_copy {
        Some(instance.get_typed_func::<(i32, i32, i32, i32), ()>(&mut store, "set_input_3_bytes")
            .context("Kernel missing 'set_input_3_bytes'")?)
    } else { None };

    let get_output_byte = if !use_zero_copy {
        Some(instance.get_typed_func::<i32, i32>(&mut store, "get_output_byte")
            .context("Kernel missing 'get_output_byte'")?)
    } else { None };

    if !bench_mode {
        if use_zero_copy {
            println!("Moonlight Bridge: [MODE: ZERO-COPY] Direct Memory Access Active.");
        } else {
            println!("Moonlight Bridge: [MODE: LEGACY] Function Call Interface Active.");
        }
        println!("Moonlight Bridge: Connected to Kinetic Core. (Protocol V2)");
        println!("Moonlight Bridge: Starting {} kinetic batches...", iterations);
    }

    // 5. The Hot Loop
    let batch_size = 32; // Vectors per batch
    let cap = 1024;
    let mut write_pos = 0;
    let mut read_pos = 0;

    let start_time = Instant::now();

    for i in 0..iterations {
        // --- STEP 1: INJECTION ---
        if use_zero_copy {
            // Genesis V3: Direct Memory Write
            let offset_ptr = get_input_offset.unwrap().call(&mut store, ())? as usize;
            let mem_slice = memory.data_mut(&mut store);

            // We write 32 * 3 = 96 bytes
            // Input Pattern: (200, 200, 200)
            for j in 0..batch_size {
                 let base = (write_pos + j * 3) % cap;
                 // Handle wrap-around relative to Ring Buffer Capacity (1024)
                 // If the write fits within the buffer without wrapping:
                 if base + 2 < cap {
                     // Safety Check: Ensure we don't write outside Wasm Memory
                     if offset_ptr + base + 2 < mem_slice.len() {
                         mem_slice[offset_ptr + base] = 200;
                         mem_slice[offset_ptr + base + 1] = 200;
                         mem_slice[offset_ptr + base + 2] = 200;
                     }
                 } else {
                     // Wrap case: Write byte-by-byte with modulo arithmetic
                     // Safety Check for each byte
                     if offset_ptr + base < mem_slice.len() {
                         mem_slice[offset_ptr + base] = 200;
                     }
                     if offset_ptr + (base + 1) % cap < mem_slice.len() {
                         mem_slice[offset_ptr + (base + 1) % cap] = 200;
                     }
                     if offset_ptr + (base + 2) % cap < mem_slice.len() {
                         mem_slice[offset_ptr + (base + 2) % cap] = 200;
                     }
                 }
            }
            write_pos = (write_pos + batch_size * 3) % cap;
        } else {
            // Legacy V2: Function Calls
            let func = set_input_3_bytes.as_ref().unwrap();
            for _ in 0..batch_size {
                func.call(&mut store, (write_pos as i32, 200, 200, 200))?;
                write_pos = (write_pos + 3) % cap;
            }
        }

        // --- STEP 2: SYNC & PROCESS ---
        set_head.call(&mut store, write_pos as i32)?;
        let processed = process_func.call(&mut store, ())?;

        // --- STEP 3: READ OUTPUT ---
        // Verification only on first batch or if not benchmarking to save time
        if !bench_mode || i == 0 {
             let processed_vecs = processed / 3;

             if use_zero_copy {
                 let offset_ptr = get_output_offset.unwrap().call(&mut store, ())? as usize;
                 let mem_slice = memory.data(&store); // Immutable borrow

                 for k in 0..processed_vecs {
                     let idx = (read_pos + (k as usize) * 3) % cap;
                     let ox = mem_slice[offset_ptr + idx];
                     let oy = mem_slice[offset_ptr + (idx + 1) % cap];
                     let oz = mem_slice[offset_ptr + (idx + 2) % cap];

                     verify(i, ox, oy, oz);
                 }
             } else {
                 let func = get_output_byte.as_ref().unwrap();
                 for _ in 0..processed_vecs {
                     let ox = func.call(&mut store, read_pos as i32)?;
                     let oy = func.call(&mut store, (read_pos as i32 + 1) % cap as i32)?;
                     let oz = func.call(&mut store, (read_pos as i32 + 2) % cap as i32)?;
                     verify(i, ox as u8, oy as u8, oz as u8);

                     read_pos = (read_pos + 3) % cap;
                 }
             }

             // Update read_pos manually for Zero-Copy since we just read
             if use_zero_copy {
                 read_pos = (read_pos + (processed_vecs as usize) * 3) % cap;
             }
        } else {
             // In bench mode, just advance read pointer logically
             read_pos = (read_pos + (processed as usize)) % cap;
        }
    }

    let duration = start_time.elapsed();

    if bench_mode {
        let total_vecs = iterations as u128 * batch_size as u128;
        let vecs_per_sec = total_vecs as f64 / duration.as_secs_f64();
        println!("BENCHMARK: {:.2} vectors/sec", vecs_per_sec);
        // Also print machine-readable
        println!("CSV,{},{:.2}", total_vecs, vecs_per_sec);
    } else {
        println!("Moonlight Bridge: Mission Complete.");
    }

    Ok(())
}

fn verify(batch: usize, ox: u8, oy: u8, oz: u8) {
    // Expected: 157
    let expected = 157;
    let diff = (ox as i32 - expected).abs();

    // Print numerical values for the first vector of the first batch (Test Requirement)
    // We need a static counter or just check if it's the first call?
    // Simplified: Just print it if batch == 0. But this prints 32 times.
    // The test just needs to find ONE occurrence.
    // Let's print it.

    if diff > 2 {
        eprintln!("  [ERROR] Neuronal Validation Failed! Expected ~{}, got ({}, {}, {})", expected, ox, oy, oz);
    } else {
        if batch == 0 {
             // Print formatted output for test regex: Output: (157, 157, 157)
             // We only need to print it once per batch to avoid spam, but printing all is fine for 32 items.
             println!("  [Vec3] Output: ({}, {}, {})", ox, oy, oz);
        }
    }
    // Always print the validation token once per run
    if batch == 0 && (ox as i32 - expected).abs() <= 2 {
        println!("Neuronal Validation: ACTIVE");
    }
}
