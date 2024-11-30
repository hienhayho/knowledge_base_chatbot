export const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

export const authEndpoints = {
    login: `${BASE_API_URL}/api/users/login`,
    register: `${BASE_API_URL}/api/users/create`,
    me: `${BASE_API_URL}/api/users/me`,
};

export const knowledgeBaseEndpoints = {
    fetchKnowledgeBases: `${BASE_API_URL}/api/kb/get_all`,
    createKnowledgeBase: `${BASE_API_URL}/api/kb/create`,
};
