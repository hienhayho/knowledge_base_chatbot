export type IApiResponse<T> = T | { detail: string };
export interface INavItem {
    name: string;
    path: string;
    description: string;
    feature?: string;
}

export interface SelectOption {
    value: string;
    label: string;
}

export type WordCloudSource =
    | "Knowledge Base"
    | "Assistant"
    | "Conversation"
    | "";

export interface IUploadFile {
    doc_id: string;
    file_name: string;
    file_type: string;
    file_size_in_mb: number;
    created_at: string;
    status: string;
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

export interface IDashBoardResponse {
    file_name: string;
    file_conversation_name: string;
    total_conversations: number;
    average_assistant_response_time: number;

    assistant_statistics: {
        id: string;
        name: string;
        number_of_conversations: number;
    }[];
    conversations_statistics: {
        id: string;
        average_session_chat_time: number;
        average_user_messages: number;
    }[];
    knowledge_base_statistics: {
        id: string;
        name: string;
        total_user_messages: number;
    }[];

    detail?: string;
}

export interface IKnowledgeBase {
    id: string;
    name: string;
    description: string;
    document_count: number;
    last_updated: string;
    updated_at: string;
}

export interface IMergeableKnowledgeBase {
    id: string;
    name: string;
}

export interface IMergeableKnowledgeBaseResponse {
    inheritable_knowledge_bases: IMergeableKnowledgeBase[];
    parents: string[];
    children: string[];
    detail?: string;
}

export interface IKnowledgeBaseResponse extends IKnowledgeBase {
    detail?: string;
}

export interface IUser {
    id: string;
    username: string;
    role: string;
    organization: string;
    createdAt: string;
    updatedAt: string;
}

export interface IUserUpdateFormValues {
    organization: string;
}

export interface IUserResponse {
    id: string;
    username: string;
    role: string;
    organization: string;
    created_at: string;
    updated_at: string;
}

export interface IToken {
    id: string;
    user_id: string;
    token: string;
    createdAt: string;
    updatedAt: string;
    username: string;
    role: string;
}

export interface ITokenResponse {
    id: string;
    user_id: string;
    username: string;
    role: string;
    token: string;
    created_at: string;
    updated_at: string;
    detail?: string;
}

export interface ITokenFormValues {
    username: string;
}

export interface SignUpFormValues {
    username: string;
    email: string;
    password: string;
    retypePassword: string;
    admin_access_token?: string;
    organization?: string;
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
    agent_type: string;
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
    expires: string;
}
