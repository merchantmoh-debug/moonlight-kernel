use anyhow::{bail, Context, Result};
use log::{debug, error, info, warn};
use std::env;
use std::path::Path;
use std::time::Instant;
use wasmtime::*;

// --- CONFIGURATION ---
const MOONBIT_KERNEL: &str = "../core/target/wasm/release/build/lib/lib.wasm";
const MOCK_KERNEL: &str =
    "../core/mock_kernel/target/wasm32-unknown-unknown/release/mock_kernel.wasm";

// --- THE KINETIC BRIDGE ---

struct MoonlightBridge {
    store: Store<()>,
    memory: Memory,
    cap: usize,
    input_offset: usize,
    output_offset: usize,

    // Exports
    set_write_head: TypedFunc<i32, ()>,
    process_tensor_stream: TypedFunc<(), i32>,

    // New Exports (V2)
    vector_add_batch: Option<TypedFunc<i32, i32>>,
    vector_dot_batch: Option<TypedFunc<i32, i32>>,
    check_integrity: Option<TypedFunc<(), i32>>,

    // Legacy / Fallback
    set_input_3_bytes: Option<TypedFunc<(i32, i32, i32, i32), ()>>,
    get_output_byte: Option<TypedFunc<i32, i32>>,
}

impl MoonlightBridge {
    fn ignite(kernel_path: &str, strict_mode: bool) -> Result<Self> {
        info!("Igniting Bridge with Kernel: {} (Strict: {})", kernel_path, strict_mode);

        let mut config = Config::new();
        config.wasm_multi_memory(true);
        let engine = Engine::new(&config)?;
        let mut store = Store::new(&engine, ());

        let module = Module::from_file(&engine, kernel_path)
            .with_context(|| format!("Failed to load Wasm at '{}'", kernel_path))?;

        let linker = Linker::new(&engine);
        let instance = linker.instantiate(&mut store, &module)
            .context("Failed to instantiate Wasm module")?;

        let memory = instance
            .get_memory(&mut store, "memory")
            .context("Kernel must export 'memory'")?;

        // 1. Resolve Capacity
        let get_buffer_size = instance
            .get_typed_func::<(), i32>(&mut store, "get_buffer_size")
            .ok();

        let cap = if let Some(func) = get_buffer_size {
            func.call(&mut store, ())? as usize
        } else {
            warn!("Legacy Kernel detected. Defaulting to 1024 bytes.");
            1024
        };

        debug!("Buffer Capacity: {} bytes", cap);

        // 2. Resolve Offsets (Zero-Copy)
        let get_input_offset = instance.get_typed_func::<(), i32>(&mut store, "get_input_buffer_offset").ok();
        let get_output_offset = instance.get_typed_func::<(), i32>(&mut store, "get_output_buffer_offset").ok();

        let (input_offset, output_offset) = if let (Some(gio), Some(goo)) = (get_input_offset, get_output_offset) {
             let i = gio.call(&mut store, ())? as usize;
             let o = goo.call(&mut store, ())? as usize;
             info!("[MODE: ZERO-COPY] Direct Memory Access Active (In: {}, Out: {})", i, o);
             (i, o)
        } else {
             info!("[MODE: LEGACY] Function Call Interface Active");
             (0, 0)
        };

        // 3. Resolve Critical Functions
        let set_write_head = instance
            .get_typed_func::<i32, ()>(&mut store, "set_write_head")
            .context("Missing export: set_write_head")?;

        let process_tensor_stream = instance
            .get_typed_func::<(), i32>(&mut store, "process_tensor_stream")
            .context("Missing export: process_tensor_stream")?;

        let vector_add_batch = instance.get_typed_func::<i32, i32>(&mut store, "vector_add_batch").ok();
        let vector_dot_batch = instance.get_typed_func::<i32, i32>(&mut store, "vector_dot_batch").ok();
        let check_integrity = instance.get_typed_func::<(), i32>(&mut store, "check_integrity").ok();
        let set_input_3_bytes = instance.get_typed_func::<(i32, i32, i32, i32), ()>(&mut store, "set_input_3_bytes").ok();
        let get_output_byte = instance.get_typed_func::<i32, i32>(&mut store, "get_output_byte").ok();

        // Strict Mode Enforcement
        if strict_mode {
            if vector_add_batch.is_none() { bail!("STRICT MODE: 'vector_add_batch' missing!"); }
            if vector_dot_batch.is_none() { bail!("STRICT MODE: 'vector_dot_batch' missing!"); }
            if check_integrity.is_none() { bail!("STRICT MODE: 'check_integrity' missing!"); }
        }

        // Kinetic Optimization Check
        info!("--- KINETIC OPTIMIZATIONS ---");
        info!("> Zero-Copy Mode:    {}", if input_offset > 0 { "ACTIVE" } else { "INACTIVE" });
        info!("> Batch Vector Add:  {}", if vector_add_batch.is_some() { "ACTIVE" } else { "INACTIVE" });
        info!("> Batch Vector Dot:  {}", if vector_dot_batch.is_some() { "ACTIVE" } else { "INACTIVE" });
        info!("> Integrity Check:   {}", if check_integrity.is_some() { "ACTIVE" } else { "INACTIVE" });
        info!("-----------------------------");

        // 4. Validate Memory Layout
        let mem_size = memory.data_size(&store);
        if input_offset + cap > mem_size {
            bail!("Memory Violation: Input Buffer exceeds Wasm memory bounds.");
        }
        if output_offset + cap > mem_size {
             bail!("Memory Violation: Output Buffer exceeds Wasm memory bounds.");
        }

        // Check for Overlap
        // We assume contiguous buffers of size `cap`
        let input_end = input_offset + cap;
        let output_end = output_offset + cap;

        let overlap = (input_offset < output_end) && (output_offset < input_end);
        if overlap {
             // In some cases (In-Place ops), overlap is desired.
             // But for standard stream processing, it's a risk.
             // We'll warn for now, or bail if strict.
             // Given we have separate buffers in Mock, valid overlap implies error.
             if input_offset != output_offset { // Exact match might be intentional "in-place"
                 warn!("CRITICAL: Memory Overlap Detected between Input and Output Buffers! ({} vs {})", input_offset, output_offset);
             }
        }

        Ok(Self {
            store,
            memory,
            cap,
            input_offset,
            output_offset,
            set_write_head,
            process_tensor_stream,
            vector_add_batch,
            vector_dot_batch,
            check_integrity,
            set_input_3_bytes,
            get_output_byte,
        })
    }

