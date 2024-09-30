import React from "react";
import { Loader2 } from "lucide-react";

const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center h-screen">
      <Loader2 className="w-12 h-12 animate-spin text-blue-500" />
      <span className="ml-2 text-xl font-semibold text-gray-700">
        Loading...
      </span>
    </div>
  );
};

export default LoadingSpinner;
