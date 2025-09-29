export interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  status: "uploading" | "success" | "error";
  preview?: string;
  errorMessage?: string;
}

export type AllowedFileType = "image" | "document";

export const ALLOWED_FILE_TYPES = {
  image: ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"],
  document: [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ],
} as const;

export const ALLOWED_EXTENSIONS = {
  image: [".jpg", ".jpeg", ".png", ".gif", ".webp"],
  document: [".pdf", ".doc", ".docx"],
} as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
