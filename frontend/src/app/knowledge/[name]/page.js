// app/knowledge/[name]/page.js
"use client";

import React from "react";
import { useParams } from "next/navigation";
import DatasetView from "@/components/knowledge_base/KBDatasetView";

export default function KnowledgeBasePage() {
  const params = useParams();
  const knowledgeBaseID = decodeURIComponent(params.name);

  return <DatasetView knowledgeBaseID={knowledgeBaseID} />;
}
