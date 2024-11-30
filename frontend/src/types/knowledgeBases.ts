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
