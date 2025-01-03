export const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

export const authEndpoints = {
    login: `${BASE_API_URL}/api/users/login`,
    register: `${BASE_API_URL}/api/users/create`,
    me: `${BASE_API_URL}/api/users/me`,
};

export const knowledgeBaseEndpoints = {
    fetchKnowledgeBases: `${BASE_API_URL}/api/kb/get_all`,
    createKnowledgeBase: `${BASE_API_URL}/api/kb/create`,
    deleteKnowledgeBase: (kbId: string) =>
        `${BASE_API_URL}/api/kb/delete_kb/${kbId}`,
    fetchKnowledgeBase: (kbId?: string) =>
        `${BASE_API_URL}/api/kb/get_kb/${kbId}`,
    getDocumentStatus: (documentId: string) =>
        `${BASE_API_URL}/api/kb/document_status/${documentId}`,
    uploadToKnowledgeBase: (kbId: string) =>
        `${BASE_API_URL}/api/kb/upload?knowledge_base_id=${kbId}`,
    inheritKNowledgeBase: `${BASE_API_URL}/api/kb/inherit_kb`,

    processDocument: (documentId: string) =>
        `${BASE_API_URL}/api/kb/process/${documentId}`,
    stopProcessingDocument: (documentId: string) =>
        `${BASE_API_URL}/api/kb/stop_processing/${documentId}`,
    downloadDocument: (documentId: string) =>
        `${BASE_API_URL}/api/kb/download/${documentId}`,
    deleteDocument: (documentId: string) =>
        `${BASE_API_URL}/api/kb/delete_document/${documentId}`,
};

export const assistantEndpoints = {
    fetchAssistants: `${BASE_API_URL}/api/assistant`,
    fetchAssistant: (assistantId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}`,
    fetchAssistantConversations: (assistantId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/conversations`,
    createAssistant: `${BASE_API_URL}/api/assistant`,
    updateAssistant: (assistantId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/update`,
    deleteAssistant: (assistantId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}`,

    updateTools: (assistantId?: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/tools`,

    createConversation: (assistantId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/conversations`,
    fetchConversationHistory: (assistantId: string, conversationId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/conversations/${conversationId}/history`,
    exportConversation: (assistantId: string, conversationId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/export/${conversationId}`,
    exportConversations: (assistantId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/export_conversations`,
    renameConversation: (assistantId?: string, conversationId?: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/conversations/${conversationId}/rename`,
    deleteConversation: (assistantId?: string, conversationId?: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/conversations/${conversationId}`,

    sendMessage: (assistantId: string, conversationId: string) =>
        `${BASE_API_URL}/api/assistant/${assistantId}/conversations/${conversationId}/messages`,
    productionMessage: (conversationId: string) =>
        `${BASE_API_URL}/api/assistant_v2/conversations/${conversationId}/production_messages`,
};

export const adminEndpoints = {
    fetchUsers: `${BASE_API_URL}/api/admin/users`,
    switchUser: `${BASE_API_URL}/api/admin/switch-user`,
    editUser: (userId: string) => `${BASE_API_URL}/api/admin/users/${userId}`,
    deleteUser: (userId: string) => `${BASE_API_URL}/api/admin/users/${userId}`,
    fetchTokens: `${BASE_API_URL}/api/admin/tokens`,
    createToken: `${BASE_API_URL}/api/admin/create-token`,
    deleteToken: (tokenId: string) =>
        `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/admin/delete-token/${tokenId}`,
};

export const toolsEndpoints = {
    fetchTools: `${BASE_API_URL}/api/tools`,
};

export const agentEndpoints = {
    fetchAllExistAgent: `${BASE_API_URL}/api/agent`,
};

export const dashboardEndpoints = {
    fetchOptions: (source: string) => `${BASE_API_URL}/api/dashboard/${source}`,
    fetchDashboardData: `${BASE_API_URL}/api/dashboard`,
    exportFile: (fileName: string) =>
        `${BASE_API_URL}/api/dashboard/export/${fileName}`,
    userWordCloudUrl: (type: string, source: string) =>
        `${BASE_API_URL}/api/dashboard/wordcloud/${type}/${source}?is_user=true`,
    assistantWordCloudUrl: (type: string, source: string) =>
        `${BASE_API_URL}/api/dashboard/wordcloud/${type}/${source}?is_user=false`,
};
