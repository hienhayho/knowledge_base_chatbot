import React from "react";
import { FileText, MoreVertical } from "lucide-react";

const KnowledgeBaseCard = ({ title, docCount, lastUpdated, onClick }) => {
  return (
    <div
      className="bg-white rounded-lg shadow-md p-4 sm:p-6 hover:shadow-lg transition-shadow duration-300 w-full h-full"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 rounded-full flex items-center justify-center">
          <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500" />
        </div>
        <button className="text-gray-400 hover:text-gray-600">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>
      <h2 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-gray-800">
        {title}
      </h2>
      <div className="flex items-center text-sm text-gray-500 mb-2">
        <FileText className="w-4 h-4 mr-2" />
        {docCount} {docCount === 1 ? "Document" : "Documents"}
      </div>
      <div className="text-sm text-gray-500">Last updated: {lastUpdated}</div>
    </div>
  );
};

export default KnowledgeBaseCard;
