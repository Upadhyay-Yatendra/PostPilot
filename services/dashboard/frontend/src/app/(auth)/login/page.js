"use client";

import { useState } from "react";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import Image from "next/image";
import { useRouter } from "next/navigation";
import axios from "axios";
export default function SignupPage() {
  const router = useRouter();

   const initialFormData = {
     email: "",
     password: "",
   };
  const [formData, setFormData] = useState(initialFormData);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async(e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/api/v1/auth/login", {
        email: formData.email,
        password: formData.password,
      });

      // store token in sessionStorage
      sessionStorage.setItem("access_token", response.data.access_token);

      console.log("Signup successful:", response.data);
      router.push("/dashboard");
    } catch (err) {
      console.log(err)
      alert("Login failed:", err);
    } finally {
      setLoading(false);
      setFormData(initialFormData);
    }
  };


  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-white">
      <div className="w-full max-w-md p-8 bg-white">
        <div className="flex items-center justify-center space-x-2">
          <Image
            src="/images/logo.png"
            alt="PostPilot Logo"
            width={60}
            height={60}
          />
          <span className="text-xl font-semibold text-gray-800">Postpilot</span>
        </div>
        <h1 className="text-2xl font-bold text-center text-gray-900">
          Hey there ,welcome back
        </h1>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              className="mt-1 block w-full rounded-lg border border-gray-300 p-3 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              required
            />
          </div>

          {/* Password with Toggle */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                placeholder="Enter a strong password"
                minLength={6}
                value={formData.password}
                name="password"
                onChange={handleChange}
                className="mt-1 block w-full rounded-lg border border-gray-300 p-3 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-3 flex items-center text-gray-500"
              >
                {showPassword ? <FaEyeSlash size={20} /> : <FaEye size={20} />}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="w-full rounded-full bg-blue-500 py-3 text-white font-medium hover:bg-blue-600 transition cursor-pointer"
          >
            {loading ? <span>Loading...</span> : <div>Login with Email</div>}
          </button>
        </form>

        <div className="py-10 flex items-center justify-center">
          Don&#39;t have an account?
          <span
            className="text-[#227cb0] ml-2 cursor-pointer"
            onClick={() => router.push("/signup")}
          >
            Sign up
          </span>
        </div>
      </div>
    </div>
  );
}
