"use client";
import Image from "next/image";
import { FaLinkedin, FaYoutube, FaEnvelope, FaXTwitter } from "react-icons/fa6";

export default function Footer() {
  return (
    <footer className="bg-white border-t">
      <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Left Section */}
        <div className="space-y-4">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <Image
              src="/images/logo.png" // place logo in /public/images/logo.png
              alt="Supergrow Logo"
              width={32}
              height={32}
            />
            <span className="text-xl font-bold text-gray-900">Supergrow</span>
          </div>
          <p className="text-gray-600 text-sm">
            Build Your Personal Brand on LinkedIn with Supergrow.
          </p>

          {/* Social Icons */}
          <div className="flex space-x-4 text-gray-500 text-xl">
            <FaLinkedin className="hover:text-gray-800 cursor-pointer" />
            <FaYoutube className="hover:text-gray-800 cursor-pointer" />
            <FaEnvelope className="hover:text-gray-800 cursor-pointer" />
            <FaXTwitter className="hover:text-gray-800 cursor-pointer" />
          </div>
        </div>

        {/* Products */}
        <div>
          <h3 className="text-gray-900 font-semibold mb-3">Products</h3>
          <ul className="space-y-2 text-gray-600 text-sm">
            <li>For Agency</li>
            <li>Voice notes</li>
            <li>Swipe files (save ideas)</li>
            <li>LinkedIn Post Ideas</li>
            <li>LinkedIn Post Generator</li>
            <li>LinkedIn Carousel Maker</li>
            <li>LinkedIn Post Scheduling</li>
            <li>LinkedIn Engagement</li>
          </ul>
        </div>

        {/* Company */}
        <div>
          <h3 className="text-gray-900 font-semibold mb-3">Company</h3>
          <ul className="space-y-2 text-gray-600 text-sm">
            <li>Team</li>
            <li>Affiliate Program</li>
            <li>Roadmap</li>
            <li>Privacy Policy</li>
            <li>Terms of Service</li>
          </ul>
        </div>

        {/* Resources */}
        <div>
          <h3 className="text-gray-900 font-semibold mb-3">Resources</h3>
          <ul className="space-y-2 text-gray-600 text-sm">
            <li>Blog</li>
            <li>Customer Stories</li>
            <li>Our Wall Of Love 💙</li>
            <li>ChatGPT vs Supergrow</li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
