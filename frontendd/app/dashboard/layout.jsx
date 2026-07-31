import Sidebar from "@/components/Sidebar";

export default function DashboardLayout({ children }) {
  return (
    <div className="alias-dashboard">
      <Sidebar />

      <main className="alias-main">
        <div className="alias-main-inner">
          {children}
        </div>
      </main>
    </div>
  );
}
