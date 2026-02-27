
pub const BUFFER_SIZE: usize = 65536;
pub const MASK: usize = BUFFER_SIZE - 1;

#[allow(dead_code)]
pub struct NativeKernel {
    pub buffer: Vec<u8>,
    pub output_buffer: Vec<u8>,
    pub canary: u8,
    pub tail_canary: u8,
    pub read_head: usize,
    pub write_head: usize,
}

impl NativeKernel {
    pub fn new() -> Self {
        Self {
            buffer: vec![0; BUFFER_SIZE],
            output_buffer: vec![0; BUFFER_SIZE],
            canary: 0xAA,
            tail_canary: 0x55,
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
            self.write_head = (pos as usize) & MASK;
        }
    }

    #[allow(dead_code)]
    pub fn get_read_head(&self) -> i32 {
        self.read_head as i32
    }

    #[allow(dead_code)]
    pub fn get_output_byte(&self, index: i32) -> i32 {
        if index >= 0 {
            let idx = (index as usize) & MASK;
            self.output_buffer[idx] as i32
        } else {
            0
        }
    }

    #[allow(dead_code)]
    pub fn get_buffer_mut(&mut self) -> &mut [u8] {
        &mut self.buffer
    }

    #[allow(dead_code)]
    pub fn get_output_buffer(&self) -> &[u8] {
        &self.output_buffer
    }

    #[inline(always)]
    fn diff(&self) -> usize {
        if self.write_head >= self.read_head {
            self.write_head - self.read_head
        } else {
            (BUFFER_SIZE - self.read_head) + self.write_head
        }
    }

    #[inline(always)]
    fn process_vector_at(&mut self, idx: usize) {
        let x = self.buffer[idx] as f32;
        let y = self.buffer[(idx + 1) & MASK] as f32;
        let z = self.buffer[(idx + 2) & MASK] as f32;

        let len_sq = x * x + y * y + z * z;
        let (nx, ny, nz) = if len_sq > 0.0 {
            let len = len_sq.sqrt();
            (x / len, y / len, z / len)
        } else {
            (x, y, z)
        };

        self.output_buffer[idx] = (nx * 100.0 + 100.0) as u8;
        self.output_buffer[(idx + 1) & MASK] = (ny * 100.0 + 100.0) as u8;
        self.output_buffer[(idx + 2) & MASK] = (nz * 100.0 + 100.0) as u8;
    }

    #[inline(always)]
    fn process_contiguous_chunk_simd(in_slice: &[u8], out_slice: &mut [u8]) {
        // Optimized for larger chunks: 48 bytes = 16 vectors
        // This helps the compiler auto-vectorize more aggressively
        let mut chunks_in = in_slice.chunks_exact(48);
        let mut chunks_out = out_slice.chunks_exact_mut(48);

        for (inc, outc) in chunks_in.by_ref().zip(chunks_out.by_ref()) {
            for i in 0..16 {
                let off = i * 3;
                let x = inc[off] as f32;
                let y = inc[off+1] as f32;
                let z = inc[off+2] as f32;

                let len_sq = x*x + y*y + z*z;
                // Branchless select (approximate for f32)
                let (nx, ny, nz) = if len_sq > 0.0 {
                    let len = len_sq.sqrt();
                    (x/len, y/len, z/len)
                } else {
                    (x, y, z)
                };

                outc[off] = (nx * 100.0 + 100.0) as u8;
                outc[off+1] = (ny * 100.0 + 100.0) as u8;
                outc[off+2] = (nz * 100.0 + 100.0) as u8;
            }
        }

        // Handle remainder (blocks of 12)
        let remainder_in = chunks_in.remainder();
        let remainder_out = chunks_out.into_remainder();

        let mut sub_chunks_in = remainder_in.chunks_exact(12);
        let mut sub_chunks_out = remainder_out.chunks_exact_mut(12);

        for (inc, outc) in sub_chunks_in.by_ref().zip(sub_chunks_out.by_ref()) {
             for i in 0..4 {
                let off = i * 3;
                let x = inc[off] as f32;
                let y = inc[off+1] as f32;
                let z = inc[off+2] as f32;

                let len_sq = x*x + y*y + z*z;
                let (nx, ny, nz) = if len_sq > 0.0 {
                    let len = len_sq.sqrt();
                    (x/len, y/len, z/len)
                } else {
                    (x, y, z)
                };

                outc[off] = (nx * 100.0 + 100.0) as u8;
                outc[off+1] = (ny * 100.0 + 100.0) as u8;
                outc[off+2] = (nz * 100.0 + 100.0) as u8;
            }
        }
    }

