import { login, me, register } from "./auth";
import { createKnowledgeBase, fetchKnowledgeBases } from "./knowledgeBase";

export const authApi = { login, me, register };
export const knowledgeBaseApi = { fetchKnowledgeBases, createKnowledgeBase };
