"use client";
import { useState } from "react";
import { faqs } from "./data";

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState(null);

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="w-full bg-[#0f0f12] text-white py-12 px-4 sm:py-16 sm:px-6">
      <div className="max-w-3xl mx-auto">
        {/* Heading */}
        <h2 className="text-xl sm:text-3xl md:text-4xl font-bold text-center mb-8 sm:mb-10">
          Frequently Asked Questions
        </h2>

        {/* FAQ List */}
        <div className="space-y-3 sm:space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-[#1c1c21] rounded-lg sm:rounded-xl overflow-hidden"
            >
              {/* Question */}
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full flex justify-between items-center px-3 py-3 sm:px-4 sm:py-4 text-left font-medium text-base sm:text-lg hover:bg-[#25252b] transition"
              >
                <span className="pr-2 flex-1 whitespace-normal break-words">
                  {faq.question}
                </span>
                <span className="text-lg sm:text-xl flex-shrink-0 ml-2">
                  {openIndex === index ? "−" : "+"}
                </span>
              </button>

              {/* Answer */}
              {openIndex === index && (
                <div className="px-3 sm:px-4 pb-3 sm:pb-4 text-gray-300 text-sm sm:text-base leading-relaxed whitespace-normal break-words">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
