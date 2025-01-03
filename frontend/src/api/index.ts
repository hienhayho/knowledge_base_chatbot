import {
    createToken,
    deleteToken,
    deleteUser,
    fetchTokens,
    getUsers,
    switchUser,
    updateUser,
} from "./admin";
import { fetchAllAgentChoices } from "./agents";
import {
    createAssistant,
    createConversation,
    deleteAssistant,
    deleteConversation,
    exportConversation,
    exportFileConversations,
    fetchAssistant,
    fetchAssistantConversations,
    fetchAssistants,
    fetchConversationHistory,
    renameConversation,
    sendMessage,
    updateAssistant,
    updateTools,
} from "./assistant";
import { login, me, register } from "./auth";
import { exportFile, fetchDashboardData, fetchOptions } from "./dashboard";
import {
    createKnowledgeBase,
    deleteDocument,
    deleteKnowledgeBase,
    downloadDocument,
    fetchKnowledgeBase,
    fetchKnowledgeBases,
    getDocumentStatus,
    inheritKnowledgeBase,
    processDocument,
    stopProcessingDocument,
    uploadToKnowledgeBase,
} from "./knowledgeBase";
import { fetchTools } from "./tools";

// Auth API
export const authApi = { login, me, register };

// Knowledge Base API
export const knowledgeBaseApi = {
    fetchKnowledgeBases,
    fetchKnowledgeBase,
    createKnowledgeBase,
    inheritKnowledgeBase,
    deleteKnowledgeBase,
    getDocumentStatus,
    uploadToKnowledgeBase,
    downloadDocument,
    deleteDocument,
    processDocument,
    stopProcessingDocument,
};

// Admin API
export const adminApi = {
    getUsers,
    updateUser,
    switchUser,
    deleteUser,
    fetchTokens,
    deleteToken,
    createToken,
};

// Assistant API
export const assistantApi = {
    fetchAssistants,
    fetchAssistant,
    createAssistant,
    updateAssistant,
    deleteAssistant,

    updateTools,

    fetchAssistantConversations,
    createConversation,
    renameConversation,
    deleteConversation,
    exportConversation,
    fetchConversationHistory,
    exportFileConversations,

    sendMessage,
};

// Agent API
export const agentApi = {
    fetchAllAgentChoices,
};

// Dashboard API
export const dashboardApi = {
    fetchDashboardData,
    exportFile,
    fetchOptions,
};

// Tools API
export const toolsApi = {
    fetchTools,
};
