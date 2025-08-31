
import FAQSection from "@/components/Faq/FAQSection";
import Testimonials from "@/components/Testimonial/Testimonials";
import FeaturesSection from "@/components/FeatureSection";
export default function Home() {
  return (
    <div className="">
      <section className="w-full flex flex-col items-center text-center px-4 sm:px-6 py-12 sm:py-16 md:py-24">
        {/* Main Heading */}
        <h1 className="text-2xl sm:text-3xl md:text-5xl font-extrabold leading-snug sm:leading-tight text-gray-900 max-w-3xl break-words whitespace-normal">
          The all-in-one LinkedIn <br className="hidden md:block" />
          platform to turn content <br className="hidden md:block" />
          into{" "}
          <span className="bg-blue-100 text-[#227cb0] px-2 py-1 rounded-md">
            pipeline
          </span>
        </h1>

        {/* Features */}
        <div className="flex flex-col sm:flex-row sm:flex-wrap items-center justify-center gap-3 sm:gap-4 md:gap-6 mt-6 sm:mt-8 w-full">
          <span className="flex items-center gap-2 bg-blue-100 text-[#227cb0] px-3 py-2 rounded-full text-xs sm:text-sm md:text-base font-medium whitespace-normal break-words text-center">
            <span className="flex items-center justify-center w-4 h-4 rounded-full bg-[#227cb0] flex-shrink-0">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="white"
                className="w-3 h-3"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
            FIND CLIENTS FASTER
          </span>

          <span className="flex items-center gap-2 bg-blue-100 text-[#227cb0] px-3 py-2 rounded-full text-xs sm:text-sm md:text-base font-medium whitespace-normal break-words text-center">
            <span className="flex items-center justify-center w-4 h-4 rounded-full bg-[#227cb0] flex-shrink-0">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="white"
                className="w-3 h-3"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
            CREATE CONTENT THAT CONVERTS
          </span>

          <span className="flex items-center gap-2 bg-blue-100 text-[#227cb0] px-3 py-2 rounded-full text-xs sm:text-sm md:text-base font-medium whitespace-normal break-words text-center">
            <span className="flex items-center justify-center w-4 h-4 rounded-full bg-[#227cb0] flex-shrink-0">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="white"
                className="w-3 h-3"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
            TRACK GROWTH THAT MATTERS
          </span>
        </div>

        {/* CTA Button */}
        <button className="mt-6 sm:mt-8 px-5 sm:px-6 py-3 bg-[#227cb0] text-white text-base sm:text-lg font-medium rounded-lg shadow-md hover:bg-[#053a64] transition">
          Start For Free
        </button>
      </section>

      <Testimonials />
      <FeaturesSection/>
      <FAQSection />
    </div>
  );
}
