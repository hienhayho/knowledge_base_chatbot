export type IApiResponse<T> = T | { detail: string };
export interface INavItem {
    name: string;
    path: string;
}

export interface ILoginFormValues {
    username: string;
    password: string;
}

export interface ILoginResponse {
    access_token: string;
}

export interface ICreateKnowledgeBase {
    name: string;
    description: string;
    is_contextual_rag: boolean;
}

export interface IKnowledgeBase {
    id: string;
    name: string;
    description: string;
    document_count: number;
    last_updated: string;
    updated_at: string;
}

export interface IKnowledgeBaseResponse extends IKnowledgeBase {
    detail?: string;
}

export interface IUser {
    id: string;
    username: string;
    role: string;
    createdAt: string;
    updatedAt: string;
}

export interface SignUpFormValues {
    username: string;
    email: string;
    password: string;
    retypePassword: string;
    admin_access_token?: string;
}

export interface SignUpResponse {
    username: string;
    detail?: string;
}

export interface IAssistant {
    id: string;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
    instruct_prompt: string;
    agent_backstory?: string;
    knowledge_base_id?: string;
    tools: string[];
    exist_tools?: string[];
    configuration?: Record<string, string | number>;
}

export interface IConversation {
    id: string;
    name: string;
    assistant_id: string;
    created_at: string;
    updated_at: string;
}

export interface IAdminUserSelect {
    value: string;
    label: string;
}

export interface IAdminSwitchUserResponse {
    user: IUser;
    access_token: string;
    type: string;
}
