// Mock Kernel (Rust) mimicking MoonBit Kernel Interface
// "The Mechanic's Ear" - Testing Rig

// Using a 64KB buffer for larger tensor operations
const BUFFER_SIZE: usize = 65536;

#[no_mangle]
pub static mut BUFFER: [u8; BUFFER_SIZE] = [0; BUFFER_SIZE];

#[no_mangle]
pub static mut OUTPUT_BUFFER: [u8; BUFFER_SIZE] = [0; BUFFER_SIZE];

#[no_mangle]
pub static mut CANARY: u8 = 0xAA;

static mut READ_HEAD: usize = 0;
static mut WRITE_HEAD: usize = 0;

#[no_mangle]
pub extern "C" fn get_buffer_size() -> i32 {
    BUFFER_SIZE as i32
}

#[no_mangle]
pub extern "C" fn set_input_byte(index: i32, val: i32) {
    unsafe {
        if index >= 0 {
            let idx = (index as usize) & (BUFFER_SIZE - 1);
            BUFFER[idx] = val as u8;
        }
    }
}

#[no_mangle]
pub extern "C" fn set_input_3_bytes(index: i32, x: i32, y: i32, z: i32) {
    unsafe {
        if index >= 0 {
            let idx = (index as usize) & (BUFFER_SIZE - 1);
            BUFFER[idx] = x as u8;
            BUFFER[(idx + 1) & (BUFFER_SIZE - 1)] = y as u8;
            BUFFER[(idx + 2) & (BUFFER_SIZE - 1)] = z as u8;
        }
    }
}

#[no_mangle]
pub extern "C" fn set_write_head(pos: i32) {
    unsafe {
        if pos >= 0 {
            WRITE_HEAD = (pos as usize) & (BUFFER_SIZE - 1);
        }
    }
}

#[no_mangle]
pub extern "C" fn get_read_head() -> i32 {
    unsafe { READ_HEAD as i32 }
}

#[no_mangle]
pub extern "C" fn get_output_byte(index: i32) -> i32 {
    unsafe {
        if index >= 0 {
            let idx = (index as usize) & (BUFFER_SIZE - 1);
            OUTPUT_BUFFER[idx] as i32
        } else {
            0
        }
    }
}

// --- Zero-Copy Interface (Genesis V3) ---
// Returns the offset of the input buffer in Wasm Linear Memory.
#[no_mangle]
pub extern "C" fn get_input_buffer_offset() -> i32 {
    std::ptr::addr_of!(BUFFER) as i32
}

// Returns the offset of the output buffer in Wasm Linear Memory.
#[no_mangle]
pub extern "C" fn get_output_buffer_offset() -> i32 {
    std::ptr::addr_of!(OUTPUT_BUFFER) as i32
}

fn diff(read: usize, write: usize, cap: usize) -> usize {
    if write >= read {
        write - read
    } else {
        (cap - read) + write
    }
}

#[inline(always)]
unsafe fn process_single_vector(idx: usize) {
    let x = BUFFER[idx] as f64;
    let y = BUFFER[(idx + 1) & (BUFFER_SIZE - 1)] as f64;
    let z = BUFFER[(idx + 2) & (BUFFER_SIZE - 1)] as f64;

    // Normalize Logic
    let len = (x * x + y * y + z * z).sqrt();
    let (nx, ny, nz) = if len == 0.0 {
        (x, y, z)
    } else {
        (x / len, y / len, z / len)
    };

    // Scale to visualize direction: (nx * 100 + 100)
    // Range [-1, 1] -> [0, 200] approximately.
    // Clamped to u8 range implicitly by cast.
    OUTPUT_BUFFER[idx] = (nx * 100.0 + 100.0) as u8;
    OUTPUT_BUFFER[(idx + 1) & (BUFFER_SIZE - 1)] = (ny * 100.0 + 100.0) as u8;
    OUTPUT_BUFFER[(idx + 2) & (BUFFER_SIZE - 1)] = (nz * 100.0 + 100.0) as u8;
}

#[no_mangle]
pub extern "C" fn process_tensor_stream() -> i32 {
    unsafe {
        let mut processed = 0;

        // Verify Canary integrity (Start of Cycle)
        if CANARY != 0xAA {
            panic!("KERNEL PANIC: Canary corrupted! Memory violation detected.");
        }

        // Process in chunks of 4 (12 bytes) (Loop Unrolling)
        while diff(READ_HEAD, WRITE_HEAD, BUFFER_SIZE) >= 12 {
            let idx = READ_HEAD;

            // Explicitly unroll 4 calls
            process_single_vector(idx);
            process_single_vector((idx + 3) & (BUFFER_SIZE - 1));
            process_single_vector((idx + 6) & (BUFFER_SIZE - 1));
            process_single_vector((idx + 9) & (BUFFER_SIZE - 1));

            READ_HEAD = (READ_HEAD + 12) & (BUFFER_SIZE - 1);
            processed += 12;
        }

        // Handle remaining (1-3 vectors)
        while diff(READ_HEAD, WRITE_HEAD, BUFFER_SIZE) >= 3 {
            process_single_vector(READ_HEAD);
            READ_HEAD = (READ_HEAD + 3) & (BUFFER_SIZE - 1);
            processed += 3;
        }

        processed
    }
}

