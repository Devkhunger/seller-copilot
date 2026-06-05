
import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Inventory from "./pages/Inventory.jsx";
import ListingDoctor from "./pages/ListingDoctor.jsx";
import Login from "./pages/Login.jsx";
import MlInsights from "./pages/MlInsights.jsx";
import RtoRisk from "./pages/RtoRisk.jsx";
import SkuScore from "./pages/SkuScore.jsx";
import Upload from "./pages/Upload.jsx";
import Usage from "./pages/Usage.jsx";
import WeeklyProfit from "./pages/WeeklyProfit.jsx";
import AskCopilot from "./pages/AskCopilot.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}> 
        <Route path="/upload" element={<Upload />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/sku-score" element={<SkuScore />} />
        <Route path="/rto-risk" element={<RtoRisk />} />
        <Route path="/ask" element={<AskCopilot />} />
        <Route path="/listing-doctor" element={<ListingDoctor />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/weekly-profit" element={<WeeklyProfit />} />
        <Route path="/ml-insights" element={<MlInsights />} />
        <Route path="/usage" element={<Usage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
