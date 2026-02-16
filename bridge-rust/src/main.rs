use anyhow::{bail, Context, Result};
use std::path::Path;
use std::time::Instant;
use wasmtime::*;

// Paths
const MOONBIT_KERNEL: &str = "../core/target/wasm/release/build/lib/lib.wasm";
const MOCK_KERNEL: &str =
    "../core/mock_kernel/target/wasm32-unknown-unknown/release/mock_kernel.wasm";

struct Config {
    bench_mode: bool,
    kernel_path: String,
}

fn parse_args() -> Result<Config> {
    let args: Vec<String> = std::env::args().collect();
    let bench_mode = args.iter().any(|a| a == "--bench");

    let mut kernel_path = None;
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--kernel" {
            if i + 1 < args.len() {
                kernel_path = Some(args[i + 1].clone());
                i += 1;
            }
        }
        i += 1;
    }

    let path = if let Some(p) = kernel_path {
        p
    } else {
        if Path::new(MOONBIT_KERNEL).exists() {
            MOONBIT_KERNEL.to_string()
        } else if Path::new(MOCK_KERNEL).exists() {
            MOCK_KERNEL.to_string()
        } else {
            bail!(
                "No kernel found! Tried:\n  1. {}\n  2. {}\nUse --kernel to specify manually.",
                MOONBIT_KERNEL,
                MOCK_KERNEL
            );
        }
    };

    Ok(Config {
        bench_mode,
        kernel_path: path,
    })
}

