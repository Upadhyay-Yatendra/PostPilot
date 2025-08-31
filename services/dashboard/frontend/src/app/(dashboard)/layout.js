import Sidebar from "@/components/Sidebar";
import { SidebarProvider } from "@/context/SidebarContext";

export default function DashboardLayout({ children }) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 p-6 overflow-y-auto h-screen">{children}</main>
      </div>
    </SidebarProvider>
  );
}
