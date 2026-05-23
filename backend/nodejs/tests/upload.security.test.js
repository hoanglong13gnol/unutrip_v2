import { describe, it, expect, vi } from "vitest";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { sniffImageMime, validateUploadedImageFiles } from "../src/shared/http/upload.js";

describe("upload security", () => {
  it("sniffImageMime accepts JPEG magic bytes", () => {
    const jpeg = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0, 0, 0, 0, 0, 0, 0, 0]);
    expect(sniffImageMime(jpeg)).toBe("image/jpeg");
  });

  it("sniffImageMime rejects non-image content", () => {
    const exe = Buffer.from("MZ", "ascii");
    expect(sniffImageMime(exe)).toBeNull();
  });

  it("validateUploadedImageFiles rejects .exe disguised as .jpg", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "unutrip-upload-"));
    const filePath = path.join(dir, "evil.jpg");
    fs.writeFileSync(filePath, Buffer.from("MZ"));

    const req = {
      file: { path: filePath, originalname: "evil.jpg" }
    };
    const res = {
      statusCode: 200,
      body: null,
      status(code) {
        this.statusCode = code;
        return this;
      },
      json(payload) {
        this.body = payload;
        return this;
      }
    };
    const next = vi.fn();

    validateUploadedImageFiles(req, res, next);

    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(400);
    expect(res.body.message).toMatch(/JPEG, PNG, or WebP/i);
    expect(fs.existsSync(filePath)).toBe(false);
  });

  it("validateUploadedImageFiles accepts real PNG bytes", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "unutrip-upload-"));
    const filePath = path.join(dir, "ok.png");
    const png = Buffer.from([
      0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0
    ]);
    fs.writeFileSync(filePath, png);

    const req = {
      file: { path: filePath, originalname: "ok.png" }
    };
    const res = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn()
    };
    const next = vi.fn();

    validateUploadedImageFiles(req, res, next);

    expect(next).toHaveBeenCalledTimes(1);
    expect(res.status).not.toHaveBeenCalled();
  });
});