    fn write_batch(&mut self, write_pos: usize, count: usize) -> Result<usize> {
        let bytes_needed = count * 3;
        let end_pos = write_pos + bytes_needed;

        // KINETIC PATH: Direct Memory Access
        let mem_slice = self.memory.data_mut(&mut self.store);

        if end_pos <= self.cap {
            // Contiguous
            let start = self.input_offset + write_pos;
            let end = start + bytes_needed;
            if end <= mem_slice.len() {
                mem_slice[start..end].fill(200); // Signal: 200
            }
        } else {
            // Wrap
            let first_chunk = self.cap - write_pos;
            let second_chunk = bytes_needed - first_chunk;

            let start1 = self.input_offset + write_pos;
            let end1 = start1 + first_chunk;

            let start2 = self.input_offset;
            let end2 = start2 + second_chunk;

            if end1 <= mem_slice.len() && end2 <= mem_slice.len() {
                 mem_slice[start1..end1].fill(200);
                 mem_slice[start2..end2].fill(200);
            }
        }

        Ok(end_pos % self.cap)
    }

    fn run_kinetic_loop(&mut self, iterations: usize, batch_size: usize, verify_active: bool) -> Result<()> {
        // Integrity Check (Start)
        if let Some(check) = &self.check_integrity {
             let status = check.call(&mut self.store, ())?;
             if status == 0 {
                 bail!("KERNEL PANIC: Integrity Check Failed on Startup! (Canary Corrupted)");
             }
        }

        let mut write_pos = 0;
        let mut read_pos = 0;

        let start = Instant::now();

        for i in 0..iterations {
            // 1. Inject Signal
            write_pos = self.write_batch(write_pos, batch_size)?;

            // 2. Sync Head
            self.set_write_head.call(&mut self.store, write_pos as i32)?;

            // 3. Process
            let processed_bytes = self.process_tensor_stream.call(&mut self.store, ())?;
            let processed_vecs = processed_bytes / 3;

            // 4. Verify (Neuronal Validation) - BEFORE modification
            if verify_active && i == 0 {
                self.verify_output(read_pos, processed_vecs as usize)?;
            }

            // 5. Vector Ops (Optional)
            if let Some(func) = &self.vector_add_batch {
                if i % 10 == 0 && processed_vecs > 0 {
                    func.call(&mut self.store, processed_vecs)?;
                    if i == 0 {
                         debug!("Vector Batch Addition: ACTIVE");
                    }
                }
            }

            if let Some(func) = &self.vector_dot_batch {
                if i % 20 == 0 && processed_vecs > 0 {
                    func.call(&mut self.store, processed_vecs)?;
                    if i == 0 {
                         debug!("Vector Batch Dot Product: ACTIVE");
                    }
                }
            }

            read_pos = (read_pos + processed_bytes as usize) % self.cap;
        }

        let duration = start.elapsed();
        if iterations > 100 {
            let total_vecs = iterations as u128 * batch_size as u128;
            let vecs_per_sec = total_vecs as f64 / duration.as_secs_f64();
            let bytes_per_sec = (total_vecs * 3) as f64 / duration.as_secs_f64();
            let mb_per_sec = bytes_per_sec / 1_048_576.0;

            println!("BENCHMARK: {:.2} vectors/sec | {:.2} MB/s", vecs_per_sec, mb_per_sec);
            println!("BENCHMARK_DATA: vectors_sec={:.2}, mb_sec={:.2}", vecs_per_sec, mb_per_sec);
        } else {
            info!("Kinetic Loop Complete. Time: {:?}", duration);
        }

        // Integrity Check (End)
        if let Some(check) = &self.check_integrity {
             let status = check.call(&mut self.store, ())?;
             if status == 0 {
                 bail!("KERNEL PANIC: Integrity Check Failed after Kinetic Loop! (Canary Corrupted)");
             } else if verify_active {
                 info!("Integrity Check: PASS");
             }
        }

        Ok(())
    }

