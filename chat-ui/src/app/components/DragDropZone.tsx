"use client";

import { ReactNode } from "react";

interface DragDropZoneProps {
  children: ReactNode;
  isDragOver: boolean;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  className?: string;
}

export default function DragDropZone({
  children,
  isDragOver,
  onDragOver,
  onDragLeave,
  onDrop,
  className = "",
}: DragDropZoneProps) {
  return (
    <div
      className={`relative ${className}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {children}

      {/* Drag Overlay */}
      {isDragOver && (
        <div className="absolute inset-0 bg-blue-500 bg-opacity-10 border-2 border-dashed border-blue-500 rounded-lg flex items-center justify-center z-50">
          <div className="text-center">
            <div className="mb-4">
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-blue-500 mx-auto"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17,8 12,3 7,8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p className="text-blue-600 font-medium text-lg">Drop files here</p>
            <p className="text-blue-500 text-sm mt-1">
              Images, PDFs, and Word documents
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