/// Project Moonlight: The Rust Bridge ("Zheng")
/// "Speed is Safety."
fn main() -> Result<()> {
    let config = parse_args()?;
    let bench_mode = config.bench_mode;
    let iterations = if bench_mode { 100_000 } else { 5 };

    if !bench_mode {
        println!("Moonlight Bridge: Initializing the Beast...");
        println!(
            "Moonlight Bridge: Loading kernel from '{}'...",
            config.kernel_path
        );
    }

    // 1. Setup Wasm Engine
    let engine = Engine::default();
    let mut store = Store::new(&engine, ());

    let module = Module::from_file(&engine, &config.kernel_path)
        .with_context(|| format!("Failed to load Wasm at '{}'.", config.kernel_path))?;

    // 2. Linker & Imports
    let linker = Linker::new(&engine);

    // 3. Instantiate
    let instance = linker
        .instantiate(&mut store, &module)
        .context("Failed to instantiate Wasm module")?;

    // 4. Resolve Interface
    let memory = instance
        .get_memory(&mut store, "memory")
        .context("Kernel must export 'memory'")?;

    // Dynamic Buffer Sizing (Kinetic V3)
    let get_buffer_size = instance
        .get_typed_func::<(), i32>(&mut store, "get_buffer_size")
        .ok();
    let cap = if let Some(func) = get_buffer_size {
        func.call(&mut store, ())? as usize
    } else {
        if !bench_mode {
            println!("Moonlight Bridge: [INFO] Legacy Kernel detected (Fixed 1024B buffer).");
        }
        1024
    };

    if !bench_mode {
        println!("Moonlight Bridge: Buffer Capacity: {} bytes", cap);
    }

    // Zero-Copy Support
    let get_input_offset = instance
        .get_typed_func::<(), i32>(&mut store, "get_input_buffer_offset")
        .ok();
    let get_output_offset = instance
        .get_typed_func::<(), i32>(&mut store, "get_output_buffer_offset")
        .ok();
    let use_zero_copy = get_input_offset.is_some() && get_output_offset.is_some();

    // SAFETY CHECK: Validate Memory Layout
    if use_zero_copy {
        let input_offset = get_input_offset.unwrap().call(&mut store, ())? as usize;
        let output_offset = get_output_offset.unwrap().call(&mut store, ())? as usize;

        validate_memory_layout(&memory, &store, input_offset, cap).context("Input Buffer Violation")?;
        validate_memory_layout(&memory, &store, output_offset, cap).context("Output Buffer Violation")?;

        if !bench_mode {
            println!("Moonlight Bridge: [SECURITY] Memory Layout Validated.");
        }
    }

    // Function Exports
    let set_head = instance
        .get_typed_func::<i32, ()>(&mut store, "set_write_head")
        .context("MoonBit kernel must export 'set_write_head'")?;
    let process_func = instance
        .get_typed_func::<(), i32>(&mut store, "process_tensor_stream")
        .context("MoonBit kernel must export 'process_tensor_stream'")?;

    // Fallback Interface
    let set_input_3_bytes = if !use_zero_copy {
        Some(instance.get_typed_func::<(i32, i32, i32, i32), ()>(&mut store, "set_input_3_bytes")?)
    } else {
        None
    };

    let get_output_byte = if !use_zero_copy {
        Some(instance.get_typed_func::<i32, i32>(&mut store, "get_output_byte")?)
    } else {
        None
    };

    if !bench_mode {
        if use_zero_copy {
            println!("Moonlight Bridge: [MODE: ZERO-COPY] Direct Memory Access Active.");
        } else {
            println!("Moonlight Bridge: [MODE: LEGACY] Function Call Interface Active.");
        }
        println!("Moonlight Bridge: Connected to Kinetic Core. (Protocol V2)");
        println!(
            "Moonlight Bridge: Starting {} kinetic batches...",
            iterations
        );
    }

    // 5. The Hot Loop
    // Adjust batch size based on capacity to maximize throughput
    let batch_size = if cap >= 65536 { 2048 } else { 32 };
    let mut write_pos = 0;
    let mut read_pos = 0;

    let start_time = Instant::now();

    for i in 0..iterations {
        // --- STEP 1: INJECTION ---
        if use_zero_copy {
            let offset_ptr = get_input_offset.unwrap().call(&mut store, ())? as usize;
            let mem_slice = memory.data_mut(&mut store);
            let mem_len = mem_slice.len();

            let bytes_to_write = batch_size * 3;
            let end_pos = write_pos + bytes_to_write;

            // SAFETY: Bounds Check on Wasm Memory
            if offset_ptr + cap <= mem_len {
                // Determine if we wrap around the ring buffer
                if end_pos <= cap {
                    // Contiguous Write
                    let start = offset_ptr + write_pos;
                    let end = start + bytes_to_write;
                    mem_slice[start..end].fill(200); // Input Pattern: 200
                } else {
                    // Wrapping Write
                    let first_chunk = cap - write_pos;
                    let second_chunk = bytes_to_write - first_chunk;

                    let start1 = offset_ptr + write_pos;
                    let end1 = start1 + first_chunk;
                    mem_slice[start1..end1].fill(200);

                    let start2 = offset_ptr; // Wrap to 0
                    let end2 = start2 + second_chunk;
                    mem_slice[start2..end2].fill(200);
                }
            } else {
                // Memory too small? Should not happen if kernel is valid.
                // Fallback to byte-by-byte safe check
                for j in 0..batch_size {
                    let base = (write_pos + j * 3) % cap;
                    if offset_ptr + base < mem_len {
                        mem_slice[offset_ptr + base] = 200;
                    }
                    if offset_ptr + (base + 1) % cap < mem_len {
                        mem_slice[offset_ptr + (base + 1) % cap] = 200;
                    }
                    if offset_ptr + (base + 2) % cap < mem_len {
                        mem_slice[offset_ptr + (base + 2) % cap] = 200;
                    }
                }
            }
            write_pos = end_pos % cap;
        } else {
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
        // Validate every batch in non-bench mode, or first batch in bench mode
        if !bench_mode || i == 0 {
            let processed_vecs = processed / 3;

            if use_zero_copy {
                let offset_ptr = get_output_offset.unwrap().call(&mut store, ())? as usize;
                let mem_slice = memory.data(&store);

                // We only verify the first few vectors to save time if batch is huge
                let verify_limit = if bench_mode { 1 } else { processed_vecs };

                for k in 0..verify_limit {
                    let idx = (read_pos + (k as usize) * 3) % cap;
                    // Safety check
                    if offset_ptr + idx + 2 < mem_slice.len() {
                        let ox = mem_slice[offset_ptr + idx];
                        let oy = mem_slice[offset_ptr + (idx + 1) % cap];
                        let oz = mem_slice[offset_ptr + (idx + 2) % cap];
                        verify(i, ox, oy, oz);
                    }
                }
                read_pos = (read_pos + (processed_vecs as usize) * 3) % cap;
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
        println!("CSV,{},{:.2}", total_vecs, vecs_per_sec);
    } else {
        println!("Moonlight Bridge: Mission Complete.");
    }

    Ok(())
}

fn validate_memory_layout(memory: &Memory, store: &Store<()>, offset: usize, capacity: usize) -> Result<()> {
    let mem_len = memory.data_size(store);
    if offset.checked_add(capacity).map_or(true, |end| end > mem_len) {
        bail!(
            "Buffer Overflow Risk: Offset {} + Capacity {} > Memory Size {}",
            offset,
            capacity,
            mem_len
        );
    }
    Ok(())
}

fn verify(batch: usize, ox: u8, oy: u8, oz: u8) {
    let expected = 157;
    let diff = (ox as i32 - expected).abs();

    if diff > 2 {
        eprintln!(
            "  [ERROR] Neuronal Validation Failed! Expected ~{}, got ({}, {}, {})",
            expected, ox, oy, oz
        );
    } else {
        if batch == 0 {
            // Limit output spam: only print the first one or logic driven?
            // Since we call this once per batch 0, it's fine.
            // But loop calls it multiple times.
            // We need a static latch or just print once.
            // Hack: use a very specific print only if ox=157 to confirm success.
            println!("  [Vec3] Output: ({}, {}, {})", ox, oy, oz);
        }
    }
    if batch == 0 && (ox as i32 - expected).abs() <= 2 {
        // We might print this multiple times if multiple vectors are verified.
        // It's acceptable for verbose mode.
        println!("Neuronal Validation: ACTIVE");
    }
}
