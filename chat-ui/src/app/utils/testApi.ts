/**
 * Test utilities for API integration
 */

import { chatApi } from "../services/chatApi";

export const testApiConnection = async () => {
  try {
    console.log("Testing API connection...");

    // Test creating a thread
    const thread = await chatApi.createThread({
      title: "Test Thread",
      metadata: { test: true },
    });

    console.log("✅ Thread created:", thread);

    // Test sending a message
    const message = await chatApi.sendChatMessage({
      thread_id: thread.thread_id,
      content: "Hello, this is a test message!",
      message_type: "text",
      metadata: { test: true },
    });

    console.log("✅ Message sent:", message);

    // Test getting thread messages
    const messages = await chatApi.getThreadMessages(thread.thread_id);
    console.log("✅ Messages retrieved:", messages);

    return { success: true, thread, message, messages };
  } catch (error) {
    console.error("❌ API test failed:", error);
    return { success: false, error };
  }
};

export const testStreamingChat = async (threadId: string) => {
  try {
    console.log("Testing streaming chat...");

    const receivedChunks: unknown[] = [];

    await chatApi.streamChatMessage(
      {
        thread_id: threadId,
        content: "Test streaming message",
        message_type: "text",
        metadata: { test: true },
      },
      (chunk) => {
        console.log("📦 Received chunk:", chunk);
        receivedChunks.push(chunk);
      },
      (error) => {
        console.error("❌ Stream error:", error);
      },
      () => {
        console.log("✅ Stream completed");
      }
    );

    return { success: true, chunks: receivedChunks };
  } catch (error) {
    console.error("❌ Streaming test failed:", error);
    return { success: false, error };
  }
};

export const testAsyncReport = async (threadId: string) => {
  try {
    console.log("Testing async report...");

    const interruption = await chatApi.createAsyncReport({
      thread_id: threadId,
      content: "Generate a test report about AI trends",
      message_type: "text",
      metadata: { test: true },
    });

    console.log("✅ Async report created:", interruption);

    // Test choosing response mode
    const choice = await chatApi.handleResponseModeChoice({
      task_id: interruption.task_id,
      response_mode: "async",
      user_id: "test-user",
    });

    console.log("✅ Response mode chosen:", choice);

    return { success: true, interruption, choice };
  } catch (error) {
    console.error("❌ Async report test failed:", error);
    return { success: false, error };
  }
};