// New Function: Vector Addition (Batch)
// Adds vectors from BUFFER (A) and OUTPUT_BUFFER (B) -> OUTPUT_BUFFER (Result)
#[no_mangle]
pub extern "C" fn vector_add_batch(count: i32) -> i32 {
    unsafe {
        let n = count as usize;
        let mut processed = 0;

        let mut current_head = READ_HEAD;

        // Simple loop (no unrolling needed for now as it's memory bound)
        for _ in 0..n {
            let idx = current_head;
            let idx_y = (idx + 1) & (BUFFER_SIZE - 1);
            let idx_z = (idx + 2) & (BUFFER_SIZE - 1);

            // Simple addition: Out = In + Out (Clamped)
            let val_in_x = BUFFER[idx] as u16;
            let val_out_x = OUTPUT_BUFFER[idx] as u16;
            OUTPUT_BUFFER[idx] = ((val_in_x + val_out_x).min(255)) as u8;

            let val_in_y = BUFFER[idx_y] as u16;
            let val_out_y = OUTPUT_BUFFER[idx_y] as u16;
            OUTPUT_BUFFER[idx_y] = ((val_in_y + val_out_y).min(255)) as u8;

            let val_in_z = BUFFER[idx_z] as u16;
            let val_out_z = OUTPUT_BUFFER[idx_z] as u16;
            OUTPUT_BUFFER[idx_z] = ((val_in_z + val_out_z).min(255)) as u8;

            current_head = (current_head + 3) & (BUFFER_SIZE - 1);
            processed += 1;
        }
        processed as i32
    }
}

// Simulated Heavy Compute: Matrix Multiplication (4x4)
#[no_mangle]
pub extern "C" fn matrix_multiply_4x4(a_offset: i32, b_offset: i32, out_offset: i32) {
    unsafe {
        // Simple O(N^3) implementation for 4x4 matrix
        let a_idx = (a_offset as usize) & (BUFFER_SIZE - 1);
        let b_idx = (b_offset as usize) & (BUFFER_SIZE - 1);
        let out_idx = (out_offset as usize) & (BUFFER_SIZE - 1);

        if a_idx + 16 > BUFFER_SIZE || b_idx + 16 > BUFFER_SIZE || out_idx + 16 > BUFFER_SIZE {
            return;
        }

        for r in 0..4 {
            for c in 0..4 {
                let mut sum: u32 = 0;
                for k in 0..4 {
                    let a_val = BUFFER[a_idx + r * 4 + k] as u32;
                    let b_val = BUFFER[b_idx + k * 4 + c] as u32;
                    sum += a_val * b_val;
                }
                OUTPUT_BUFFER[out_idx + r * 4 + c] = (sum % 255) as u8;
            }
        }
    }
}

// New Function: Vector Dot Product (Batch)
// Computes dot product of Input * Output for 'count' vectors
#[no_mangle]
pub extern "C" fn vector_dot_batch(count: i32) -> i32 {
    unsafe {
        let n = count as usize;
        let mut dot_sum: i32 = 0;

        let mut current_head = READ_HEAD;

        for _ in 0..n {
            let idx = current_head;
            let idx_y = (idx + 1) & (BUFFER_SIZE - 1);
            let idx_z = (idx + 2) & (BUFFER_SIZE - 1);

            let in_x = BUFFER[idx] as i32;
            let out_x = OUTPUT_BUFFER[idx] as i32;
            dot_sum = dot_sum.wrapping_add(in_x * out_x);

            let in_y = BUFFER[idx_y] as i32;
            let out_y = OUTPUT_BUFFER[idx_y] as i32;
            dot_sum = dot_sum.wrapping_add(in_y * out_y);

            let in_z = BUFFER[idx_z] as i32;
            let out_z = OUTPUT_BUFFER[idx_z] as i32;
            dot_sum = dot_sum.wrapping_add(in_z * out_z);

            current_head = (current_head + 3) & (BUFFER_SIZE - 1);
        }
        dot_sum
    }
}

// Check Integrity (Canary)
#[no_mangle]
pub extern "C" fn check_integrity() -> i32 {
    unsafe {
        if CANARY == 0xAA {
            1 // Safe
        } else {
            0 // Corrupted
        }
    }
}
