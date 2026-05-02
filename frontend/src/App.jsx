import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import ProductPage from "./pages/ProductPage";
import ComparePage from "./pages/ComparePage";
import ScannerPage from "./pages/ScannerPage";
import AccountPage from "./pages/AccountPage";
import WebsitePage from "./pages/WebsitePage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<WebsitePage page="about" />} />
        <Route path="/contact" element={<WebsitePage page="contact" />} />
        <Route path="/support" element={<WebsitePage page="support" />} />
        <Route path="/privacy" element={<WebsitePage page="privacy" />} />
        <Route path="/terms" element={<WebsitePage page="terms" />} />
        <Route path="/terms-of-use" element={<WebsitePage page="terms" />} />
        <Route path="/subscription-terms" element={<WebsitePage page="subscriptionTerms" />} />
        <Route path="/delete-account" element={<WebsitePage page="deleteAccount" />} />
        <Route path="/pricing" element={<WebsitePage page="pricing" />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/scanner" element={<ScannerPage />} />
        <Route path="/account" element={<AccountPage />} />
        <Route path="/product/:barcode" element={<ProductPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
