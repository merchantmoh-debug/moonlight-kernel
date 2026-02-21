// Project Moonlight: Generated Kernel (V3.1)
// Auto-synthesized by Ark Sovereign Engine
// Target: Wasm-GC / Wasm-Linear

package lib

// --- The Fundamental Truth ---
// "Speed is Safety."

let buffer_size : Int = 65536
let input_buffer : FixedArray[Byte] = FixedArray::make(buffer_size, b'\x00')
let output_buffer : FixedArray[Byte] = FixedArray::make(buffer_size, b'\x00')
let canary : Byte = b'\xAA'

var read_head : Int = 0
var write_head : Int = 0

// --- Exports for Rust Host ---

pub fn get_buffer_size() -> Int {
  buffer_size
}

// NOTE: Zero-Copy exports removed for V3.1 safety.
// Direct memory access requires unsafe FFI or predictable layout.
// We default to the 'Legacy' Function Call interface for guaranteed stability.

pub fn set_write_head(pos : Int) -> Unit {
  if pos >= 0 {
    write_head = pos % buffer_size
  }
}

pub fn get_read_head() -> Int {
  read_head
}

pub fn set_input_byte(index : Int, val : Int) -> Unit {
  if index >= 0 {
    input_buffer[index % buffer_size] = val.to_byte()
  }
}

pub fn set_input_3_bytes(index : Int, x : Int, y : Int, z : Int) -> Unit {
  if index >= 0 {
    let idx = index % buffer_size
    input_buffer[idx] = x.to_byte()
    input_buffer[(idx + 1) % buffer_size] = y.to_byte()
    input_buffer[(idx + 2) % buffer_size] = z.to_byte()
  }
}

pub fn get_output_byte(index : Int) -> Int {
  if index >= 0 {
    output_buffer[index % buffer_size].to_int()
  } else {
    0
  }
}

// --- Vector Math ---

struct Vec3 {
  x : Double
  y : Double
  z : Double
}

fn Vec3::new(x : Double, y : Double, z : Double) -> Vec3 {
  { x, y, z }
}

fn Vec3::dot(self : Vec3, other : Vec3) -> Double {
  self.x * other.x + self.y * other.y + self.z * other.z
}

fn normalize(self : Vec3) -> Vec3 {
  let len = (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
  if len == 0.0 {
    self
  } else {
    { x: self.x / len, y: self.y / len, z: self.z / len }
  }
}

// --- Matrix Math ---

struct Matrix_Float64 {
  rows : Int
  cols : Int
  data : FixedArray[Double]
}

fn Matrix_Float64::new(rows : Int, cols : Int) -> Matrix_Float64 {
  { rows, cols, data: FixedArray::make(rows * cols, 0.0) }
}

fn Matrix_Float64::set(self : Matrix_Float64, row : Int, col : Int, val : Double) -> Unit {
  self.data[row * self.cols + col] = val
}

fn Matrix_Float64::get(self : Matrix_Float64, row : Int, col : Int) -> Double {
  self.data[row * self.cols + col]
}

fn Matrix_Float64::add(self : Matrix_Float64, other : Matrix_Float64) -> Matrix_Float64 {
  let res = Matrix_Float64::new(self.rows, self.cols)
  let mut i = 0
  while i < self.rows * self.cols {
    res.data[i] = self.data[i] + other.data[i]
    i = i + 1
  }
  res
}

struct Mat4x4 {
  m00 : Double; m01 : Double; m02 : Double; m03 : Double
  m10 : Double; m11 : Double; m12 : Double; m13 : Double
  m20 : Double; m21 : Double; m22 : Double; m23 : Double
  m30 : Double; m31 : Double; m32 : Double; m33 : Double
}

fn Mat4x4::identity() -> Mat4x4 {
  {
    m00: 1.0, m01: 0.0, m02: 0.0, m03: 0.0,
    m10: 0.0, m11: 1.0, m12: 0.0, m13: 0.0,
    m20: 0.0, m21: 0.0, m22: 1.0, m23: 0.0,
    m30: 0.0, m31: 0.0, m32: 0.0, m33: 1.0,
  }
}

// --- Kinetic Processing ---

fn diff(read : Int, write : Int, cap : Int) -> Int {
  if write >= read {
    write - read
  } else {
    (cap - read) + write
  }
}

pub fn process_tensor_stream() -> Int {
  let mut processed = 0

  // Kinetic Loop: Process chunks of 3 bytes (Vec3)
  while diff(read_head, write_head, buffer_size) >= 3 {
    let idx = read_head

    // 1. Read Raw Bytes (Function Call Interface)
    let x = input_buffer[idx].to_int().to_double()
    let y = input_buffer[(idx + 1) % buffer_size].to_int().to_double()
    let z = input_buffer[(idx + 2) % buffer_size].to_int().to_double()

    // 2. Compute (Neuronal Activation)
    let v = Vec3::new(x, y, z)
    let vn = v.normalize()

    // 3. Quantize Output (0-255 range mapping [-1, 1] -> [0, 200])
    // Matches Mock Kernel Logic: (nx * 100.0 + 100.0)
    let ox = (vn.x * 100.0 + 100.0).to_int()
    let oy = (vn.y * 100.0 + 100.0).to_int()
    let oz = (vn.z * 100.0 + 100.0).to_int()

    // 4. Write Output
    output_buffer[idx] = ox.to_byte()
    output_buffer[(idx + 1) % buffer_size] = oy.to_byte()
    output_buffer[(idx + 2) % buffer_size] = oz.to_byte()

    read_head = (read_head + 3) % buffer_size
    processed = processed + 3
  }

  processed
}

/// New Function: Vector Addition (Batch)
/// Adds vectors from input_buffer and output_buffer -> output_buffer (Result)
pub fn vector_add_batch(count : Int) -> Int {
  let mut processed = 0
  let mut current_head = read_head

  let mut i = 0
  while i < count {
    let idx = current_head

    // Simple addition: Out = In + Out (Clamped)
    let val_in_x = input_buffer[idx].to_int()
    let val_out_x = output_buffer[idx].to_int()
    let res_x = if val_in_x + val_out_x > 255 { 255 } else { val_in_x + val_out_x }
    output_buffer[idx] = res_x.to_byte()

    let idx_y = (idx + 1) % buffer_size
    let val_in_y = input_buffer[idx_y].to_int()
    let val_out_y = output_buffer[idx_y].to_int()
    let res_y = if val_in_y + val_out_y > 255 { 255 } else { val_in_y + val_out_y }
    output_buffer[idx_y] = res_y.to_byte()

    let idx_z = (idx + 2) % buffer_size
    let val_in_z = input_buffer[idx_z].to_int()
    let val_out_z = output_buffer[idx_z].to_int()
    let res_z = if val_in_z + val_out_z > 255 { 255 } else { val_in_z + val_out_z }
    output_buffer[idx_z] = res_z.to_byte()

    current_head = (current_head + 3) % buffer_size
    processed = processed + 1
    i = i + 1
  }
  processed
}

pub fn main() -> Unit {
  println("Moonlight Kernel: Initialized.")
}
