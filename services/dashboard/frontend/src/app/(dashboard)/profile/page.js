"use client";
import { useSidebar } from "@/context/SidebarContext";
import { useEffect, useState } from "react";
import axios from "axios";

export default function ProfileWidget() {
  const { isOpen } = useSidebar();
    const [user, setUser] = useState({})
    const [loading,setLoading]=useState(false)


     const fetchData = async () => {
         const token = sessionStorage.getItem("access_token");
         console.log("token",token)
       setLoading(true);
       try {
           const response = await axios.get(
             "http://localhost:8000/api/v1/auth/me",
             {
               headers: {
                 Authorization: `Bearer ${token}`, // ✅ Add token here
               },
             }
           );

           // Update user state with response data
           setUser(response.data);
         console.log("Signup successful:", response.data);
       } catch (err) {
         console.log(err);
         alert("Login failed:", err);
       } finally {
         setLoading(false);
       }
     };

    useEffect(() => {
        fetchData()
    },[])
  return (
    <div className="p-4 bg-gray-100 rounded-lg shadow">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        Hi! Sreejita Sen. Welcome back.
      </h1>
      
      
    </div>
  );
}
