"use client";
import { useSidebar } from "@/context/SidebarContext";
import {
  Calendar,
  MessageSquare,
  Cpu,
  Lightbulb,
  BarChart2,
} from "lucide-react";

const cards = [
  {
    icon: Calendar,
    title: "Consistency is key!",
    description: "Write and schedule your next post now",
    button: "Start composing",
  },
  {
    icon: MessageSquare,
    title: "Your comments grow your reach:",
    description: "reply to stay visible",
    button: "Engage now",
  },
  {
    icon: Cpu,
    title: "Need help writing?",
    description: "Let AI do the heavy lifting",
    button: "Try AI chat assist",
  },
  {
    icon: Lightbulb,
    title: "Find inspiration",
    description: "Get fresh content ideas instantly",
    button: "Explore ideas",
  },
  {
    icon: BarChart2,
    title: "Track performance",
    description: "See how your posts are doing",
    button: "View analytics",
  },
];
export default function DashboardWidget() {
  const { isOpen } = useSidebar();

  return (
    <div className="p-4 bg-gray-100 rounded-lg shadow">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        Hi! Sreejita Sen. Welcome back.
      </h1>

      {/* Cards Grid */}
      <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div
              key={index}
              className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow duration-200 flex flex-col items-center"
            >
              {/* Icon */}
              <div className="p-3 bg-blue-50 rounded-lg mb-4">
                <Icon className="text-blue-500" size={24} />
              </div>

              {/* Title & Description */}
              <h2 className="font-semibold text-gray-800 mb-1">{card.title}</h2>
              <p className="text-gray-500 text-sm mb-4">{card.description}</p>

              {/* Button */}
              <button className="mt-auto text-blue-600 font-medium border border-blue-200 px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors">
                {card.button}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
