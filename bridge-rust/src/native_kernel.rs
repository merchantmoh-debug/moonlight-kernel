
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

    fn process_single_vector(&mut self, idx: usize) {
        let x = self.buffer[idx] as f64;
        let y = self.buffer[(idx + 1) & (BUFFER_SIZE - 1)] as f64;
        let z = self.buffer[(idx + 2) & (BUFFER_SIZE - 1)] as f64;

        // Normalize Logic
        let len = (x * x + y * y + z * z).sqrt();
        let (nx, ny, nz) = if len == 0.0 {
            (x, y, z)
        } else {
            (x / len, y / len, z / len)
        };

        // Scale to visualize direction: (nx * 100 + 100)
        self.output_buffer[idx] = (nx * 100.0 + 100.0) as u8;
        self.output_buffer[(idx + 1) & (BUFFER_SIZE - 1)] = (ny * 100.0 + 100.0) as u8;
        self.output_buffer[(idx + 2) & (BUFFER_SIZE - 1)] = (nz * 100.0 + 100.0) as u8;
    }

    pub fn process_tensor_stream(&mut self) -> i32 {
        let mut processed = 0;

        // Verify Canary
        if self.canary != 0xAA {
            panic!("KERNEL PANIC: Canary corrupted! Memory violation detected.");
        }

        // Process in chunks of 4 (12 bytes)
        while self.diff() >= 12 {
            let idx = self.read_head;

            self.process_single_vector(idx);
            self.process_single_vector((idx + 3) & (BUFFER_SIZE - 1));
            self.process_single_vector((idx + 6) & (BUFFER_SIZE - 1));
            self.process_single_vector((idx + 9) & (BUFFER_SIZE - 1));

            self.read_head = (self.read_head + 12) & (BUFFER_SIZE - 1);
            processed += 12;
        }

        // Handle remaining
        while self.diff() >= 3 {
            self.process_single_vector(self.read_head);
            self.read_head = (self.read_head + 3) & (BUFFER_SIZE - 1);
            processed += 3;
        }

        processed
    }

    pub fn vector_add_batch(&mut self, count: i32) -> i32 {
        let n = count as usize;
        let mut processed = 0;
        let mut current_head = self.read_head;

        for _ in 0..n {
            let idx = current_head;
            let idx_y = (idx + 1) & (BUFFER_SIZE - 1);
            let idx_z = (idx + 2) & (BUFFER_SIZE - 1);

            let val_in_x = self.buffer[idx] as u16;
            let val_out_x = self.output_buffer[idx] as u16;
            self.output_buffer[idx] = ((val_in_x + val_out_x).min(255)) as u8;

            let val_in_y = self.buffer[idx_y] as u16;
            let val_out_y = self.output_buffer[idx_y] as u16;
            self.output_buffer[idx_y] = ((val_in_y + val_out_y).min(255)) as u8;

            let val_in_z = self.buffer[idx_z] as u16;
            let val_out_z = self.output_buffer[idx_z] as u16;
            self.output_buffer[idx_z] = ((val_in_z + val_out_z).min(255)) as u8;

            current_head = (current_head + 3) & (BUFFER_SIZE - 1);
            processed += 1;
        }
        processed as i32
    }

    pub fn vector_dot_batch(&self, count: i32) -> i32 {
        let n = count as usize;
        let mut dot_sum: i32 = 0;
        let mut current_head = self.read_head;

        for _ in 0..n {
            let idx = current_head;
            let idx_y = (idx + 1) & (BUFFER_SIZE - 1);
            let idx_z = (idx + 2) & (BUFFER_SIZE - 1);

            let in_x = self.buffer[idx] as i32;
            let out_x = self.output_buffer[idx] as i32;
            dot_sum = dot_sum.wrapping_add(in_x * out_x);

            let in_y = self.buffer[idx_y] as i32;
            let out_y = self.output_buffer[idx_y] as i32;
            dot_sum = dot_sum.wrapping_add(in_y * out_y);

            let in_z = self.buffer[idx_z] as i32;
            let out_z = self.output_buffer[idx_z] as i32;
            dot_sum = dot_sum.wrapping_add(in_z * out_z);

            current_head = (current_head + 3) & (BUFFER_SIZE - 1);
        }
        dot_sum
    }

    pub fn check_integrity(&self) -> i32 {
        if self.canary == 0xAA { 1 } else { 0 }
    }
}
