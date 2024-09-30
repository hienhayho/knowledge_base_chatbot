"use client";

import React, { useState } from "react";
import { Search, ShoppingCart } from "lucide-react";
import KnowledgeStoreItem from "@/components/knowledge_store/KnowledgeStoreItem";

const KnowledgeStorePage = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [cart, setCart] = useState({});

  // Sample knowledge items data
  const knowledgeItems = [
    {
      id: 1,
      title: "Machine Learning Basics",
      description: "Comprehensive guide to ML fundamentals",
      price: 29.99,
    },
    {
      id: 2,
      title: "Advanced Python Programming",
      description: "Master Python with advanced concepts",
      price: 39.99,
    },
    {
      id: 3,
      title: "Data Visualization Techniques",
      description: "Learn to create impactful data visuals",
      price: 24.99,
    },
    {
      id: 4,
      title: "Blockchain Technology",
      description: "Understand the core of blockchain",
      price: 34.99,
    },
    {
      id: 5,
      title: "Artificial Intelligence Ethics",
      description: "Explore ethical considerations in AI",
      price: 19.99,
    },
    {
      id: 6,
      title: "Cloud Computing Essentials",
      description: "Get started with cloud technologies",
      price: 27.99,
    },
  ];

  const filteredItems = knowledgeItems.filter(
    (item) =>
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const addToCart = (itemId) => {
    setCart((prevCart) => ({
      ...prevCart,
      [itemId]: (prevCart[itemId] || 0) + 1,
    }));
  };

  const removeFromCart = (itemId) => {
    setCart((prevCart) => {
      const newCart = { ...prevCart };
      if (newCart[itemId] > 1) {
        newCart[itemId]--;
      } else {
        delete newCart[itemId];
      }
      return newCart;
    });
  };

  const cartTotal = Object.entries(cart).reduce((total, [itemId, quantity]) => {
    const item = knowledgeItems.find((item) => item.id === parseInt(itemId));
    return total + item.price * quantity;
  }, 0);

  const cartItemCount = Object.values(cart).reduce(
    (sum, quantity) => sum + quantity,
    0
  );

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Knowledge Store</h1>
          <div className="relative">
            <input
              type="text"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border rounded-md w-64"
            />
            <Search
              className="absolute left-3 top-2.5 text-gray-400"
              size={20}
            />
          </div>
          <div className="relative">
            <ShoppingCart className="w-8 h-8 text-blue-500" />
            {cartItemCount > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
                {cartItemCount}
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredItems.map((item) => (
            <KnowledgeStoreItem
              key={item.id}
              {...item}
              onAddToCart={addToCart}
              onRemoveFromCart={removeFromCart}
              quantity={cart[item.id] || 0}
            />
          ))}
        </div>

        {cartItemCount > 0 && (
          <div className="mt-8 bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-4">Your Cart</h2>
            {Object.entries(cart).map(([itemId, quantity]) => {
              const item = knowledgeItems.find(
                (item) => item.id === parseInt(itemId)
              );
              return (
                <div
                  key={itemId}
                  className="flex justify-between items-center mb-2"
                >
                  <span>
                    {item.title} (x{quantity})
                  </span>
                  <span>${(item.price * quantity).toFixed(2)}</span>
                </div>
              );
            })}
            <div className="mt-4 pt-4 border-t flex justify-between items-center">
              <span className="text-xl font-bold">Total:</span>
              <span className="text-xl font-bold">${cartTotal.toFixed(2)}</span>
            </div>
            <button className="mt-4 w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 transition-colors">
              Proceed to Checkout
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeStorePage;
