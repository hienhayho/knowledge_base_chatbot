// app/knowledge/[name]/page.js
"use client";

import React from "react";
import { useParams } from "next/navigation";
import DatasetView from "@/components/knowledge_base/KBDatasetView";

export default function KnowledgeBasePage() {
    const params = useParams();
    const knowledgeBaseID = Array.isArray(params.name)
        ? params.name[0]
        : params.name;

    return <DatasetView knowledgeBaseID={knowledgeBaseID} />;
}