    pub fn process_tensor_stream(&mut self) -> i32 {
        let mut processed = 0;

        if self.canary != 0xAA || self.tail_canary != 0x55 {
            panic!("KERNEL PANIC: Canary corrupted! Memory violation detected.");
        }

        let available = self.diff();
        if available < 3 { return 0; }

        let mut remaining = available;

        // 1. Process Contiguous Blocks (SIMD-Friendly)
        while remaining >= 48 {
            let contiguous_len = BUFFER_SIZE - self.read_head;

            if contiguous_len >= 48 {
                let processable = std::cmp::min(remaining, contiguous_len);
                let chunk_len = (processable / 48) * 48; // Align to 48

                if chunk_len > 0 {
                    let in_slice = &self.buffer[self.read_head .. self.read_head + chunk_len];
                    let out_slice = &mut self.output_buffer[self.read_head .. self.read_head + chunk_len];

                    Self::process_contiguous_chunk_simd(in_slice, out_slice);

                    self.read_head = (self.read_head + chunk_len) & MASK;
                    processed += chunk_len;
                    remaining -= chunk_len;
                    continue;
                }
            }

            // If split or just under 48 but >= 12, try fallback
            if contiguous_len < 48 && contiguous_len >= 12 {
                 // Process sub-chunk (12 bytes)
                 let chunk_len = (contiguous_len / 12) * 12;
                 // Manually handle via small loop
                 for k in 0..(chunk_len/3) {
                     self.process_vector_at((self.read_head + k*3) & MASK);
                 }
                 self.read_head = (self.read_head + chunk_len) & MASK;
                 processed += chunk_len;
                 remaining -= chunk_len;
                 continue;
            }

            // Fallback for wrapped data or small chunks
            if remaining >= 12 {
                // Process 4 vectors manually
                for k in 0..4 {
                    self.process_vector_at((self.read_head + k*3) & MASK);
                }
                self.read_head = (self.read_head + 12) & MASK;
                processed += 12;
                remaining -= 12;
            } else {
                break;
            }
        }

        // Final Cleanup (Residuals)
        while remaining >= 3 {
            self.process_vector_at(self.read_head);
            self.read_head = (self.read_head + 3) & MASK;
            processed += 3;
            remaining -= 3;
        }

        processed as i32
    }

    pub fn vector_add_batch(&mut self, count: i32) -> i32 {
        let n = count as usize;
        let mut processed = 0;
        let mut idx = self.read_head;

        // Unroll 4x for speed
        let mut i = 0;
        while i + 4 <= n {
            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            self.output_buffer[idx] = self.output_buffer[idx].saturating_add(self.buffer[idx]);
            self.output_buffer[idx_y] = self.output_buffer[idx_y].saturating_add(self.buffer[idx_y]);
            self.output_buffer[idx_z] = self.output_buffer[idx_z].saturating_add(self.buffer[idx_z]);
            idx = (idx + 3) & MASK;

            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            self.output_buffer[idx] = self.output_buffer[idx].saturating_add(self.buffer[idx]);
            self.output_buffer[idx_y] = self.output_buffer[idx_y].saturating_add(self.buffer[idx_y]);
            self.output_buffer[idx_z] = self.output_buffer[idx_z].saturating_add(self.buffer[idx_z]);
            idx = (idx + 3) & MASK;

            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            self.output_buffer[idx] = self.output_buffer[idx].saturating_add(self.buffer[idx]);
            self.output_buffer[idx_y] = self.output_buffer[idx_y].saturating_add(self.buffer[idx_y]);
            self.output_buffer[idx_z] = self.output_buffer[idx_z].saturating_add(self.buffer[idx_z]);
            idx = (idx + 3) & MASK;

            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            self.output_buffer[idx] = self.output_buffer[idx].saturating_add(self.buffer[idx]);
            self.output_buffer[idx_y] = self.output_buffer[idx_y].saturating_add(self.buffer[idx_y]);
            self.output_buffer[idx_z] = self.output_buffer[idx_z].saturating_add(self.buffer[idx_z]);
            idx = (idx + 3) & MASK;

            i += 4;
            processed += 4;
        }

        while i < n {
            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            self.output_buffer[idx] = self.output_buffer[idx].saturating_add(self.buffer[idx]);
            self.output_buffer[idx_y] = self.output_buffer[idx_y].saturating_add(self.buffer[idx_y]);
            self.output_buffer[idx_z] = self.output_buffer[idx_z].saturating_add(self.buffer[idx_z]);
            idx = (idx + 3) & MASK;
            i += 1;
            processed += 1;
        }

        processed as i32
    }

