import multer from "multer";
import path from "node:path";
import fs from "node:fs";

const uploadsDir = path.resolve(process.cwd(), "uploads", "reviews");
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true });

const avatarsDir = path.resolve(process.cwd(), "uploads", "avatars");
if (!fs.existsSync(avatarsDir)) fs.mkdirSync(avatarsDir, { recursive: true });

const ALLOWED_EXT = /\.(jpe?g|png|webp)$/i;

/** @param {Buffer | undefined} buffer */
export function sniffImageMime(buffer) {
  if (!buffer || buffer.length < 12) return null;
  if (buffer[0] === 0xff && buffer[1] === 0xd8 && buffer[2] === 0xff) return "image/jpeg";
  if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4e && buffer[3] === 0x47) {
    return "image/png";
  }
  if (
    buffer[0] === 0x52 &&
    buffer[1] === 0x49 &&
    buffer[2] === 0x46 &&
    buffer[3] === 0x46 &&
    buffer[8] === 0x57 &&
    buffer[9] === 0x45 &&
    buffer[10] === 0x42 &&
    buffer[11] === 0x50
  ) {
    return "image/webp";
  }
  return null;
}

function removeUploadedFile(file) {
  if (!file?.path) return;
  try {
    fs.unlinkSync(file.path);
  } catch {
    /* ignore */
  }
}

/** Express middleware — run after multer; validates magic bytes. */
export function validateUploadedImageFiles(req, res, next) {
  const files = [];
  if (req.file) files.push(req.file);
  if (Array.isArray(req.files)) files.push(...req.files);

  for (const file of files) {
    const original = file.originalname || "";
    if (!ALLOWED_EXT.test(original)) {
      removeUploadedFile(file);
      return res.status(400).json({
        success: false,
        message: "Only JPEG, PNG, or WebP images are allowed"
      });
    }

    let buf;
    try {
      buf = fs.readFileSync(file.path);
    } catch {
      removeUploadedFile(file);
      return res.status(400).json({ success: false, message: "Invalid upload" });
    }

    if (!sniffImageMime(buf)) {
      removeUploadedFile(file);
      return res.status(400).json({
        success: false,
        message: "Only JPEG, PNG, or WebP images are allowed"
      });
    }
  }

  next();
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    if (file.fieldname === "avatar") cb(null, avatarsDir);
    else cb(null, uploadsDir);
  },
  filename: (req, file, cb) =>
    cb(null, `${Date.now()}-${Math.round(Math.random() * 1e6)}${path.extname(file.originalname)}`)
});

export const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    cb(null, ALLOWED_EXT.test(path.extname(file.originalname || "").toLowerCase()));
  }
});
