"use client";

import { useSidebar } from "@/context/SidebarContext";
import { useState } from "react";
import {
  LayoutDashboard,
  ChevronLeft,
  ChevronRight,
  ChartLine,
  PencilLine,
  UserRound,
  LogOut,
} from "lucide-react";
import { useRouter } from "next/navigation";
import Image from "next/image";

const menuItems = [
  { name: "Dashboard", icon: LayoutDashboard, link: "/dashboard" },
  { name: "Write a Post", icon: PencilLine, link: "/post" },
  { name: "Analytics", icon: ChartLine, link: "/analytics" },
  { name: "My Profile", icon: UserRound, link: "/profile" },
  { name: "Logout", icon: LogOut, link: "/" },
];

export default function Sidebar() {
  const { isOpen, setIsOpen } = useSidebar();
    const [currIndex, setIndex] = useState(0)
    const router = useRouter();
  return (
    <div
      className={`h-screen bg-white border-r border-gray-200 transition-all duration-300 flex flex-col
        ${isOpen ? "w-64" : "w-16"}`}
    >
      {/* Logo + Toggle */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2 overflow-hidden">
          <Image src="/images/logo.png" alt="logo" width={40} height={40} />
          {isOpen && (
            <span className="font-semibold text-lg truncate">PostPilot</span>
          )}
        </div>
        <div className="flex flex-col items-center">
          {!isOpen && (
            <Image src="/images/logo.png" alt="logo" width={40} height={40} className="mb-4" />
          )}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 bg-gray-100 rounded-md cursor-pointer"
          >
            {isOpen ? <ChevronLeft /> : <ChevronRight />}
          </button>
        </div>
      </div>

      {/* Menu Items */}
      <ul className="mt-4 flex-1">

        {menuItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <li key={index}>
              <button
                className={`flex items-center w-full gap-3 px-4 py-3 text-gray-600 cursor-pointer ${
                  !isOpen ? "justify-center" : ""
                } ${
                  index == currIndex
                    ? "text-white bg-[#227cb0]"
                    : "text-gray-600"
                } `}
                onClick={() => {
                  router.push(item.link);
                  setIndex(index);
                }}
              >
                <Icon size={20} />
                {isOpen && <span>{item.name}</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
