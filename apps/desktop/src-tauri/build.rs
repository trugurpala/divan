use std::fs;
use std::path::PathBuf;

const ICON_SIZES: [u32; 6] = [32, 16, 24, 48, 64, 256];

fn push_u16(buffer: &mut Vec<u8>, value: u16) {
    buffer.extend_from_slice(&value.to_le_bytes());
}

fn push_u32(buffer: &mut Vec<u8>, value: u32) {
    buffer.extend_from_slice(&value.to_le_bytes());
}

fn push_i32(buffer: &mut Vec<u8>, value: i32) {
    buffer.extend_from_slice(&value.to_le_bytes());
}

fn icon_pixel(size: u32, x: u32, y: u32) -> [u8; 4] {
    let scale = size.max(1);
    let left = scale * 7 / 32;
    let top = scale * 6 / 32;
    let bottom = scale * 26 / 32;
    let stem_right = scale * 11 / 32;
    let bar_right = scale * 18 / 32;
    let stroke = (scale * 3 / 32).max(1);

    let stem = x >= left && x <= stem_right && y >= top && y <= bottom;
    let top_bar = x >= left && x <= bar_right && y >= top && y <= top + stroke;
    let bottom_bar =
        x >= left && x <= bar_right && y + stroke >= bottom && y <= bottom;

    let center_x = (scale * 17 / 32) as i64;
    let center_y = (scale / 2) as i64;
    let outer_rx = (scale * 9 / 32).max(2) as i64;
    let outer_ry = (scale * 10 / 32).max(2) as i64;
    let inner_rx = (outer_rx - stroke as i64).max(1);
    let inner_ry = (outer_ry - stroke as i64).max(1);
    let dx = x as i64 - center_x;
    let dy = y as i64 - center_y;
    let outer = dx * dx * outer_ry * outer_ry + dy * dy * outer_rx * outer_rx
        <= outer_rx * outer_rx * outer_ry * outer_ry;
    let inner = dx * dx * inner_ry * inner_ry + dy * dy * inner_rx * inner_rx
        < inner_rx * inner_rx * inner_ry * inner_ry;
    let curve = x >= bar_right.saturating_sub(stroke) && outer && !inner;

    if stem || top_bar || bottom_bar || curve {
        [72, 184, 224, 255]
    } else {
        [24, 22, 18, 255]
    }
}

fn dib_layer(size: u32) -> Vec<u8> {
    let width = size as usize;
    let pixel_bytes = width * width * 4;
    let mask_stride = width.div_ceil(32) * 4;
    let mask_bytes = mask_stride * width;
    let mut dib = Vec::with_capacity(40 + pixel_bytes + mask_bytes);

    push_u32(&mut dib, 40);
    push_i32(&mut dib, size as i32);
    push_i32(&mut dib, (size * 2) as i32);
    push_u16(&mut dib, 1);
    push_u16(&mut dib, 32);
    push_u32(&mut dib, 0);
    push_u32(&mut dib, (pixel_bytes + mask_bytes) as u32);
    push_i32(&mut dib, 0);
    push_i32(&mut dib, 0);
    push_u32(&mut dib, 0);
    push_u32(&mut dib, 0);

    for y in (0..size).rev() {
        for x in 0..size {
            dib.extend_from_slice(&icon_pixel(size, x, y));
        }
    }
    dib.resize(dib.len() + mask_bytes, 0);
    dib
}

fn build_icon() -> Vec<u8> {
    let layers = ICON_SIZES
        .iter()
        .copied()
        .map(|size| (size, dib_layer(size)))
        .collect::<Vec<_>>();
    let table_size = 6 + layers.len() * 16;
    let capacity = table_size + layers.iter().map(|(_, data)| data.len()).sum::<usize>();
    let mut icon = Vec::with_capacity(capacity);

    push_u16(&mut icon, 0);
    push_u16(&mut icon, 1);
    push_u16(&mut icon, layers.len() as u16);

    let mut offset = table_size as u32;
    for (size, data) in &layers {
        icon.push(if *size == 256 { 0 } else { *size as u8 });
        icon.push(if *size == 256 { 0 } else { *size as u8 });
        icon.push(0);
        icon.push(0);
        push_u16(&mut icon, 1);
        push_u16(&mut icon, 32);
        push_u32(&mut icon, data.len() as u32);
        push_u32(&mut icon, offset);
        offset += data.len() as u32;
    }

    for (_, data) in layers {
        icon.extend_from_slice(&data);
    }
    icon
}

fn ensure_generated_icon() {
    let icon_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("icons")
        .join("divan-generated.ico");
    let icon = build_icon();
    let current = fs::read(&icon_path).ok();
    if current.as_deref() == Some(icon.as_slice()) {
        return;
    }
    if let Some(parent) = icon_path.parent() {
        fs::create_dir_all(parent).expect("failed to create Divan Desktop icon directory");
    }
    fs::write(&icon_path, icon).expect("failed to write Divan Desktop generated icon");
}

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    ensure_generated_icon();
    tauri_build::build()
}
