import {
    createToken,
    deleteToken,
    deleteUser,
    fetchTokens,
    getUsers,
    switchUser,
} from "./admin";
import { fetchAllAgentChoices } from "./agents";
import {
    createConversation,
    deleteAssistant,
    exportFileConversations,
    fetchAssistant,
    fetchAssistantConversations,
    fetchAssistants,
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
    processDocument,
    stopProcessingDocument,
    uploadToKnowledgeBase,
} from "./knowledgeBase";

// Auth API
export const authApi = { login, me, register };

// Knowledge Base API
export const knowledgeBaseApi = {
    fetchKnowledgeBases,
    fetchKnowledgeBase,
    createKnowledgeBase,
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
    deleteAssistant,

    fetchAssistantConversations,
    createConversation,
    exportFileConversations,
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
