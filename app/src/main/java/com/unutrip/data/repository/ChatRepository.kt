package com.unutrip.data.repository

import com.unutrip.data.model.ChatMessage
import com.unutrip.data.model.ChatbotResult
import com.unutrip.utils.AiChatService
import com.unutrip.utils.RagService

class ChatRepository(
    private val ragService: RagService = RagService(),
    private val aiChatService: AiChatService = AiChatService()
) {

    suspend fun sendRagChat(
        token: String,
        message: String,
        history: List<ChatMessage> = emptyList(),
        targetProvince: String? = null,
        targetCity: String? = null
    ): ChatbotResult {
        return ragService.chat(token, history, message, targetProvince, targetCity)
    }

    suspend fun sendChatFallback(token: String, message: String): ChatbotResult {
        return aiChatService.fallbackChat(token, message)
    }
}
