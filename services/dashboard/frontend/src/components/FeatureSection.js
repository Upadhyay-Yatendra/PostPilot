"use client";
import { FaPenNib } from "react-icons/fa";
import { FaLightbulb } from "react-icons/fa";
import { FaBullseye } from "react-icons/fa";

const features = [
  {
    icon: <FaPenNib className="text-3xl text-[#1e56a0]" />,
    title: "Smart Writing",
    description:
      "Generate stunning, personalized social media content, powered by AI trained on top creators' content.",
  },
  {
    icon: <FaLightbulb className="text-3xl text-[#1e56a0]" />,
    title: "Posts ideas",
    description:
      "Never run out of ideas—ask our AI to provide fresh post topics inspired by the latest trends and what creators are publishing.",
  },
  {
    icon: <FaBullseye className="text-3xl text-[#1e56a0]" />,
    title: "Targeted Reach",
    description:
      "Publish, schedule posts, engage, and answer with AI directly from the editor, ensuring maximum impact on social media.",
  },
];

export default function FeaturesSection() {
  return (
    <section className="w-full py-20 px-6 md:px-12 lg:px-24 bg-white">
      {/* Title */}
      <div className="text-center mb-20">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-[#0f0f12] leading-snug">
          <span className="bg-[#227cb0] text-white px-2 py-1 rounded-md mr-2">
            Features that
          </span>
          Help You Go <br className="sm:hidden" /> Viral On Social Media
        </h2>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {features.map((feature, index) => (
          <div
            key={index}
            className="relative bg-white border rounded-xl p-6 flex flex-col items-start shadow-sm 
                       transition-all duration-300 ease-out 
                       hover:-translate-y-2 hover:-translate-x-2
                       hover:shadow-[8px_8px_0px_0px_rgba(30,86,160,0.5)]"
          >
            {/* Icon */}
            <div className="mb-4">{feature.icon}</div>

            {/* Title */}
            <h3 className="text-lg font-bold text-[#0f0f12] mb-2">
              {feature.title}
            </h3>

            {/* Description */}
            <p className="text-gray-600 text-sm leading-relaxed">
              {feature.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
