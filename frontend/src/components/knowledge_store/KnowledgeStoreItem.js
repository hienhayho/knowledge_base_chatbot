import React from "react";
import { Book, Plus, Minus } from "lucide-react";

const KnowledgeStoreItem = ({
  id,
  title,
  description,
  price,
  onAddToCart,
  onRemoveFromCart,
  quantity,
}) => (
  <div className="bg-white rounded-lg shadow-md p-6 flex flex-col justify-between">
    <div>
      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
        <Book className="w-6 h-6 text-blue-500" />
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600 mb-4">{description}</p>
      <p className="text-lg font-bold text-blue-600">${price.toFixed(2)}</p>
    </div>
    <div className="flex items-center justify-between mt-4">
      {quantity > 0 ? (
        <div className="flex items-center">
          <button
            onClick={() => onRemoveFromCart(id)}
            className="bg-gray-200 p-2 rounded-l-md"
          >
            <Minus size={16} />
          </button>
          <span className="bg-gray-100 px-4 py-2">{quantity}</span>
          <button
            onClick={() => onAddToCart(id)}
            className="bg-gray-200 p-2 rounded-r-md"
          >
            <Plus size={16} />
          </button>
        </div>
      ) : (
        <button
          onClick={() => onAddToCart(id)}
          className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition-colors"
        >
          Add to Cart
        </button>
      )}
    </div>
  </div>
);

export default KnowledgeStoreItem;
