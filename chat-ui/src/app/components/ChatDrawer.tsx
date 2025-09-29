"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { useFileUpload } from "../hooks/useFileUpload";
import FileUploadPreview from "./FileUploadPreview";
import FileUploadButton from "./FileUploadButton";
import {
  chatApi,
  ChatMessageRequest,
  StreamChunk,
  AsyncReportRequest,
  InterruptionResponse,
  ResponseModeChoice,
  AsyncTaskStatus,
} from "../services/chatApi";

// Mock upload function that simulates uploading documents to an endpoint
const mockUploadDocument = async (
  file: File
): Promise<{ url: string; docType: string }> => {
  // Simulate upload delay
  await new Promise((resolve) =>
    setTimeout(resolve, 1000 + Math.random() * 2000)
  );

  // Simulate occasional failures (5% chance)
  if (Math.random() < 0.05) {
    throw new Error("Upload failed. Please try again.");
  }

  // Generate mock URL and determine document type
  const docType = file.type.includes("pdf")
    ? "PDF"
    : file.type.includes("word")
    ? "Word"
    : file.type.includes("image")
    ? "Image"
    : "Document";

  const mockUrl = `https://api.example.com/documents/${Date.now()}-${
    file.name
  }`;

  console.log(`Mock upload: ${file.name} -> ${mockUrl} (${docType})`);

  return { url: mockUrl, docType };
};

// Mock function to send message to backend AI agent (kept for reference)
// const sendToBackend = async (message: Message) => {
//   // Simulate API call delay
//   await new Promise((resolve) =>
//     setTimeout(resolve, 500 + Math.random() * 1000)
//   );

//   console.log("Sending to backend AI agent:", {
//     id: message.id,
//     isUser: message.isUser,
//     timestamp: message.timestamp,
//     payload: message.payload,
//   });

//   // Simulate occasional backend failures (2% chance)
//   if (Math.random() < 0.02) {
//     throw new Error("Backend service temporarily unavailable");
//   }

//   return { success: true, messageId: message.id };
// };

// Client-side only timestamp component to prevent hydration issues
const ClientOnlyTimestamp = ({
  timestamp,
  className,
}: {
  timestamp: Date;
  className?: string;
}) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <span className={`text-xs mt-1 ${className || "text-gray-500"}`}>
        --:--
      </span>
    );
  }

  return (
    <span className={`text-xs mt-1 ${className || "text-gray-500"}`}>
      {timestamp.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })}
    </span>
  );
};

