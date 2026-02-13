// Mock Kernel (Rust) mimicking MoonBit Kernel Interface
// "The Mechanic's Ear" - Testing Rig

#[no_mangle]
pub static mut BUFFER: [u8; 1024] = [0; 1024];

#[no_mangle]
pub static mut OUTPUT_BUFFER: [u8; 1024] = [0; 1024];

static mut READ_HEAD: usize = 0;
static mut WRITE_HEAD: usize = 0;
static CAPACITY: usize = 1024;

#[no_mangle]
pub extern "C" fn set_input_byte(index: i32, val: i32) {
    unsafe {
        if index >= 0 {
            let idx = (index as usize) % CAPACITY;
            BUFFER[idx] = val as u8;
        }
    }
}

#[no_mangle]
pub extern "C" fn set_input_3_bytes(index: i32, x: i32, y: i32, z: i32) {
    unsafe {
        if index >= 0 {
            let idx = (index as usize) % CAPACITY;
            BUFFER[idx] = x as u8;
            BUFFER[(idx + 1) % CAPACITY] = y as u8;
            BUFFER[(idx + 2) % CAPACITY] = z as u8;
        }
    }
}

#[no_mangle]
pub extern "C" fn set_write_head(pos: i32) {
    unsafe {
        if pos >= 0 {
            WRITE_HEAD = (pos as usize) % CAPACITY;
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
            let idx = (index as usize) % CAPACITY;
            OUTPUT_BUFFER[idx] as i32
        } else {
            0
        }
    }
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

        while diff(READ_HEAD, WRITE_HEAD, CAPACITY) >= 3 {
            // Read 3 bytes (Vec3)
            let idx = READ_HEAD;
            let x = BUFFER[idx] as f64;
            let y = BUFFER[(idx + 1) % CAPACITY] as f64;
            let z = BUFFER[(idx + 2) % CAPACITY] as f64;

            // Normalize Logic
            let len = (x*x + y*y + z*z).sqrt();
            let (nx, ny, nz) = if len == 0.0 {
                (x, y, z)
            } else {
                (x / len, y / len, z / len)
            };

            // Write to Output Buffer (Scaled back to 0-255 for visualization)
            // We map [-1.0, 1.0] -> [0, 255]? No, input is [0, 255].
            // Normalized vector components are usually <= 1.0.
            // Let's store them as (component * 100) + 100 to fit in byte?
            // Actually, let's just store the MAGNITUDE * 10 (which should be 10 if normalized correctly)
            // Or just store 255 if normalized, 0 if not.
            // Better: Store (nx * 127 + 128) to visualize direction.

            OUTPUT_BUFFER[idx] = (nx * 100.0 + 100.0) as u8;
            OUTPUT_BUFFER[(idx + 1) % CAPACITY] = (ny * 100.0 + 100.0) as u8;
            OUTPUT_BUFFER[(idx + 2) % CAPACITY] = (nz * 100.0 + 100.0) as u8;

            READ_HEAD = (READ_HEAD + 3) % CAPACITY;
            processed += 3;
        }

        processed
    }
}
