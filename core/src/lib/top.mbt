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
}

// Global state
let ring : RingBuffer = {
  capacity: 1024,
  write_head: 0,
  read_head: 0,
  buffer: Array::make(1024, b'\x00')
}

/// Safe Accessor: Host writes a byte to the buffer at a specific index.
/// This prevents memory corruption by ensuring bounds checks.
pub fn set_input_byte(index : Int, val : Int) -> Unit {
  let safe_index = index % ring.capacity
  // Convert Int to Byte (truncating)
  ring.buffer[safe_index] = val.to_byte()
}

/// Safe Accessor: Host updates the write head after filling the buffer.
pub fn set_write_head(pos : Int) -> Unit {
  ring.write_head = pos % ring.capacity
}

/// Safe Accessor: Host can read the current read head position.
pub fn get_read_head() -> Int {
  ring.read_head
}

/// The "Sovereign Logic": Process the buffer
/// Returns the number of bytes processed.
pub fn process_tensor_stream() -> Int {
  let mut processed_count = 0
  
  // Weights for our "Neuron"
  let weights = Vec3::new(0.5, 0.5, 0.5)

  // "Hot Loop" - Process in chunks of 3 (Vec3)
  // Logic: read_head catches up to write_head

  // Handle wrapping logic is complex, so we simplify:
  // We process as long as we have 3 bytes available.

  while diff(ring.read_head, ring.write_head, ring.capacity) >= 3 {

    // 1. Load Data
    let r = ring.read_head
    let b1 = ring.buffer[r].to_int().to_double()
    let b2 = ring.buffer[(r + 1) % ring.capacity].to_int().to_double()
    let b3 = ring.buffer[(r + 2) % ring.capacity].to_int().to_double()
    
    // 2. Form Signal
    let signal = Vec3::new(b1, b2, b3)

    // 3. Neuro-Symbolic Operation (Dot Product)
    let activation = signal.dot(weights)

    // 4. Threshold Check (Mock Activation)
    if activation > 100.0 {
       ignore(activation)
    }

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
