// Mock Kernel (Rust) mimicking MoonBit Kernel Interface
// "The Mechanic's Ear" - Testing Rig

// Using a 64KB buffer for larger tensor operations
const BUFFER_SIZE: usize = 65536;

#[no_mangle]
pub static mut BUFFER: [u8; BUFFER_SIZE] = [0; BUFFER_SIZE];

#[no_mangle]
pub static mut OUTPUT_BUFFER: [u8; BUFFER_SIZE] = [0; BUFFER_SIZE];

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
            let idx = (index as usize) % BUFFER_SIZE;
            BUFFER[idx] = val as u8;
        }
    }
}

#[no_mangle]
pub extern "C" fn set_input_3_bytes(index: i32, x: i32, y: i32, z: i32) {
    unsafe {
        if index >= 0 {
            let idx = (index as usize) % BUFFER_SIZE;
            BUFFER[idx] = x as u8;
            BUFFER[(idx + 1) % BUFFER_SIZE] = y as u8;
            BUFFER[(idx + 2) % BUFFER_SIZE] = z as u8;
        }
    }
}

#[no_mangle]
pub extern "C" fn set_write_head(pos: i32) {
    unsafe {
        if pos >= 0 {
            WRITE_HEAD = (pos as usize) % BUFFER_SIZE;
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
            let idx = (index as usize) % BUFFER_SIZE;
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

#[no_mangle]
pub extern "C" fn process_tensor_stream() -> i32 {
    unsafe {
        let mut processed = 0;

        // Process in chunks of 3 (Vec3)
        while diff(READ_HEAD, WRITE_HEAD, BUFFER_SIZE) >= 3 {
            let idx = READ_HEAD;
            let x = BUFFER[idx] as f64;
            let y = BUFFER[(idx + 1) % BUFFER_SIZE] as f64;
            let z = BUFFER[(idx + 2) % BUFFER_SIZE] as f64;

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
            OUTPUT_BUFFER[(idx + 1) % BUFFER_SIZE] = (ny * 100.0 + 100.0) as u8;
            OUTPUT_BUFFER[(idx + 2) % BUFFER_SIZE] = (nz * 100.0 + 100.0) as u8;

            READ_HEAD = (READ_HEAD + 3) % BUFFER_SIZE;
            processed += 3;
        }

        processed
    }
}

// Simulated Heavy Compute: Matrix Multiplication (4x4)
// This function doesn't use the RingBuffer but operates on fixed offsets to simulate
// a pure compute kernel call.
#[no_mangle]
pub extern "C" fn matrix_multiply_4x4(a_offset: i32, b_offset: i32, out_offset: i32) {
    unsafe {
        // Simple O(N^3) implementation for 4x4 matrix
        // Assuming offsets are within BUFFER
        let a_idx = (a_offset as usize) % BUFFER_SIZE;
        let b_idx = (b_offset as usize) % BUFFER_SIZE;
        let out_idx = (out_offset as usize) % BUFFER_SIZE;

        // Safety: Ensure we don't read/write out of bounds
        if a_idx + 16 > BUFFER_SIZE || b_idx + 16 > BUFFER_SIZE || out_idx + 16 > BUFFER_SIZE {
            return;
        }

        // We treat the buffer as flat f32 arrays, but here we only have u8.
        // Let's pretend each u8 is a value for simplicity of the mock.
        // Or we can just do some math on the u8s.

        for r in 0..4 {
            for c in 0..4 {
                let mut sum: u32 = 0;
                for k in 0..4 {
                    let a_val = BUFFER[a_idx + r * 4 + k] as u32;
                    let b_val = BUFFER[b_idx + k * 4 + c] as u32;
                    sum += a_val * b_val;
                }
                // Store result modulo 255
                OUTPUT_BUFFER[out_idx + r * 4 + c] = (sum % 255) as u8;
            }
        }
    }
}
