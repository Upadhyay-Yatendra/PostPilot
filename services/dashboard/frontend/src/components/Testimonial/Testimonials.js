"use client";
import Image from "next/image";
import { testimonials } from "./data";

export default function Testimonials() {
  return (
    <section className="w-full bg-[#1e56a0] py-20 px-10 sm:py-16 sm:px-6 lg:py-20 lg:px-12 xl:px-40">
      <div className="max-w-7xl mx-auto">
        {/* Section Title */}
        <div className="text-center mb-8 sm:mb-12">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white break-words">
            How they are growing their audience with{" "}
            <span className="bg-white text-[#1e56a0] px-2 py-1 rounded-lg font-semibold">
              Taplio
            </span>
          </h2>
          <p className="text-gray-200 mt-2 sm:mt-3 text-sm sm:text-base">
            Real feedback from our amazing users
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {testimonials.map((item, index) => (
            <div
              key={index}
              className="bg-white text-black rounded-2xl shadow-lg p-4 sm:p-6 flex flex-col"
            >
              {/* User Info */}
              <div className="flex items-center space-x-3 mb-3 sm:mb-4">
                <Image
                  src={item.image}
                  alt={item.name}
                  width={48}
                  height={48}
                  className="rounded-full object-cover"
                />
                <div>
                  <h3 className="font-semibold text-sm sm:text-base">
                    {item.name}
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-500">
                    {item.role}
                  </p>
                </div>
              </div>

              {/* Feedback */}
              <p className="text-gray-700 text-sm sm:text-base leading-relaxed">
                {item.feedback}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
