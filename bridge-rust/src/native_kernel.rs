
pub const BUFFER_SIZE: usize = 65536;

#[allow(dead_code)]
pub struct NativeKernel {
    pub buffer: Vec<u8>,
    pub output_buffer: Vec<u8>,
    pub canary: u8,
    pub read_head: usize,
    pub write_head: usize,
}

impl NativeKernel {
    pub fn new() -> Self {
        Self {
            buffer: vec![0; BUFFER_SIZE],
            output_buffer: vec![0; BUFFER_SIZE],
            canary: 0xAA,
            read_head: 0,
            write_head: 0,
        }
    }

    #[allow(dead_code)]
    pub fn get_buffer_size(&self) -> i32 {
        BUFFER_SIZE as i32
    }

    pub fn set_write_head(&mut self, pos: i32) {
        if pos >= 0 {
            self.write_head = (pos as usize) & (BUFFER_SIZE - 1);
        }
    }

    #[allow(dead_code)]
    pub fn get_read_head(&self) -> i32 {
        self.read_head as i32
    }

    #[allow(dead_code)]
    pub fn get_output_byte(&self, index: i32) -> i32 {
        if index >= 0 {
            let idx = (index as usize) & (BUFFER_SIZE - 1);
            self.output_buffer[idx] as i32
        } else {
            0
        }
    }

    // Zero-Copy Simulation: In native mode, we access memory directly via slice
    #[allow(dead_code)]
    pub fn get_buffer_mut(&mut self) -> &mut [u8] {
        &mut self.buffer
    }

    #[allow(dead_code)]
    pub fn get_output_buffer(&self) -> &[u8] {
        &self.output_buffer
    }

    fn diff(&self) -> usize {
        if self.write_head >= self.read_head {
            self.write_head - self.read_head
        } else {
            (BUFFER_SIZE - self.read_head) + self.write_head
        }
    }

    // Inlined helper for single vector processing (Manual optimization)
    #[inline(always)]
    fn process_vector_at(&mut self, idx: usize) {
        // Unsafe block for raw speed? No, let's stay safe but fast with masks.
        // The mask (BUFFER_SIZE - 1) is 0xFFFF.

        // Read (Kinetic Input)
        let x = self.buffer[idx] as f64;
        let y = self.buffer[(idx + 1) & 0xFFFF] as f64;
        let z = self.buffer[(idx + 2) & 0xFFFF] as f64;

        // Compute (Neuronal Activation)
        // Optimization: Fast inverse square root could be used here, but let's stick to standard sqrt for precision.
        let len_sq = x * x + y * y + z * z;
        let (nx, ny, nz) = if len_sq > 0.0 {
            let len = len_sq.sqrt();
            (x / len, y / len, z / len)
        } else {
            (x, y, z)
        };

        // Write (Kinetic Output)
        // Avoiding bounds checks on write using the same mask logic if we were iterating randomly,
        // but here idx is from read_head so it wraps naturally.
        // We write to output_buffer at the same index.

        self.output_buffer[idx] = (nx * 100.0 + 100.0) as u8;
        self.output_buffer[(idx + 1) & 0xFFFF] = (ny * 100.0 + 100.0) as u8;
        self.output_buffer[(idx + 2) & 0xFFFF] = (nz * 100.0 + 100.0) as u8;
    }

    pub fn process_tensor_stream(&mut self) -> i32 {
        let mut processed = 0;

        // Verify Canary (Critical Security)
        if self.canary != 0xAA {
            panic!("KERNEL PANIC: Canary corrupted! Memory violation detected.");
        }

        // Kinetic Loop: Unrolled 4x (12 bytes)
        // We use a local copy of read_head to avoid &mut self conflicts if we split methods,
        // but since we inlined, we can use self directly.

        while self.diff() >= 12 {
            let idx = self.read_head;

            // Unrolled execution
            self.process_vector_at(idx);
            self.process_vector_at((idx + 3) & 0xFFFF);
            self.process_vector_at((idx + 6) & 0xFFFF);
            self.process_vector_at((idx + 9) & 0xFFFF);

            self.read_head = (self.read_head + 12) & 0xFFFF;
            processed += 12;
        }

        // Handle Residuals (1-3 vectors)
        while self.diff() >= 3 {
            self.process_vector_at(self.read_head);
            self.read_head = (self.read_head + 3) & 0xFFFF;
            processed += 3;
        }

        processed
    }

    pub fn vector_add_batch(&mut self, count: i32) -> i32 {
        let n = count as usize;
        let mut processed = 0;
        let mut idx = self.read_head;

        // Simple loop optimization: iterators are often faster but indices with masks are predictable.
        // We will process one vector (3 bytes) at a time.

        for _ in 0..n {
             // Inline the addition
            let idx_y = (idx + 1) & 0xFFFF;
            let idx_z = (idx + 2) & 0xFFFF;

            // SIMD-like logic (saturating add)
            self.output_buffer[idx] = self.output_buffer[idx].saturating_add(self.buffer[idx]);
            self.output_buffer[idx_y] = self.output_buffer[idx_y].saturating_add(self.buffer[idx_y]);
            self.output_buffer[idx_z] = self.output_buffer[idx_z].saturating_add(self.buffer[idx_z]);

            idx = (idx + 3) & 0xFFFF;
            processed += 1;
        }

        // Note: vector_add_batch in previous version updated read_head?
        // No, in the synthesis script it says "current_head = ...", it doesn't update the global read_head?
        // Wait, the synthesis script says: `current_head = (current_head + 3) % buffer_size` inside the loop,
        // but `read_head` variable is NOT updated at the end of the function in the script.
        // The previous Rust implementation used `current_head` local variable.
        // So this function acts as a "peek and modify" without consuming the stream?
        // Actually, looking at main.rs usage: `self.backend.vector_add_batch(processed_vecs)?;`
        // It's called after `process_tensor_stream`.
        // `process_tensor_stream` advances `read_head`.
        // So if `vector_add_batch` uses `read_head`, it's operating on *new* data?
        // Or is it supposed to operate on the data just processed?
        // In the synthesis script: `let mut current_head = read_head` -> It starts at the *current* read_head.
        // But `process_tensor_stream` has just advanced `read_head`.
        // So `vector_add_batch` operates on the *next* batch of data?
        // That seems to be the logic.

        processed as i32
    }

    pub fn vector_dot_batch(&self, count: i32) -> i32 {
        let n = count as usize;
        let mut dot_sum: i32 = 0;
        let mut idx = self.read_head;

        for _ in 0..n {
            let idx_y = (idx + 1) & 0xFFFF;
            let idx_z = (idx + 2) & 0xFFFF;

            let in_x = self.buffer[idx] as i32;
            let out_x = self.output_buffer[idx] as i32;
            let term_x = in_x * out_x;

            let in_y = self.buffer[idx_y] as i32;
            let out_y = self.output_buffer[idx_y] as i32;
            let term_y = in_y * out_y;

            let in_z = self.buffer[idx_z] as i32;
            let out_z = self.output_buffer[idx_z] as i32;
            let term_z = in_z * out_z;

            dot_sum = dot_sum.wrapping_add(term_x).wrapping_add(term_y).wrapping_add(term_z);

            idx = (idx + 3) & 0xFFFF;
        }
        dot_sum
    }

    pub fn check_integrity(&self) -> i32 {
        if self.canary == 0xAA { 1 } else { 0 }
    }
}
