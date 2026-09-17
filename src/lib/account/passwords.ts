import { createHash, randomBytes, scryptSync, timingSafeEqual } from "node:crypto";

const KEY_LEN = 32;
const MIN_PASSWORD = 8;
const RESET_TOKEN_BYTES = 32;

export function normalizeEmail(raw: unknown): string {
  if (typeof raw !== "string") return "";
  return raw.trim().toLowerCase();
}

export function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export function validatePassword(raw: unknown): string {
  if (typeof raw !== "string") return "";
  return raw;
}

export function passwordIsStrong(password: string): boolean {
  return password.length >= MIN_PASSWORD;
}

export function hashPassword(password: string): string {
  const salt = randomBytes(16).toString("hex");
  const hash = scryptSync(password, salt, KEY_LEN).toString("hex");
  return `scrypt$${salt}$${hash}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  if (typeof stored !== "string" || !stored) return false;
  const parts = stored.split("$");
  if (parts.length !== 3 || parts[0] !== "scrypt") return false;
  const salt = parts[1];
  const hash = parts[2];
  if (!salt || !hash) return false;
  const next = scryptSync(password, salt, KEY_LEN).toString("hex");
  return timingSafeEqualHex(hash, next);
}

export function newPasswordResetToken(): string {
  return randomBytes(RESET_TOKEN_BYTES).toString("hex");
}

export function hashPasswordResetToken(token: string): string {
  return createHash("sha256").update(token).digest("hex");
}

export function isPasswordResetToken(value: string): boolean {
  return /^[0-9a-f]{64}$/i.test(value);
}

export function timingSafeEqualHex(left: string, right: string): boolean {
  const a = Buffer.from(left, "hex");
  const b = Buffer.from(right, "hex");
  if (!a.length || a.length !== b.length) return false;
  return timingSafeEqual(a, b);
}