// Choice message component for inline choices
const ChoiceMessage = ({
  message,
  onChoiceSelect,
}: {
  message: Message;
  onChoiceSelect: (
    choice: "stream" | "async",
    originalMessage: Message
  ) => void;
}) => {
  const choices = message.payload?.choices || [];
  const originalMessage = message.metadata?.originalMessage as Message;

  return (
    <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
        <svg
          className="w-4 h-4 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 mb-3">{message.text}</p>
        <div className="space-y-2">
          {choices.map((choice) => (
            <button
              key={choice.id}
              onClick={() => onChoiceSelect(choice.action, originalMessage)}
              className={`w-full p-3 rounded-lg border transition-colors flex items-center justify-between ${
                choice.action === "stream"
                  ? "bg-blue-50 border-blue-200 hover:bg-blue-100 text-blue-800"
                  : "bg-green-50 border-green-200 hover:bg-green-100 text-green-800"
              }`}
            >
              <div className="flex items-center space-x-3">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center ${
                    choice.action === "stream" ? "bg-blue-500" : "bg-green-500"
                  }`}
                >
                  <svg
                    className="w-3 h-3 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    {choice.action === "stream" ? (
                      <>
                        <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                        <path d="M3 3v5h5" />
                      </>
                    ) : (
                      <>
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                        <polyline points="3.27,6.96 12,12.01 20.73,6.96" />
                        <line x1="12" y1="22.08" x2="12" y2="12" />
                      </>
                    )}
                  </svg>
                </div>
                <div className="text-left">
                  <div className="font-medium text-sm">{choice.label}</div>
                  <div className="text-xs opacity-75">{choice.description}</div>
                </div>
              </div>
              <svg
                className="w-4 h-4 opacity-50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// Accordion component for async reports
const AsyncReportAccordion = ({
  userMessage,
  reportMessage,
  reportTitle,
  isExpanded,
  onToggle,
}: {
  userMessage: Message;
  reportMessage: Message;
  reportTitle: string;
  isExpanded: boolean;
  onToggle: () => void;
}) => {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* User Message Header */}
      <div
        className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <svg
              className="w-4 h-4 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {reportTitle}
            </p>
            <p className="text-xs text-gray-500">
              Report Request • {userMessage.timestamp.toLocaleTimeString()}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">
            Completed
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${
              isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {/* Report Content */}
      {isExpanded && (
        <div className="border-t border-gray-200">
          <div className="p-4 bg-gray-50">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                <svg
                  className="w-4 h-4 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <div className="bg-white rounded-lg p-3 border border-gray-200">
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-sm text-gray-800">
                      {reportMessage.text}
                    </div>
                  </div>
                  <ClientOnlyTimestamp
                    timestamp={reportMessage.timestamp}
                    className="text-gray-500 mt-2"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Document preview component for different file types
const DocumentPreview = ({
  file,
  docType,
  files,
}: {
  file?: File;
  docType?: string;
  files?: File[];
}) => {
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);

  useEffect(() => {
    const filesToProcess = files || (file ? [file] : []);
    const imageFiles = filesToProcess.filter((f) =>
      f.type.startsWith("image/")
    );

    if (imageFiles.length > 0) {
      const urls = imageFiles.map((f) => URL.createObjectURL(f));
      setPreviewUrls(urls);
      return () => urls.forEach((url) => URL.revokeObjectURL(url));
    }
  }, [file, files]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileIcon = (fileType?: string) => {
    const type = fileType || docType;
    switch (type) {
      case "PDF":
        return (
          <svg
            className="w-full h-full"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14,2 14,8 20,8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10,9 9,9 8,9" />
          </svg>
        );
      case "Word":
        return (
          <svg
            className="w-full h-full"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14,2 14,8 20,8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10,9 9,9 8,9" />
          </svg>
        );
      case "Image":
        return (
          <svg
            className="w-full h-full"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21,15 16,10 5,21" />
          </svg>
        );
      default:
        return (
          <svg
            className="w-full h-full"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14,2 14,8 20,8" />
          </svg>
        );
    }
  };

  const getIconColor = (fileType?: string) => {
    const type = fileType || docType;
    switch (type) {
      case "PDF":
        return "bg-red-100 text-red-600";
      case "Word":
        return "bg-blue-100 text-blue-600";
      case "Image":
        return "bg-green-100 text-green-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const filesToProcess = files || (file ? [file] : []);

  // If we have multiple files of the same type, show them in a grid
  if (filesToProcess.length > 1) {
    return (
      <div
        className="mt-1 border border-gray-200 rounded-lg overflow-hidden bg-white w-full"
        style={{ containerType: "inline-size" }}
      >
        {/* File Grid */}
        <div
          className="grid gap-2 p-3 w-full"
          style={{
            gridTemplateColumns: `repeat(auto-fit, minmax(80px, 1fr))`,
            width: "100%",
            gridAutoRows: "minmax(100px, auto)",
          }}
        >
          {filesToProcess.map((fileItem, index) => {
            const isImage = fileItem.type.startsWith("image/");
            const previewUrl = isImage ? previewUrls[index] : null;

            // Determine individual file type for each file
            const individualFileType = fileItem.type.includes("pdf")
              ? "PDF"
              : fileItem.type.includes("word")
              ? "Word"
              : fileItem.type.includes("image")
              ? "Image"
              : "Document";

            return (
              <div
                key={index}
                className="relative aspect-square overflow-hidden rounded-lg bg-gray-50 flex flex-col items-center justify-center border border-gray-200 hover:border-gray-300 transition-colors w-full h-full"
              >
                {isImage && previewUrl ? (
                  <Image
                    src={previewUrl}
                    alt={fileItem.name}
                    width={120}
                    height={120}
                    className="w-full h-full object-cover"
                    unoptimized
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full p-2">
                    <div
                      className={`w-12 h-12 rounded-lg flex items-center justify-center mb-2 ${getIconColor(
                        individualFileType
                      )}`}
                    >
                      <div className="w-6 h-6">
                        {getFileIcon(individualFileType)}
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 text-center truncate w-full px-1">
                      {fileItem.name.length > 12
                        ? `${fileItem.name.substring(0, 12)}...`
                        : fileItem.name}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {individualFileType}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* File Info */}
        <div className="p-2 border-t border-gray-100">
          <p className="text-xs font-medium text-gray-900">
            {filesToProcess.length}{" "}
            {filesToProcess.length === 1 ? "file" : "files"} uploaded
          </p>
          <p className="text-xs text-gray-500">
            Total size:{" "}
            {formatFileSize(filesToProcess.reduce((sum, f) => sum + f.size, 0))}
          </p>
        </div>
      </div>
    );
  }

  // Single file display (existing logic)
  return (
    <div className="mt-1 border border-gray-200 rounded-lg overflow-hidden bg-white w-full">
      {/* Single Image Preview */}
      {previewUrls.length > 0 && (
        <div className="max-h-20 overflow-hidden relative">
          <Image
            src={previewUrls[0]}
            alt={file?.name || ""}
            width={200}
            height={80}
            className="w-full h-auto object-cover"
            unoptimized
          />
        </div>
      )}

      {/* Document Info */}
      <div className="p-2 flex items-center space-x-2">
        <div
          className={`flex-shrink-0 w-6 h-6 rounded flex items-center justify-center ${getIconColor()}`}
        >
          <div className="w-3 h-3">{getFileIcon()}</div>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-900 truncate">
            {file?.name || "File"}
          </p>
          <p className="text-xs text-gray-500">
            {docType} • {formatFileSize(file?.size || 0)}
          </p>
        </div>
        <div className="flex-shrink-0">
          <button
            onClick={() => {
              if (file) {
                const url = URL.createObjectURL(file);
                const a = document.createElement("a");
                a.href = url;
                a.download = file.name;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
              }
            }}
            className="text-blue-600 hover:text-blue-800 text-xs font-medium"
          >
            ↓
          </button>
        </div>
      </div>
    </div>
  );
};

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  threadId: string;
  payload?: {
    type: "text" | "document" | "choice";
    content?: string;
    url?: string;
    docType?: string;
    file?: File; // For local preview
    files?: File[]; // For multiple files
    choices?: Array<{
      id: string;
      label: string;
      description: string;
      action: "stream" | "async";
    }>;
  };
  // Backend API fields
  message_id?: string;
  content?: string;
  is_user?: boolean;
  message_type?: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

interface Thread {
  id: string;
  title: string;
  createdAt: Date;
  lastMessageAt: Date;
  // Backend API fields
  thread_id?: string;
  message_count?: number;
  last_message_preview?: string;
}

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatDrawer({ isOpen, onClose }: ChatDrawerProps) {
  // Thread management state
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string>("");
  const [isLoadingThreads, setIsLoadingThreads] = useState(false);
  const [threadsError, setThreadsError] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);

  const [inputText, setInputText] = useState("");
  const [drawerWidth, setDrawerWidth] = useState(384); // Default 96 * 4 = 384px (w-96)
  const [isResizing, setIsResizing] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [userHasScrolled, setUserHasScrolled] = useState(false);
  const [messageIdCounter, setMessageIdCounter] = useState(1);
  const [isUploading, setIsUploading] = useState(false);
  const [isThreadSidebarOpen, setIsThreadSidebarOpen] = useState(false);

  // Chat API states
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");

  // Async task states
  const [pendingInterruption, setPendingInterruption] =
    useState<InterruptionResponse | null>(null);
  const [isProcessingAsync, setIsProcessingAsync] = useState(false);
  const [completedTasks, setCompletedTasks] = useState<AsyncTaskStatus[]>([]);
  const [activeTasks, setActiveTasks] = useState<Set<string>>(new Set());
  const [notifications, setNotifications] = useState<AsyncTaskStatus[]>([]);
  const [acceptingTask, setAcceptingTask] = useState<string | null>(null);

  // Accordion state for async reports
  const [expandedAccordions, setExpandedAccordions] = useState<Set<string>>(
    new Set()
  );
  const drawerRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // File upload functionality
  const {
    uploadedFiles,
    isDragOver,
    handleFiles,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    removeFile,
    clearAllFiles,
  } = useFileUpload();

  // Thread management functions
  const createNewThread = async () => {
    try {
      setIsLoadingThreads(true);
      setThreadsError(null);

      const response = await chatApi.createThread({
        title: "New Conversation",
        metadata: { user_id: "user-1" }, // TODO: Get from auth context
      });

      const newThread: Thread = {
        id: response.thread_id,
        thread_id: response.thread_id,
        title: response.title,
        createdAt: new Date(response.created_at),
        lastMessageAt: new Date(response.last_message_at),
      };

      setThreads((prev) => [newThread, ...prev]);
      setCurrentThreadId(response.thread_id);

      // Clear input and uploaded files when creating new thread
      setInputText("");
      clearAllFiles();
      setMessages([]);
      // Reset scroll state when creating new thread
      setUserHasScrolled(false);
      setShowScrollButton(false);
    } catch (error) {
      console.error("Failed to create thread:", error);
      setThreadsError(
        error instanceof Error ? error.message : "Failed to create thread"
      );
    } finally {
      setIsLoadingThreads(false);
    }
  };

  const switchToThread = async (threadId: string) => {
    setCurrentThreadId(threadId);
    // Clear input and uploaded files when switching threads
    setInputText("");
    clearAllFiles();
    // Reset scroll state when switching threads
    setUserHasScrolled(false);
    setShowScrollButton(false);

    // Load messages for the selected thread
    await loadThreadMessages(threadId);

    // Always scroll to bottom when switching threads
    setTimeout(() => scrollToBottom(), 100);
  };

  const loadThreads = async () => {
    try {
      setIsLoadingThreads(true);
      setThreadsError(null);

      const threadSummaries = await chatApi.listThreads();

      const threads: Thread[] = threadSummaries.map((summary) => ({
        id: summary.thread_id,
        thread_id: summary.thread_id,
        title: summary.title,
        createdAt: new Date(summary.created_at),
        lastMessageAt: new Date(summary.last_message_at),
        message_count: summary.message_count,
        last_message_preview: summary.last_message_preview,
      }));

      setThreads(threads);

      // If no current thread is selected and we have threads, select the first one
      if (!currentThreadId && threads.length > 0) {
        setCurrentThreadId(threads[0].id);
        await loadThreadMessages(threads[0].id);
      }
    } catch (error) {
      console.error("Failed to load threads:", error);
      setThreadsError(
        error instanceof Error ? error.message : "Failed to load threads"
      );
    } finally {
      setIsLoadingThreads(false);
    }
  };

  const loadThreadMessages = async (threadId: string) => {
    try {
      setIsLoadingMessages(true);
      setMessagesError(null);

      const messageResponses = await chatApi.getThreadMessages(threadId);

      const messages: Message[] = messageResponses
        .filter((msg) => {
          // Filter out interruption messages from backend
          const metadata = msg.metadata || {};
          const isInterruption =
            metadata.interruption || metadata.awaiting_choice;

          // Also filter by content pattern as backup
          const isInterruptionByContent =
            msg.content.includes("I understand you want a report generated") ||
            msg.content.includes(
              "How would you like to receive the response"
            ) ||
            msg.content.includes(
              "Please choose your preferred response mode"
            ) ||
            msg.content.includes("Streaming Response") ||
            msg.content.includes("Async Response");

          const shouldFilter = isInterruption || isInterruptionByContent;

          // Debug logging
          if (shouldFilter) {
            console.log("Filtering out interruption message:", {
              content: msg.content.substring(0, 100) + "...",
              metadata: metadata,
              reason: isInterruption ? "metadata" : "content",
            });
          }

          return !shouldFilter;
        })
        .map((msg) => ({
          id: msg.message_id,
          message_id: msg.message_id,
          text: msg.content,
          content: msg.content,
          isUser: msg.is_user,
          is_user: msg.is_user,
          timestamp: new Date(msg.created_at),
          created_at: msg.created_at,
          threadId: threadId,
          message_type: msg.message_type,
          metadata: msg.metadata,
          payload: {
            type: msg.message_type === "document" ? "document" : "text",
            content: msg.content,
          },
        }));

      setMessages(messages);
    } catch (error) {
      console.error("Failed to load thread messages:", error);
      setMessagesError(
        error instanceof Error ? error.message : "Failed to load messages"
      );
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const getCurrentThreadMessages = () => {
    return messages.filter((message) => message.threadId === currentThreadId);
  };

  const updateThreadLastMessage = (threadId: string, timestamp: Date) => {
    setThreads((prev) =>
      prev.map((thread) =>
        thread.id === threadId
          ? { ...thread, lastMessageAt: timestamp }
          : thread
      )
    );
  };

  const getShortenedThreadId = (threadId: string) => {
    // Extract the number from thread-{number} and show as #1, #2, etc.
    const match = threadId.match(/thread-(\d+)/);
    return match ? `#${match[1]}` : threadId;
  };

  const toggleAccordion = (accordionId: string) => {
    setExpandedAccordions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(accordionId)) {
        newSet.delete(accordionId);
      } else {
        newSet.add(accordionId);
      }
      return newSet;
    });
  };

  // Utility function to extract report title from content
  const extractReportTitle = (
    content: string,
    userMessage: string,
    metadata?: Record<string, unknown>
  ): string => {
    // First, check if title is provided in metadata (from backend)
    if (metadata?.report_title && typeof metadata.report_title === "string") {
      return metadata.report_title;
    }

    // Then, try to extract title from markdown headers in the content
    const headerMatch = content.match(/^#\s+(.+)$/m);
    if (headerMatch) {
      return headerMatch[1].trim();
    }

    // Try to extract from other markdown patterns
    const altHeaderMatch = content.match(/^##\s+(.+)$/m);
    if (altHeaderMatch) {
      return altHeaderMatch[1].trim();
    }

    // Try to extract from the first line if it looks like a title
    const firstLine = content.split("\n")[0].trim();
    if (
      firstLine.length > 0 &&
      firstLine.length < 100 &&
      !firstLine.includes(".")
    ) {
      return firstLine;
    }

    // Fallback: generate title from user message
    const userWords = userMessage.toLowerCase();
    if (userWords.includes("report about")) {
      const topic = userMessage.split(/report about/i)[1]?.trim();
      return topic ? `Report: ${topic}` : "Research Report";
    } else if (userWords.includes("report on")) {
      const topic = userMessage.split(/report on/i)[1]?.trim();
      return topic ? `Report: ${topic}` : "Research Report";
    } else if (userWords.includes("analysis of")) {
      const topic = userMessage.split(/analysis of/i)[1]?.trim();
      return topic ? `Analysis: ${topic}` : "Analysis Report";
    } else if (userWords.includes("generate") && userWords.includes("report")) {
      const words = userMessage.split(" ");
      const topicWords = [];
      for (let i = 0; i < words.length; i++) {
        if (
          words[i].toLowerCase() === "about" ||
          words[i].toLowerCase() === "on"
        ) {
          topicWords.push(...words.slice(i + 1, i + 6));
          break;
        }
      }
      const topic = topicWords.join(" ").replace(/[?!.]/g, "").trim();
      return topic ? `Report: ${topic}` : "Research Report";
    }

    // Final fallback
    return "Research Report";
  };

  const getAsyncReportPairs = (messages: Message[]) => {
    const pairs: Array<{
      userMessage: Message;
      reportMessage: Message;
      accordionId: string;
      reportTitle: string;
    }> = [];
    const processedMessages = new Set<string>();

    console.log(
      "DEBUG: getAsyncReportPairs called with",
      messages.length,
      "messages"
    );

    // First, look for consecutive messages (original pattern)
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i];

      // Skip if already processed
      if (processedMessages.has(message.id)) continue;

      // Look for async report pattern: user message followed by AI report
      if (message.isUser && i + 1 < messages.length) {
        const nextMessage = messages[i + 1];

        // Check if next message is an async AI report
        // Async reports have specific metadata indicating they were generated asynchronously
        const isAsyncReport =
          !nextMessage.isUser &&
          (nextMessage.metadata?.workflow_used === "report_researcher" ||
            nextMessage.metadata?.completed_task === true) &&
          (nextMessage.metadata?.response_mode === "async" ||
            nextMessage.metadata?.async_task_id) && // Key indicator: async response mode or async task ID
          nextMessage.text.length > 100; // Report content is typically longer

        if (isAsyncReport) {
          console.log(
            "DEBUG: Found async report pair:",
            message.text,
            "->",
            nextMessage.text.substring(0, 100)
          );
          const accordionId = `accordion-${message.id}`;
          const reportTitle = extractReportTitle(
            nextMessage.text,
            message.text,
            nextMessage.metadata
          );
          pairs.push({
            userMessage: message,
            reportMessage: nextMessage,
            accordionId,
            reportTitle,
          });

          // Mark both messages as processed
          processedMessages.add(message.id);
          processedMessages.add(nextMessage.id);
        }
      }
    }

    // Second, look for completed task messages that weren't paired above
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i];

      // Skip if already processed
      if (processedMessages.has(message.id)) continue;

      // Check if this is a completed task message
      const isCompletedTask =
        !message.isUser &&
        message.metadata?.completed_task === true &&
        (message.metadata?.workflow_used === "report_researcher" ||
          message.metadata?.async_task_id) &&
        (message.metadata?.response_mode === "async" ||
          message.metadata?.async_task_id);

      if (isCompletedTask) {
        console.log(
          "DEBUG: Found completed task message:",
          message.text.substring(0, 100)
        );
        // Find the most recent user message that hasn't been paired yet
        let userMessage: Message | null = null;
        for (let j = i - 1; j >= 0; j--) {
          const candidateMessage = messages[j];
          if (
            candidateMessage.isUser &&
            !processedMessages.has(candidateMessage.id)
          ) {
            userMessage = candidateMessage;
            break;
          }
        }

        if (userMessage) {
          const accordionId = `accordion-${userMessage.id}`;
          const reportTitle = extractReportTitle(
            message.text,
            userMessage.text,
            message.metadata
          );
          pairs.push({
            userMessage,
            reportMessage: message,
            accordionId,
            reportTitle,
          });

          // Mark both messages as processed
          processedMessages.add(userMessage.id);
          processedMessages.add(message.id);
        }
      }
    }

    return pairs;
  };

  // Backend API functions
  const sendChatMessageToBackend = async (message: Message) => {
    if (!currentThreadId) return;

    try {
      setIsSendingMessage(true);

      const request: ChatMessageRequest = {
        thread_id: currentThreadId,
        content: message.text,
        message_type: message.payload?.type || "text",
        metadata: {
          user_id: "user-1", // TODO: Get from auth context
          ...message.metadata,
        },
      };

      // Check if this should be async (for report generation)
      if (
        message.text.toLowerCase().includes("report") ||
        message.text.toLowerCase().includes("analysis") ||
        message.text.toLowerCase().includes("research")
      ) {
        // Add the user message to chat
        setMessages((prev) => [...prev, message]);

        // Send to async endpoint to create interruption
        const asyncRequest: AsyncReportRequest = {
          thread_id: currentThreadId,
          content: message.text,
          message_type: message.payload?.type || "text",
          metadata: {
            user_id: "user-1",
            ...message.metadata,
          },
        };

        const interruption = await chatApi.createAsyncReport(asyncRequest);
        setPendingInterruption(interruption);
        return;
      }

      // For regular messages, use streaming
      await streamChatMessage(request);
    } catch (error) {
      console.error("Failed to send message to backend:", error);

      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        text: `❌ Failed to send message: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        isUser: false,
        timestamp: new Date(),
        threadId: currentThreadId,
        payload: {
          type: "text",
          content: `❌ Failed to send message: ${
            error instanceof Error ? error.message : "Unknown error"
          }`,
        },
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const streamChatMessage = async (request: ChatMessageRequest) => {
    if (!currentThreadId) return;

    try {
      setIsStreaming(true);
      setStreamingContent("");

      // Create a placeholder message for streaming
      const streamingMessageId = `streaming-${Date.now()}`;

      const streamingMessage: Message = {
        id: streamingMessageId,
        text: "",
        isUser: false,
        timestamp: new Date(),
        threadId: currentThreadId,
        payload: {
          type: "text",
          content: "",
        },
        metadata: {
          streaming: true,
        },
      };

      setMessages((prev) => [...prev, streamingMessage]);

      await chatApi.streamChatMessage(
        request,
        (chunk: StreamChunk) => {
          if (chunk.type === "content") {
            setStreamingContent((prev) => {
              const newContent = prev + chunk.data.content;

              // Update the streaming message with the new content
              setMessages((prevMessages) =>
                prevMessages.map((msg) =>
                  msg.id === streamingMessageId
                    ? { ...msg, text: newContent }
                    : msg
                )
              );

              return newContent;
            });
          } else if (chunk.type === "metadata") {
            console.log("Stream metadata:", chunk.data);
          } else if (chunk.type === "error") {
            console.error("Stream error:", chunk.data);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === streamingMessageId
                  ? {
                      ...msg,
                      text: `❌ Error: ${chunk.data.error_message}`,
                      metadata: { ...msg.metadata, error: true },
                    }
                  : msg
              )
            );
          } else if (chunk.type === "end") {
            console.log("Stream completed");
            // Remove streaming indicator and finalize the message
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === streamingMessageId
                  ? {
                      ...msg,
                      metadata: { ...msg.metadata, streaming: false },
                    }
                  : msg
              )
            );
          }
        },
        (error) => {
          console.error("Stream error:", error);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === streamingMessageId
                ? {
                    ...msg,
                    text: `❌ Stream error: ${error.message}`,
                    metadata: { ...msg.metadata, error: true },
                  }
                : msg
            )
          );
        },
        () => {
          console.log("Stream completed");
        }
      );
    } catch (error) {
      console.error("Failed to stream message:", error);
    } finally {
      setIsStreaming(false);
      setStreamingContent("");
      // Ensure streaming indicator is removed
      setMessages((prev) =>
        prev.map((msg) =>
          msg.metadata?.streaming
            ? { ...msg, metadata: { ...msg.metadata, streaming: false } }
            : msg
        )
      );
    }
  };

  const handleChoiceSelection = async (
    choice: "stream" | "async",
    originalMessage: Message
  ) => {
    try {
      setIsSendingMessage(true);

      // Add user's choice as a message
      const choiceResponseMessage: Message = {
        id: `choice-response-${Date.now()}`,
        text:
          choice === "stream"
            ? "Stream Report Generation"
            : "Generate Complete Report",
        isUser: true,
        timestamp: new Date(),
        threadId: currentThreadId,
        payload: {
          type: "text",
          content:
            choice === "stream"
              ? "Stream Report Generation"
              : "Generate Complete Report",
        },
      };

      setMessages((prev) => [...prev, choiceResponseMessage]);

      if (choice === "stream") {
        // Use streaming for the message
        const request: ChatMessageRequest = {
          thread_id: currentThreadId,
          content: originalMessage.text,
          message_type: originalMessage.payload?.type || "text",
          metadata: {
            user_id: "user-1",
            ...originalMessage.metadata,
          },
          response_mode: "stream",
        };

        await streamChatMessage(request);
      } else {
        // Use async for the message
        const asyncRequest: AsyncReportRequest = {
          thread_id: currentThreadId,
          content: originalMessage.text,
          message_type: originalMessage.payload?.type || "text",
          metadata: {
            user_id: "user-1",
            ...originalMessage.metadata,
          },
        };

        const interruption = await chatApi.createAsyncReport(asyncRequest);
        setPendingInterruption(interruption);
      }
    } catch (error) {
      console.error("Failed to handle choice selection:", error);

      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        text: "Failed to process your request. Please try again.",
        isUser: false,
        timestamp: new Date(),
        threadId: currentThreadId,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleResponseModeChoice = async (choice: "stream" | "async") => {
    if (!pendingInterruption) return;

    try {
      setIsProcessingAsync(true);

      const responseModeChoice: ResponseModeChoice = {
        task_id: pendingInterruption.task_id,
        response_mode: choice,
        user_id: "user-1", // TODO: Get from auth context
      };

      const response = await chatApi.handleResponseModeChoice(
        responseModeChoice
      );

      // Clear the pending interruption
      setPendingInterruption(null);

      // Add user choice message
      const choiceMessage: Message = {
        id: `choice-${Date.now()}`,
        text: `I choose ${choice} response mode`,
        isUser: true,
        timestamp: new Date(),
        threadId: currentThreadId,
        payload: {
          type: "text",
          content: `I choose ${choice} response mode`,
        },
      };

      setMessages((prev) => [...prev, choiceMessage]);

      // Add AI confirmation message
      const confirmationMessage: Message = {
        id: `confirmation-${Date.now()}`,
        text: response.message,
        isUser: false,
        timestamp: new Date(),
        threadId: currentThreadId,
        payload: {
          type: "text",
          content: response.message,
        },
        metadata: {
          task_id: response.task_id,
          response_mode: choice,
        },
      };

      setMessages((prev) => [...prev, confirmationMessage]);

      if (choice === "stream") {
        // For streaming, we need to connect to the streaming endpoint
        // Find the original user message from the chat history
        const originalMessage = messages.find(
          (msg) =>
            (msg.isUser && msg.text.toLowerCase().includes("report")) ||
            msg.text.toLowerCase().includes("analysis") ||
            msg.text.toLowerCase().includes("research")
        );

        if (originalMessage) {
          const streamRequest: ChatMessageRequest = {
            thread_id: currentThreadId,
            content: originalMessage.text,
            message_type: originalMessage.payload?.type || "text",
            metadata: {
              user_id: "user-1",
              ...originalMessage.metadata,
            },
            response_mode: "stream",
          };

          await streamChatMessage(streamRequest);
        }
      } else if (choice === "async") {
        // Add to active tasks for monitoring
        setActiveTasks((prev) => new Set(prev).add(response.task_id));
      }

      // Clear the pending interruption after processing
      setPendingInterruption(null);
    } catch (error) {
      console.error("Failed to handle response mode choice:", error);
    } finally {
      setIsProcessingAsync(false);
    }
  };

  const pollTaskStatus = async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await chatApi.getTaskStatus(taskId);

        if (status.status === "completed") {
          clearInterval(pollInterval);

          // Add the completed result as a message
          if (status.result) {
            const resultMessage: Message = {
              id: `result-${taskId}`,
              text: status.result,
              isUser: false,
              timestamp: new Date(status.updated_at),
              threadId: currentThreadId,
              payload: {
                type: "text",
                content: status.result,
              },
              metadata: {
                task_id: taskId,
                completed: true,
              },
            };

            setMessages((prev) => [...prev, resultMessage]);
          }
        } else if (status.status === "failed") {
          clearInterval(pollInterval);

          // Add error message
          const errorMessage: Message = {
            id: `error-${taskId}`,
            text: `❌ Task failed: ${status.error || "Unknown error"}`,
            isUser: false,
            timestamp: new Date(status.updated_at),
            threadId: currentThreadId,
            payload: {
              type: "text",
              content: `❌ Task failed: ${status.error || "Unknown error"}`,
            },
            metadata: {
              task_id: taskId,
              error: true,
            },
          };

          setMessages((prev) => [...prev, errorMessage]);
        }
      } catch (error) {
        console.error("Failed to poll task status:", error);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds
  };

  // Task monitoring functions for async tasks
  const checkTaskStatus = async (taskId: string) => {
    try {
      const status = await chatApi.getTaskStatus(taskId);

      // Debug: Log the status to see what fields are available
      console.log(`Task ${taskId} status:`, status);

      if (status.status === "completed") {
        // Task completed - add to notifications
        setNotifications((prev) => {
          const exists = prev.some((task) => task.task_id === taskId);
          if (!exists) {
            return [...prev, status];
          }
          return prev;
        });

        // Remove from active tasks
        setActiveTasks((prev) => {
          const newSet = new Set(prev);
          newSet.delete(taskId);
          return newSet;
        });

        // Add to completed tasks
        setCompletedTasks((prev) => {
          const exists = prev.some((task) => task.task_id === taskId);
          if (!exists) {
            return [...prev, status];
          }
          return prev;
        });
      } else if (status.status === "failed") {
        // Task failed - remove from active tasks
        setActiveTasks((prev) => {
          const newSet = new Set(prev);
          newSet.delete(taskId);
          return newSet;
        });
      }
    } catch (error) {
      console.error(`Failed to check status for task ${taskId}:`, error);
    }
  };

  const acceptTaskResult = async (task: AsyncTaskStatus) => {
    setAcceptingTask(task.task_id);

    try {
      // Debug: Log the task object to see what fields are available
      console.log("Accepting task result:", task);

      // Remove from notifications
      setNotifications((prev) =>
        prev.filter((t) => t.task_id !== task.task_id)
      );
      // Try to fetch the latest messages from the thread to get the actual AI response
      const threadMessages = await chatApi.getThreadMessages(currentThreadId);

      // Debug: Log all messages to see what we're getting
      console.log("All thread messages:", threadMessages);
      console.log("Looking for task_id:", task.task_id);

      // Find the message that was created by this async task
      const asyncMessage = threadMessages.find(
        (msg) =>
          msg.metadata &&
          msg.metadata.async_task_id === task.task_id &&
          !msg.is_user
      );

      let resultContent = "Task completed successfully";

      // Prioritize task.result as it contains the actual report content
      if (task.result) {
        resultContent = task.result;
        console.log("Using task result:", task.result);
      } else if (asyncMessage) {
        // Use the actual AI response from the message
        resultContent = asyncMessage.content;
        console.log("Found async message:", asyncMessage);
      } else if (task.message) {
        // Fallback to task message
        resultContent = `Task completed: ${task.message}`;
        console.log("Using task message:", task.message);
      } else {
        // Debug: Show what we found
        console.log(
          "No async message found. Available messages with metadata:"
        );
        threadMessages.forEach((msg, index) => {
          if (msg.metadata) {
            console.log(`Message ${index}:`, {
              content: msg.content.substring(0, 100) + "...",
              metadata: msg.metadata,
              is_user: msg.is_user,
            });
          }
        });
      }

      // Create the result message
      const resultMessage: Message = {
        id: `result-${task.task_id}`,
        text: resultContent,
        isUser: false,
        timestamp: new Date(task.updated_at),
        threadId: currentThreadId,
        payload: {
          type: "text",
          content: resultContent,
        },
        metadata: {
          task_id: task.task_id,
          completed_task: true,
          original_task: task, // Store the full task object for debugging
          workflow_used: "report_researcher", // Required for accordion display
          response_mode: "async", // Required for accordion display
        },
      };

      // Add the result message to the chat
      // The getAsyncReportPairs function will handle pairing it with the appropriate user message
      setMessages((prev) => [...prev, resultMessage]);
    } catch (error) {
      console.error("Failed to fetch async task result:", error);

      // Fallback to basic result
      const resultMessage: Message = {
        id: `result-${task.task_id}`,
        text: task.result || task.message || "Task completed successfully",
        isUser: false,
        timestamp: new Date(task.updated_at),
        threadId: currentThreadId,
        payload: {
          type: "text",
          content: task.result || task.message || "Task completed successfully",
        },
        metadata: {
          task_id: task.task_id,
          completed_task: true,
          workflow_used: "report_researcher", // Required for accordion display
          response_mode: "async", // Required for accordion display
        },
      };

      setMessages((prev) => [...prev, resultMessage]);
    } finally {
      setAcceptingTask(null);
    }
  };

  const dismissNotification = (taskId: string) => {
    setNotifications((prev) => prev.filter((task) => task.task_id !== taskId));
  };

  // Polling effect for active async tasks
  useEffect(() => {
    if (activeTasks.size === 0) return;

    const interval = setInterval(() => {
      activeTasks.forEach((taskId) => {
        checkTaskStatus(taskId);
      });
    }, 3000); // Check every 3 seconds

    return () => clearInterval(interval);
  }, [activeTasks]);

  const updateThreadTitle = (threadId: string, messageText: string) => {
    setThreads((prev) =>
      prev.map((thread) =>
        thread.id === threadId && thread.title === "New Conversation"
          ? {
              ...thread,
              title:
                messageText.length > 30
                  ? `${messageText.substring(0, 30)}...`
                  : messageText,
            }
          : thread
      )
    );
  };

  const handleSendMessage = async () => {
    if (!currentThreadId) {
      console.error("No thread selected");
      return;
    }

    if (inputText.trim() || uploadedFiles.length > 0) {
      const textToSend = inputText.trim();
      setInputText("");

      // If there are uploaded files, upload them first
      if (uploadedFiles.length > 0) {
        setIsUploading(true);
        try {
          // Upload all files and create a single unified document message
          const uploadPromises = uploadedFiles.map((f) =>
            mockUploadDocument(f.file)
          );
          const uploadResults = await Promise.all(uploadPromises);

          // Create a single unified document message with all files
          const now = new Date();
          const unifiedDocumentMessage: Message = {
            id: messageIdCounter.toString(),
            text:
              uploadedFiles.length === 1
                ? `📄 Document uploaded: ${uploadedFiles[0].name}`
                : `📄 ${uploadedFiles.length} documents uploaded`,
            isUser: true,
            timestamp: now,
            threadId: currentThreadId,
            payload: {
              type: "document",
              url: uploadResults[0]?.url || "",
              docType: "Mixed", // Mixed type for multiple file types
              files: uploadedFiles.map((f) => f.file),
            },
          };

          setMessageIdCounter((prev) => prev + 1);
          setMessages((prev) => [...prev, unifiedDocumentMessage]);

          // Send unified document message to backend
          try {
            await sendChatMessageToBackend(unifiedDocumentMessage);
          } catch (error) {
            console.error("Failed to send document to backend:", error);
          }

          // Clear uploaded files after successful upload
          clearAllFiles();
        } catch (error) {
          console.error("Upload failed:", error);
          // Add error message
          const errorMessage: Message = {
            id: messageIdCounter.toString(),
            text: `❌ Upload failed: ${
              error instanceof Error ? error.message : "Unknown error"
            }`,
            isUser: true,
            timestamp: new Date(),
            threadId: currentThreadId,
          };
          setMessageIdCounter((prev) => prev + 1);
          setMessages((prev) => [...prev, errorMessage]);
          return;
        } finally {
          setIsUploading(false);
        }
      }

      // If there's text, send it as a regular message
      if (textToSend) {
        const now = new Date();
        const textMessage: Message = {
          id: messageIdCounter.toString(),
          text: textToSend,
          isUser: true,
          timestamp: now,
          threadId: currentThreadId,
          payload: {
            type: "text",
            content: textToSend,
          },
        };
        setMessageIdCounter((prev) => prev + 1);
        setMessages((prev) => [...prev, textMessage]);

        // Update thread's last message timestamp
        updateThreadLastMessage(currentThreadId, now);

        // Update thread title if it's the first user message
        const currentThreadMessages = messages.filter(
          (m) => m.threadId === currentThreadId && m.isUser
        );
        if (currentThreadMessages.length === 0) {
          updateThreadTitle(currentThreadId, textToSend);
        }

        // Send text message to backend
        try {
          await sendChatMessageToBackend(textMessage);
        } catch (error) {
          console.error("Failed to send text message to backend:", error);
        }
      }

      // Auto-scroll to bottom when sending a message
      setTimeout(() => scrollToBottom(), 100);
    }
  };

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
      // Reset scroll state when programmatically scrolling to bottom
      setUserHasScrolled(false);
      setShowScrollButton(false);
    }
  };

  const handleScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        messagesContainerRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;

      // Track if user has manually scrolled up
      if (!isNearBottom && scrollTop > 0) {
        setUserHasScrolled(true);
      } else if (isNearBottom) {
        setUserHasScrolled(false);
      }

      // Only show scroll button if user has scrolled up and is not near bottom
      setShowScrollButton(userHasScrolled && !isNearBottom);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const newWidth = window.innerWidth - e.clientX;
      const minWidth = 300; // Minimum width
      const maxWidth = 800; // Maximum width

      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setDrawerWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing]);

  // Auto-scroll to bottom when messages change or thread changes
  useEffect(() => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        messagesContainerRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;

      // Always scroll to bottom when switching threads, or when near bottom during message updates
      if (isNearBottom) {
        scrollToBottom();
      }
    }
  }, [messages]);

  // Always scroll to bottom when switching threads
  useEffect(() => {
    scrollToBottom();
  }, [currentThreadId]);

  // Load threads when component mounts
  useEffect(() => {
    if (isOpen) {
      loadThreads();
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="fixed top-4 right-4 z-60 space-y-2">
          {notifications.map((task) => (
            <div
              key={task.task_id}
              className="bg-green-50 border border-green-200 rounded-lg p-4 shadow-lg max-w-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    <h4 className="text-sm font-medium text-green-800">
                      Task Completed
                    </h4>
                  </div>
                  <p className="text-sm text-green-700 mb-3">
                    Your async task has finished processing.
                  </p>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => acceptTaskResult(task)}
                      disabled={acceptingTask === task.task_id}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {acceptingTask === task.task_id
                        ? "Loading..."
                        : "View Result"}
                    </button>
                    <button
                      onClick={() => dismissNotification(task.task_id)}
                      className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 transition-colors"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => dismissNotification(task.task_id)}
                  className="ml-2 text-green-600 hover:text-green-800"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div className="fixed inset-0 bg-transparent z-40" onClick={onClose} />
      )}

      {/* Drawer */}
      <div
        ref={drawerRef}
        className={`fixed top-0 right-0 h-full bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
        style={{ width: `${drawerWidth}px` }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Resize Handle */}
        <div
          className="absolute left-0 top-0 h-full w-1 bg-gray-300 hover:bg-gray-400 cursor-col-resize transition-colors"
          onMouseDown={handleMouseDown}
        />
        {/* Header */}
        <div className="flex-shrink-0 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center space-x-3">
              <h2 className="text-lg font-semibold text-gray-800">
                AI Assistant
              </h2>
              <span className="text-sm text-gray-500 bg-gray-200 px-2 py-1 rounded-full">
                {getShortenedThreadId(currentThreadId)}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              {/* Thread List Toggle Button */}
              {threads.length > 1 && (
                <button
                  onClick={() => setIsThreadSidebarOpen(!isThreadSidebarOpen)}
                  className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                  title="View all conversations"
                >
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M3 12h18M3 6h18M3 18h18" />
                  </svg>
                </button>
              )}
              {/* New Thread Button */}
              <button
                onClick={createNewThread}
                className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                title="New conversation"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </button>
              {/* Close Button */}
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-200 rounded-full transition-colors"
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
          onScroll={handleScroll}
        >
          {/* Loading state */}
          {isLoadingMessages && (
            <div className="flex justify-center items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">Loading messages...</span>
            </div>
          )}

          {/* Error state */}
          {messagesError && (
            <div className="flex justify-center items-center py-8">
              <div className="text-red-600 text-center">
                <p className="font-medium">Failed to load messages</p>
                <p className="text-sm">{messagesError}</p>
                <button
                  onClick={() =>
                    currentThreadId && loadThreadMessages(currentThreadId)
                  }
                  className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {/* Messages */}
          {!isLoadingMessages &&
            !messagesError &&
            (() => {
              const currentMessages = getCurrentThreadMessages();
              const asyncReportPairs = getAsyncReportPairs(currentMessages);
              const processedMessageIds = new Set(
                asyncReportPairs.flatMap((pair) => [
                  pair.userMessage.id,
                  pair.reportMessage.id,
                ])
              );

              // Create a map of async report pairs for quick lookup
              const asyncReportMap = new Map();
              asyncReportPairs.forEach((pair) => {
                asyncReportMap.set(pair.userMessage.id, pair);
              });

              // Create a unified message list that maintains chronological order
              const renderMessages = () => {
                const result: React.ReactElement[] = [];

                currentMessages.forEach((message: Message) => {
                  // Check if this message is part of an async report pair
                  if (asyncReportMap.has(message.id)) {
                    // This is a user message that starts an async report pair
                    const pair = asyncReportMap.get(message.id);
                    result.push(
                      <div key={pair.accordionId} className="mb-4">
                        <AsyncReportAccordion
                          userMessage={pair.userMessage}
                          reportMessage={pair.reportMessage}
                          reportTitle={pair.reportTitle}
                          isExpanded={expandedAccordions.has(pair.accordionId)}
                          onToggle={() => toggleAccordion(pair.accordionId)}
                        />
                      </div>
                    );
                  } else if (!processedMessageIds.has(message.id)) {
                    // This is a regular message (not part of an async report pair)
                    result.push(
                      <div
                        key={message.id}
                        className={`flex ${
                          message.isUser ? "justify-end" : "justify-start"
                        }`}
                      >
                        <div
                          className={`flex items-start space-x-2 ${
                            message.isUser
                              ? "flex-row-reverse space-x-reverse"
                              : ""
                          }`}
                          style={{
                            maxWidth: `${Math.min(drawerWidth * 0.85, 480)}px`,
                          }}
                        >
                          <div
                            className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                              message.isUser
                                ? "bg-blue-600 text-white"
                                : "bg-gray-600 text-white"
                            }`}
                          >
                            {message.isUser ? (
                              <svg
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              >
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                <circle cx="12" cy="7" r="4" />
                              </svg>
                            ) : (
                              <svg
                                width="16"
                                height="16"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              >
                                <rect
                                  x="3"
                                  y="11"
                                  width="18"
                                  height="11"
                                  rx="2"
                                  ry="2"
                                />
                                <circle cx="12" cy="5" r="2" />
                                <path d="M12 7v4" />
                                <line x1="8" y1="16" x2="8" y2="16" />
                                <line x1="16" y1="16" x2="16" y2="16" />
                              </svg>
                            )}
                          </div>
                          <div
                            className={`px-3 py-2 rounded-lg ${
                              message.isUser
                                ? "bg-blue-600 text-white"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {message.payload?.type === "choice" ? (
                              <ChoiceMessage
                                message={message}
                                onChoiceSelect={handleChoiceSelection}
                              />
                            ) : message.payload?.type === "document" ? (
                              <div>
                                <p className="text-xs font-medium mb-1">
                                  {message.text as string}
                                </p>
                                {(message.payload.files ||
                                  message.payload.file) && (
                                  <DocumentPreview
                                    file={message.payload.file}
                                    files={message.payload.files}
                                    docType={
                                      message.payload.docType || "Document"
                                    }
                                  />
                                )}
                              </div>
                            ) : (
                              <div>
                                <p className="text-sm">
                                  {message.text as string}
                                </p>
                                {(message.metadata?.streaming as boolean) && (
                                  <div className="flex items-center mt-1">
                                    <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full mr-1"></div>
                                    <span className="text-xs text-gray-500">
                                      Streaming...
                                    </span>
                                  </div>
                                )}
                              </div>
                            )}
                            <ClientOnlyTimestamp
                              timestamp={message.timestamp}
                              className={
                                message.isUser
                                  ? "text-blue-100"
                                  : "text-gray-500"
                              }
                            />
                          </div>
                        </div>
                      </div>
                    );
                  }
                  // If the message is processed (part of async report pair but not the user message), skip it
                });

                return result;
              };

              return <>{renderMessages()}</>;
            })()}

          {/* Interruption message with choices */}
          {pendingInterruption && (
            <div className="flex justify-start">
              <div className="max-w-md">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800 mb-3">
                    {pendingInterruption.message}
                  </p>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleResponseModeChoice("stream")}
                      disabled={isProcessingAsync}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                      {isProcessingAsync ? "Processing..." : "Streaming"}
                    </button>
                    <button
                      onClick={() => handleResponseModeChoice("async")}
                      disabled={isProcessingAsync}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                    >
                      {isProcessingAsync ? "Processing..." : "Async"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Scroll to Bottom Button */}
        {showScrollButton && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-24 right-4 bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full shadow-lg transition-all duration-200 hover:scale-105 z-10"
            aria-label="Scroll to bottom"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 5v14" />
              <path d="M19 12l-7 7-7-7" />
            </svg>
          </button>
        )}

        {/* File Upload Previews */}
        {uploadedFiles.length > 0 && (
          <div className="flex-shrink-0 p-2 sm:p-4 border-t border-gray-200 max-h-24 sm:max-h-32 overflow-y-auto">
            <div className="space-y-1 sm:space-y-2">
              {uploadedFiles.map((file, index) => (
                <FileUploadPreview
                  key={`${file.id}-${index}-${file.name}-${file.size}`}
                  file={file}
                  onRemove={removeFile}
                />
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="flex-shrink-0 p-2 sm:p-4 border-t border-gray-200">
          <div className="flex space-x-2 min-w-0">
            <div className="flex-shrink-0">
              <FileUploadButton onFilesSelected={handleFiles} />
            </div>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="flex-shrink-0">
              <button
                onClick={handleSendMessage}
                disabled={
                  isUploading ||
                  isSendingMessage ||
                  isStreaming ||
                  !currentThreadId
                }
                className={`px-3 py-2 rounded-lg transition-colors flex items-center space-x-1 text-sm ${
                  isUploading ||
                  isSendingMessage ||
                  isStreaming ||
                  !currentThreadId
                    ? "bg-gray-400 text-gray-200 cursor-not-allowed"
                    : "bg-blue-600 text-white hover:bg-blue-700"
                }`}
              >
                {isUploading ? (
                  <>
                    <svg
                      className="animate-spin h-4 w-4"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    <span className="hidden sm:inline">Uploading...</span>
                    <span className="sm:hidden">...</span>
                  </>
                ) : isSendingMessage || isStreaming ? (
                  <>
                    <svg
                      className="animate-spin h-4 w-4"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    <span className="hidden sm:inline">
                      {isStreaming ? "Streaming..." : "Sending..."}
                    </span>
                    <span className="sm:hidden">...</span>
                  </>
                ) : (
                  <>
                    <span className="hidden sm:inline">Send</span>
                    <svg
                      className="sm:hidden h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

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
              <p className="text-blue-600 font-medium text-lg">
                Drop files here
              </p>
              <p className="text-blue-500 text-sm mt-1">
                Images, PDFs, and Word documents
              </p>
            </div>
          </div>
        )}

        {/* Thread Sidebar */}
        {isThreadSidebarOpen && threads.length > 1 && (
          <div className="absolute left-0 top-0 h-full w-80 bg-white border-r border-gray-200 shadow-lg z-60 flex flex-col">
            <div className="p-4 border-b border-gray-200 flex-shrink-0">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-800">
                  Conversations
                </h3>
                <button
                  onClick={() => setIsThreadSidebarOpen(false)}
                  className="p-1 hover:bg-gray-200 rounded-full transition-colors"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {/* Loading state */}
              {isLoadingThreads && (
                <div className="flex justify-center items-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600 text-sm">
                    Loading conversations...
                  </span>
                </div>
              )}

              {/* Error state */}
              {threadsError && (
                <div className="text-red-600 text-center py-4">
                  <p className="text-sm font-medium">
                    Failed to load conversations
                  </p>
                  <p className="text-xs">{threadsError}</p>
                  <button
                    onClick={loadThreads}
                    className="mt-2 px-2 py-1 bg-red-100 text-red-700 rounded text-xs hover:bg-red-200"
                  >
                    Retry
                  </button>
                </div>
              )}

              {/* Threads list */}
              {!isLoadingThreads && !threadsError && (
                <div className="space-y-2">
                  {threads
                    .sort(
                      (a, b) =>
                        b.lastMessageAt.getTime() - a.lastMessageAt.getTime()
                    )
                    .map((thread) => {
                      return (
                        <button
                          key={thread.id}
                          onClick={() => {
                            switchToThread(thread.id);
                            setIsThreadSidebarOpen(false);
                          }}
                          className={`w-full text-left p-3 rounded-lg transition-colors ${
                            thread.id === currentThreadId
                              ? "bg-blue-100 border border-blue-200"
                              : "bg-gray-50 hover:bg-gray-100 border border-gray-200"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-900">
                              {thread.title}
                            </span>
                            <span className="text-xs text-gray-500">
                              {thread.message_count || 0}{" "}
                              {(thread.message_count || 0) === 1
                                ? "message"
                                : "messages"}
                            </span>
                          </div>
                          {thread.last_message_preview && (
                            <p className="text-xs text-gray-600 truncate">
                              {thread.last_message_preview}
                            </p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {thread.lastMessageAt.toLocaleDateString()} at{" "}
                            {thread.lastMessageAt.toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </p>
                        </button>
                      );
                    })}
                </div>
              )}

              {/* Empty state */}
              {!isLoadingThreads && !threadsError && threads.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500 text-sm">No conversations yet</p>
                  <p className="text-gray-400 text-xs mt-1">
                    Start a new conversation to begin
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
