// Project Moonlight: Generated Kernel
// Auto-synthesized by Ark Sovereign Engine
// Target: Wasm-GC / Wasm-Linear
// Version: 5.1.0 (Kinetic Realization)

package lib

// --- The Fundamental Truth ---
// "Speed is Safety."

// --- Matrix: Float64 ---
struct Matrix_Float64 {
  rows : Int
  cols : Int
  data : Array[Double]
}

pub fn Matrix_Float64::new(rows : Int, cols : Int) -> Matrix_Float64 {
  { rows, cols, data: Array::make(rows * cols, 0.0) }
}

pub fn get(self : Matrix_Float64, r : Int, c : Int) -> Double {
  self.data[r * self.cols + c]
}

pub fn set(self : Matrix_Float64, r : Int, c : Int, v : Double) -> Unit {
  self.data[r * self.cols + c] = v
}

pub fn transpose(self : Matrix_Float64) -> Matrix_Float64 {
  let res = Matrix_Float64::new(self.cols, self.rows)
  for i = 0; i < self.rows; i = i + 1 {
    for j = 0; j < self.cols; j = j + 1 {
      res.set(j, i, self.get(i, j))
    }
  }
  res
}

pub fn add(self : Matrix_Float64, other : Matrix_Float64) -> Matrix_Float64 {
  if self.rows != other.rows || self.cols != other.cols {
    abort("Matrix dimension mismatch in add")
  }
  let res = Matrix_Float64::new(self.rows, self.cols)
  for i = 0; i < self.rows * self.cols; i = i + 1 {
    res.data[i] = self.data[i] + other.data[i]
  }
  res
}

// Naive O(N^3) Multiplication
pub fn mul(self : Matrix_Float64, other : Matrix_Float64) -> Matrix_Float64 {
  if self.cols != other.rows {
    abort("Matrix dimension mismatch in mul")
  }
  let res = Matrix_Float64::new(self.rows, other.cols)
  for i = 0; i < self.rows; i = i + 1 {
    for j = 0; j < other.cols; j = j + 1 {
      let mut sum = 0.0
      for k = 0; k < self.cols; k = k + 1 {
        sum = sum + self.get(i, k) * other.get(k, j)
      }
      res.set(i, j, sum)
    }
  }
  res
}

// --- Fixed Matrix: Mat4x4 ---
struct Mat4x4 {
  m00 : Double
  m01 : Double
  m02 : Double
  m03 : Double
  m10 : Double
  m11 : Double
  m12 : Double
  m13 : Double
  m20 : Double
  m21 : Double
  m22 : Double
  m23 : Double
  m30 : Double
  m31 : Double
  m32 : Double
  m33 : Double
}

pub fn Mat4x4::identity() -> Mat4x4 {
  {
    m00 : 1.0,
    m01 : 0.0,
    m02 : 0.0,
    m03 : 0.0,
    m10 : 0.0,
    m11 : 1.0,
    m12 : 0.0,
    m13 : 0.0,
    m20 : 0.0,
    m21 : 0.0,
    m22 : 1.0,
    m23 : 0.0,
    m30 : 0.0,
    m31 : 0.0,
    m32 : 0.0,
    m33 : 1.0
  }
}

// --- Vector: Vec3 ---
struct Vec3 {
  x : Double
  y : Double
  z : Double
}

pub fn Vec3::new(x : Double, y : Double, z : Double) -> Vec3 {
  { x, y, z }
}

pub fn dot(self : Vec3, other : Vec3) -> Double {
  self.x * other.x + self.y * other.y + self.z * other.z
}

pub fn normalize(self : Vec3) -> Vec3 {
  let len = (self.dot(self)).sqrt()
  if len == 0.0 {
     self
  } else {
     { x: self.x / len, y: self.y / len, z: self.z / len }
  }
}
