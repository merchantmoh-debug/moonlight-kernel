// Project Moonlight: The Kinetic Core
// "Speed is Safety."

package lib

/// A Ring Buffer structure.
/// For this MVP, we use safe accessors to avoid memory corruption.
struct RingBuffer {
  capacity : Int
  mut write_head : Int
  mut read_head : Int
  buffer : Array[Byte]
  output_buffer : Array[Byte]
}

// Global state
let ring : RingBuffer = {
  capacity: 1024,
  write_head: 0,
  read_head: 0,
  buffer: Array::make(1024, b'\x00'),
  output_buffer: Array::make(1024, b'\x00')
}

/// Safe Accessor: Host writes a byte to the buffer at a specific index.
pub fn set_input_byte(index : Int, val : Int) -> Unit {
  if index >= 0 {
    let safe_index = index % ring.capacity
    ring.buffer[safe_index] = val.to_byte()
  }
}

/// High-Performance Accessor: Host writes 3 bytes at once.
/// Reduces Wasm boundary crossing overhead by 3x.
pub fn set_input_3_bytes(index : Int, x : Int, y : Int, z : Int) -> Unit {
  if index >= 0 {
    let idx = index % ring.capacity
    ring.buffer[idx] = x.to_byte()
    ring.buffer[(idx + 1) % ring.capacity] = y.to_byte()
    ring.buffer[(idx + 2) % ring.capacity] = z.to_byte()
  }
}

/// Safe Accessor: Host updates the write head after filling the buffer.
pub fn set_write_head(pos : Int) -> Unit {
  if pos >= 0 {
    ring.write_head = pos % ring.capacity
  }
}

/// Safe Accessor: Host can read the current read head position.
pub fn get_read_head() -> Int {
  ring.read_head
}

/// Safe Accessor: Host reads a byte from the output buffer.
pub fn get_output_byte(index : Int) -> Int {
  if index >= 0 {
    let safe_index = index % ring.capacity
    ring.output_buffer[safe_index].to_int()
  } else {
    0
  }
}

/// The "Sovereign Logic": Process the buffer
/// Returns the number of bytes processed.
pub fn process_tensor_stream() -> Int {
  let mut processed_count = 0
  
  // "Hot Loop" - Process in chunks of 3 bytes (Vec3)
  while diff(ring.read_head, ring.write_head, ring.capacity) >= 3 {
    let idx = ring.read_head

    // 1. Read Inputs (Zero-Copy from Ring Buffer)
    let x = ring.buffer[idx].to_int().to_double()
    let y = ring.buffer[(idx + 1) % ring.capacity].to_int().to_double()
    let z = ring.buffer[(idx + 2) % ring.capacity].to_int().to_double()

    // 2. Compute (Neuronal Activation)
    let v = Vec3::new(x, y, z)
    let n = v.normalize()

    // 3. Write Outputs (Signal Response)
    // We scale the normalized vector components (-1.0 to 1.0)
    // to fit into a byte for visualization (0-255).
    // Mapping: v * 100 + 100. (e.g., 0 -> 100, 1 -> 200, -1 -> 0)

    let ox = (n.x * 100.0 + 100.0).to_int().to_byte()
    let oy = (n.y * 100.0 + 100.0).to_int().to_byte()
    let oz = (n.z * 100.0 + 100.0).to_int().to_byte()

    ring.output_buffer[idx] = ox
    ring.output_buffer[(idx + 1) % ring.capacity] = oy
    ring.output_buffer[(idx + 2) % ring.capacity] = oz

    // 4. Advance
    ring.read_head = (ring.read_head + 3) % ring.capacity
    processed_count = processed_count + 3
  }

  processed_count
}

// Helper for ring buffer difference
fn diff(read : Int, write : Int, cap : Int) -> Int {
  if write >= read {
    write - read
  } else {
    (cap - read) + write
  }
}

pub fn main() -> Unit {
  println("Moonlight Kernel: Initialized.")
}
