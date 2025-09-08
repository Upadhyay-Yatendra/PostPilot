"use client";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function NavBar() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Fixed Navbar */}
      <nav className="fixed top-0 left-0 right-0 w-full flex items-center justify-between px-6 py-3 shadow-sm bg-white z-50">
        {/* Logo */}
        <div className="flex items-center space-x-2">
          <Image
            src="/images/logo.png"
            alt="PostPilot Logo"
            width={60}
            height={60}
          />
          <span className="text-xl font-semibold text-gray-800">Postpilot</span>
        </div>


        {/* Desktop Buttons */}
        <div className="hidden md:flex space-x-3">
          <button
            className="rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
            onClick={() => router.push("/login")}
          >
            Log In
          </button>
          <button
            className="rounded-lg px-4 py-2 text-sm bg-[#227cb0] text-white hover:bg-[#053a64] cursor-pointer"
            onClick={() => router.push("/signup")}
          >
            Sign-Up For Free
          </button>
        </div>

        {/* Mobile Hamburger */}
        <button
          className="md:hidden text-gray-700 text-2xl"
          onClick={() => setIsOpen(true)}
        >
          ☰
        </button>

        {/* Sidebar for Mobile */}
        <div
          className={`fixed top-0 right-0 h-full w-64 bg-white shadow-lg transform ${
            isOpen ? "translate-x-0" : "translate-x-full"
          } transition-transform duration-300 ease-in-out z-50`}
        >
          {/* Sidebar Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <span className="text-lg font-semibold">Menu</span>
            <button
              className="text-gray-600 text-2xl"
              onClick={() => setIsOpen(false)}
            >
              ✕
            </button>
          </div>

          {/* Sidebar Links */}
          <div className="flex flex-col space-y-4 p-4 text-gray-700 font-medium">
            <Link
              href="/dashboard"
              className="hover:text-blue-600"
              onClick={() => setIsOpen(false)}
            >
              Dashboard
            </Link>
            <Link
              href="/about"
              className="hover:text-blue-600"
              onClick={() => setIsOpen(false)}
            >
              About Us
            </Link>
            <Link
              href="/profile"
              className="hover:text-blue-600"
              onClick={() => setIsOpen(false)}
            >
              My Profile
            </Link>
          </div>

          {/* Sidebar Buttons */}
          <div className="flex flex-col space-y-3 p-4 border-t">
            <button className="rounded-lg border px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
              Log In
            </button>
            <button className="rounded-lg px-4 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700">
              Sign-Up For Free
            </button>
          </div>
        </div>

        {/* Background Overlay */}
        {isOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-40 z-40"
            onClick={() => setIsOpen(false)}
          />
        )}
      </nav>

      {/* Spacer for fixed navbar height */}
      <div className="pt-20" />
    </>
  );
}
