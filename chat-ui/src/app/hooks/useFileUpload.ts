"use client";

import { useState, useCallback } from "react";
import {
  UploadedFile,
  ALLOWED_FILE_TYPES,
  MAX_FILE_SIZE,
} from "../types/fileUpload";

// Mock upload API
const mockUploadFile = async (
  file: File
): Promise<{ success: boolean; error?: string }> => {
  // Simulate upload delay
  await new Promise((resolve) =>
    setTimeout(resolve, 2000 + Math.random() * 3000)
  );

  // Simulate occasional failures (10% chance)
  if (Math.random() < 0.1) {
    return { success: false, error: "Upload failed. Please try again." };
  }

  // Log file info for debugging (using the file parameter)
  console.log(`Uploaded file: ${file.name} (${file.size} bytes)`);
  return { success: true };
};

export const useFileUpload = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [idCounter, setIdCounter] = useState(0);

  const validateFile = (file: File): { isValid: boolean; error?: string } => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return { isValid: false, error: "File size must be less than 10MB" };
    }

    // Check file type
    const allAllowedTypes = [
      ...ALLOWED_FILE_TYPES.image,
      ...ALLOWED_FILE_TYPES.document,
    ];
    if (
      !allAllowedTypes.includes(file.type as (typeof allAllowedTypes)[number])
    ) {
      return {
        isValid: false,
        error: "Only images, PDFs, and Word documents are allowed",
      };
    }

    return { isValid: true };
  };

  const createPreview = (file: File): string | undefined => {
    if (file.type.startsWith("image/")) {
      return URL.createObjectURL(file);
    }
    return undefined;
  };

  const uploadFile = useCallback(
    async (file: File) => {
      const validation = validateFile(file);
      const fileId = `file-${idCounter}`;
      setIdCounter((prev) => prev + 1);

      if (!validation.isValid) {
        const uploadedFile: UploadedFile = {
          id: fileId,
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          status: "error",
          errorMessage: validation.error,
          preview: createPreview(file),
        };
        setUploadedFiles((prev) => [...prev, uploadedFile]);
        return;
      }

      const uploadedFile: UploadedFile = {
        id: fileId,
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        status: "uploading",
        preview: createPreview(file),
      };

      setUploadedFiles((prev) => [...prev, uploadedFile]);

      try {
        const result = await mockUploadFile(file);

        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id
              ? {
                  ...f,
                  status: result.success ? "success" : "error",
                  errorMessage: result.error,
                }
              : f
          )
        );
      } catch (error) {
        console.error("Upload error:", error);
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id
              ? {
                  ...f,
                  status: "error",
                  errorMessage: "Upload failed. Please try again.",
                }
              : f
          )
        );
      }
    },
    [idCounter]
  );

  const removeFile = useCallback((fileId: string) => {
    setUploadedFiles((prev) => {
      const fileToRemove = prev.find((f) => f.id === fileId);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return prev.filter((f) => f.id !== fileId);
    });
  }, []);

  const clearAllFiles = useCallback(() => {
    uploadedFiles.forEach((file) => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });
    setUploadedFiles([]);
  }, [uploadedFiles]);

  const handleFiles = useCallback(
    (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      fileArray.forEach(uploadFile);
    },
    [uploadFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFiles(files);
      }
    },
    [handleFiles]
  );

  return {
    uploadedFiles,
    isDragOver,
    uploadFile,
    removeFile,
    clearAllFiles,
    handleFiles,
    handleDragOver,
    handleDragLeave,
    handleDrop,
  };
};
