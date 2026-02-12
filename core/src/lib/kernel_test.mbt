package lib

// Project Moonlight: Verification Suite
// "Trust, but Verify."

test "Matrix_Float64::add" {
  let m1 = Matrix_Float64::new(2, 2)
  let m2 = Matrix_Float64::new(2, 2)
  
  // Set values
  m1.set(0, 0, 1.0); m1.set(0, 1, 2.0)
  m2.set(0, 0, 3.0); m2.set(0, 1, 4.0)
  
  let res = m1.add(m2)
  
  // Assertions (Primitive)
  if res.get(0, 0) != 4.0 { abort("Add Failed: 1+3 != 4") }
  if res.get(0, 1) != 6.0 { abort("Add Failed: 2+4 != 6") }
}

test "Vec3::dot" {
  let v1 = Vec3::new(1.0, 0.0, 0.0) // X-axis
  let v2 = Vec3::new(0.0, 1.0, 0.0) // Y-axis
  
  let dot = v1.dot(v2)
  
  if dot != 0.0 { abort("Dot Failed: Orthogonal vectors must be 0") }
  
  let v3 = Vec3::new(2.0, 0.0, 0.0)
  let dot2 = v1.dot(v3)
  
  if dot2 != 2.0 { abort("Dot Failed: Parallel vectors") }
}

test "Mat4x4::identity" {
  let id = Mat4x4::identity()
  
  // Check diagonal
  if id.m00 != 1.0 { abort("Identity Failed: m00") }
  if id.m11 != 1.0 { abort("Identity Failed: m11") }
  if id.m22 != 1.0 { abort("Identity Failed: m22") }
  if id.m33 != 1.0 { abort("Identity Failed: m33") }
  
  // Check off-diagonal
  if id.m01 != 0.0 { abort("Identity Failed: m01") }
}

test "Vec3::normalize" {
  // 1. Standard Vector (3, 0, 4) -> Magnitude 5
  let v1 = Vec3::new(3.0, 0.0, 4.0)
  let n1 = v1.normalize()
  if (n1.x - 0.6).abs() > 1e-9 { abort("Normalize Failed: x component") }
  if (n1.y - 0.0).abs() > 1e-9 { abort("Normalize Failed: y component") }
  if (n1.z - 0.8).abs() > 1e-9 { abort("Normalize Failed: z component") }

  // 2. Zero Vector (0, 0, 0) -> Should return itself safely
  let v_zero = Vec3::new(0.0, 0.0, 0.0)
  let n_zero = v_zero.normalize()
  if n_zero.x != 0.0 || n_zero.y != 0.0 || n_zero.z != 0.0 {
    abort("Normalize Failed: Zero vector should remain zero")
  }

  // 3. Single Component Vector (0, 10, 0) -> (0, 1, 0)
  let v2 = Vec3::new(0.0, 10.0, 0.0)
  let n2 = v2.normalize()
  if n2.x != 0.0 { abort("Normalize Failed: x component (single)") }
  if n2.y != 1.0 { abort("Normalize Failed: y component (single)") }
  if n2.z != 0.0 { abort("Normalize Failed: z component (single)") }
}