    fn verify_output(&mut self, start_read_pos: usize, count: usize) -> Result<()> {
        let mem_slice = self.memory.data(&self.store);
        let limit = if count > 10 { 10 } else { count }; // Verify first 10

        for k in 0..limit {
            let idx = (start_read_pos + k * 3) % self.cap;
            let offset = self.output_offset + idx;

            if offset + 2 < mem_slice.len() {
                let ox = mem_slice[offset];
                let oy = mem_slice[offset + 1];
                let oz = mem_slice[offset + 2];

                // Logic: 200 input -> Normalize -> 157 output
                // 200 / sqrt(3*200^2) = 0.577
                // 0.577 * 100 + 100 = 157.7 -> 157
                let expected = 157;
                let diff = (ox as i32 - expected).abs();

                if diff <= 2 {
                    if k == 0 {
                         println!("Neuronal Validation: ACTIVE");
                         debug!("Verified Vector: ({}, {}, {})", ox, oy, oz);
                    }
                } else {
                    error!("Validation FAILED: Expected ~{}, Got ({}, {}, {})", expected, ox, oy, oz);
                }
            }
        }
        Ok(())
    }
}

fn main() -> Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let args: Vec<String> = env::args().collect();
    let bench_mode = args.iter().any(|a| a == "--bench");
    let strict_mode = args.iter().any(|a| a == "--strict");

    let mut kernel_path = None;
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--kernel" && i + 1 < args.len() {
            kernel_path = Some(args[i + 1].clone());
        }
        i += 1;
    }

    let path = kernel_path.unwrap_or_else(|| {
        if Path::new(MOONBIT_KERNEL).exists() {
            MOONBIT_KERNEL.to_string()
        } else {
            MOCK_KERNEL.to_string()
        }
    });

    let mut bridge = MoonlightBridge::ignite(&path, strict_mode)?;

    let iterations = if bench_mode { 100_000 } else { 5 };
    let batch_size = if bridge.cap >= 65536 { 1024 } else { 32 };

    bridge.run_kinetic_loop(iterations, batch_size, !bench_mode)?;

    Ok(())
}
