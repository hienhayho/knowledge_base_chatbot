import React from "react";
import { AlertTriangle } from "lucide-react";

const ErrorComponent = ({ message }) => {
  return (
    <div className="flex items-center justify-center h-screen bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-4">
          Oops! Something went wrong
        </h2>
        <p className="text-center text-gray-600 mb-6">
          {message ||
            "We're having trouble loading this page. Please try again later."}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="w-full bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded transition duration-300"
        >
          Retry
        </button>
      </div>
    </div>
  );
};

export default ErrorComponent;