    pub fn vector_dot_batch(&self, count: i32) -> i32 {
        let n = count as usize;
        let mut dot_sum: i32 = 0;
        let mut idx = self.read_head;

        // Unroll 4x
        let mut i = 0;
        while i + 4 <= n {
            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            let term_x = (self.buffer[idx] as i32) * (self.output_buffer[idx] as i32);
            let term_y = (self.buffer[idx_y] as i32) * (self.output_buffer[idx_y] as i32);
            let term_z = (self.buffer[idx_z] as i32) * (self.output_buffer[idx_z] as i32);
            dot_sum = dot_sum.wrapping_add(term_x).wrapping_add(term_y).wrapping_add(term_z);
            idx = (idx + 3) & MASK;

            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            let term_x = (self.buffer[idx] as i32) * (self.output_buffer[idx] as i32);
            let term_y = (self.buffer[idx_y] as i32) * (self.output_buffer[idx_y] as i32);
            let term_z = (self.buffer[idx_z] as i32) * (self.output_buffer[idx_z] as i32);
            dot_sum = dot_sum.wrapping_add(term_x).wrapping_add(term_y).wrapping_add(term_z);
            idx = (idx + 3) & MASK;

            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            let term_x = (self.buffer[idx] as i32) * (self.output_buffer[idx] as i32);
            let term_y = (self.buffer[idx_y] as i32) * (self.output_buffer[idx_y] as i32);
            let term_z = (self.buffer[idx_z] as i32) * (self.output_buffer[idx_z] as i32);
            dot_sum = dot_sum.wrapping_add(term_x).wrapping_add(term_y).wrapping_add(term_z);
            idx = (idx + 3) & MASK;

            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            let term_x = (self.buffer[idx] as i32) * (self.output_buffer[idx] as i32);
            let term_y = (self.buffer[idx_y] as i32) * (self.output_buffer[idx_y] as i32);
            let term_z = (self.buffer[idx_z] as i32) * (self.output_buffer[idx_z] as i32);
            dot_sum = dot_sum.wrapping_add(term_x).wrapping_add(term_y).wrapping_add(term_z);
            idx = (idx + 3) & MASK;

            i += 4;
        }

        while i < n {
            let idx_y = (idx + 1) & MASK;
            let idx_z = (idx + 2) & MASK;
            let term_x = (self.buffer[idx] as i32) * (self.output_buffer[idx] as i32);
            let term_y = (self.buffer[idx_y] as i32) * (self.output_buffer[idx_y] as i32);
            let term_z = (self.buffer[idx_z] as i32) * (self.output_buffer[idx_z] as i32);
            dot_sum = dot_sum.wrapping_add(term_x).wrapping_add(term_y).wrapping_add(term_z);
            idx = (idx + 3) & MASK;
            i += 1;
        }
        dot_sum
    }

    pub fn check_integrity(&self) -> i32 {
        if self.canary == 0xAA && self.tail_canary == 0x55 { 1 } else { 0 }
    }
}
